import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q

from esg.models import (
    EmissionFactor,
    NormalizedEmissionRecord,
    RawIngestRow,
    RecordChangeLog,
    SourceSystem,
    UploadBatch,
)

User = get_user_model()


UNIT_CONVERSIONS = {
    "l": ("liters", Decimal("1")),
    "liter": ("liters", Decimal("1")),
    "liters": ("liters", Decimal("1")),
    "gallon": ("liters", Decimal("3.78541")),
    "gallons": ("liters", Decimal("3.78541")),
    "kwh": ("kwh", Decimal("1")),
    "mwh": ("kwh", Decimal("1000")),
    "km": ("km", Decimal("1")),
    "mi": ("km", Decimal("1.60934")),
    "nights": ("nights", Decimal("1")),
}

SUSPICION_WEIGHTS = {
    "missing_factor": Decimal("40"),
    "high_usage": Decimal("25"),
    "unknown_unit": Decimal("25"),
    "missing_distance": Decimal("20"),
    "negative_or_zero": Decimal("50"),
    "date_parse_issue": Decimal("20"),
}


@dataclass
class NormalizedRow:
    activity_date: date
    activity_type: str
    scope: str
    quantity: Decimal
    quantity_unit: str
    normalized_quantity: Decimal
    normalized_unit: str
    validation_flags: list[str]


def _clean_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_")


def _normalize_header_row(row: dict[str, Any]) -> dict[str, Any]:
    return {_clean_key(k): v for k, v in row.items()}


def _to_decimal(value: Any) -> Decimal:
    text = str(value).strip().replace(",", "")
    if text == "":
        return Decimal("0")
    return Decimal(text)


def _parse_date(value: str) -> date:
    value = value.strip()
    patterns = ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d")
    for pattern in patterns:
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")


def _to_normalized_unit(quantity: Decimal, unit_raw: str) -> tuple[Decimal, str, list[str]]:
    flags: list[str] = []
    unit_key = unit_raw.strip().lower()
    if unit_key not in UNIT_CONVERSIONS:
        flags.append("unknown_unit")
        return quantity, unit_key, flags
    target_unit, multiplier = UNIT_CONVERSIONS[unit_key]
    return quantity * multiplier, target_unit, flags


def _resolve_factor(org_id: int, scope: str, activity_type: str, unit: str, activity_date: date):
    return (
        EmissionFactor.objects.filter(
            Q(organization_id=org_id) | Q(organization__isnull=True),
            scope=scope,
            activity_type=activity_type,
            unit=unit,
            is_active=True,
            valid_from__lte=activity_date,
        )
        .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=activity_date))
        .order_by("-organization_id", "-valid_from")
        .first()
    )


def _normalize_sap(row: dict[str, Any]) -> NormalizedRow:
    fuel_type = str(row.get("fuel_type") or row.get("material_description") or "unknown").strip().lower()
    quantity = _to_decimal(row.get("quantity", "0"))
    unit_raw = str(row.get("unit", "")).strip()
    activity_date = _parse_date(str(row.get("posting_date", "")))
    normalized_quantity, normalized_unit, flags = _to_normalized_unit(quantity, unit_raw)
    if quantity <= 0:
        flags.append("negative_or_zero")
    if normalized_quantity > Decimal("100000"):
        flags.append("high_usage")
    return NormalizedRow(
        activity_date=activity_date,
        activity_type=f"fuel_{fuel_type}",
        scope=NormalizedEmissionRecord.SCOPE_1,
        quantity=quantity,
        quantity_unit=unit_raw,
        normalized_quantity=normalized_quantity,
        normalized_unit=normalized_unit,
        validation_flags=flags,
    )


def _normalize_utility(row: dict[str, Any]) -> NormalizedRow:
    usage = _to_decimal(row.get("usage", "0"))
    unit_raw = str(row.get("unit", "")).strip()
    billing_end = _parse_date(str(row.get("billing_end", "")))
    normalized_quantity, normalized_unit, flags = _to_normalized_unit(usage, unit_raw)
    if usage <= 0:
        flags.append("negative_or_zero")
    if normalized_quantity > Decimal("1000000"):
        flags.append("high_usage")
    return NormalizedRow(
        activity_date=billing_end,
        activity_type="purchased_electricity",
        scope=NormalizedEmissionRecord.SCOPE_2,
        quantity=usage,
        quantity_unit=unit_raw,
        normalized_quantity=normalized_quantity,
        normalized_unit=normalized_unit,
        validation_flags=flags,
    )


def _normalize_travel(row: dict[str, Any]) -> NormalizedRow:
    travel_type = str(row.get("travel_type", "")).strip().lower()
    flags: list[str] = []
    activity_date = _parse_date(str(row.get("travel_date", row.get("booking_date", "2024-01-01"))))

    if travel_type == "flight":
        distance = _to_decimal(row.get("distance_km", "0"))
        if distance <= 0:
            flags.append("missing_distance")
        quantity = distance
        quantity_unit = "km"
        activity_type = "business_flight"
    elif travel_type == "hotel":
        quantity = _to_decimal(row.get("hotel_nights", "0"))
        quantity_unit = "nights"
        activity_type = "business_hotel"
    else:
        quantity = _to_decimal(row.get("taxi_distance", "0"))
        quantity_unit = str(row.get("taxi_unit", "km"))
        activity_type = "ground_transport"
        if quantity <= 0:
            flags.append("missing_distance")

    normalized_quantity, normalized_unit, unit_flags = _to_normalized_unit(quantity, quantity_unit)
    flags.extend(unit_flags)
    if quantity <= 0:
        flags.append("negative_or_zero")
    return NormalizedRow(
        activity_date=activity_date,
        activity_type=activity_type,
        scope=NormalizedEmissionRecord.SCOPE_3,
        quantity=quantity,
        quantity_unit=quantity_unit,
        normalized_quantity=normalized_quantity,
        normalized_unit=normalized_unit,
        validation_flags=flags,
    )


def _normalize_for_source(source_type: str, row: dict[str, Any]) -> NormalizedRow:
    if source_type == SourceSystem.TYPE_SAP:
        return _normalize_sap(row)
    if source_type == SourceSystem.TYPE_UTILITY:
        return _normalize_utility(row)
    if source_type == SourceSystem.TYPE_TRAVEL:
        return _normalize_travel(row)
    raise ValueError(f"Unsupported source type: {source_type}")


def _suspicion_score(flags: list[str]) -> Decimal:
    score = Decimal("0")
    for flag in set(flags):
        score += SUSPICION_WEIGHTS.get(flag, Decimal("10"))
    return min(score, Decimal("100"))


def _create_record_log(record: NormalizedEmissionRecord, actor: User, reason: str = "") -> None:
    RecordChangeLog.objects.create(
        organization=record.organization,
        record=record,
        event_type=RecordChangeLog.EVENT_CREATED,
        actor=actor,
        changed_fields=["status", "emissions_tco2e", "validation_flags"],
        after_state={
            "status": record.status,
            "emissions_tco2e": str(record.emissions_tco2e),
            "validation_flags": record.validation_flags,
        },
        reason=reason,
    )


@transaction.atomic
def ingest_csv_batch(*, batch: UploadBatch, actor: User) -> dict[str, int]:
    batch.file.open("rb")
    raw_bytes = batch.file.read()
    batch.file.close()

    checksum = hashlib.sha256(raw_bytes).hexdigest()
    batch.file_checksum_sha256 = checksum

    decoded = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    total_rows = 0
    parsed_rows = 0
    error_rows = 0

    for row_num, raw_row in enumerate(reader, start=2):
        total_rows += 1
        normalized_row = _normalize_header_row(raw_row)
        raw_model = RawIngestRow.objects.create(
            organization=batch.organization,
            upload_batch=batch,
            source_row_number=row_num,
            raw_payload=normalized_row,
            parse_status=RawIngestRow.PARSE_OK,
        )
        try:
            transformed = _normalize_for_source(batch.source_system.source_type, normalized_row)
            factor = _resolve_factor(
                org_id=batch.organization_id,
                scope=transformed.scope,
                activity_type=transformed.activity_type,
                unit=transformed.normalized_unit,
                activity_date=transformed.activity_date,
            )
            flags = list(transformed.validation_flags)
            if not factor:
                flags.append("missing_factor")
                emissions = Decimal("0")
            else:
                emissions = transformed.normalized_quantity * factor.factor_value

            score = _suspicion_score(flags)
            status = (
                NormalizedEmissionRecord.STATUS_SUSPICIOUS
                if score >= Decimal("30")
                else NormalizedEmissionRecord.STATUS_PENDING
            )

            record = NormalizedEmissionRecord.objects.create(
                organization=batch.organization,
                source_system=batch.source_system,
                upload_batch=batch,
                source_row=raw_model,
                activity_date=transformed.activity_date,
                activity_type=transformed.activity_type,
                scope=transformed.scope,
                quantity=transformed.quantity,
                quantity_unit=transformed.quantity_unit,
                normalized_quantity=transformed.normalized_quantity,
                normalized_unit=transformed.normalized_unit,
                emissions_tco2e=emissions,
                factor=factor,
                status=status,
                suspicion_score=score,
                validation_flags=flags,
            )
            _create_record_log(record, actor, reason="Created via CSV ingestion pipeline.")
            parsed_rows += 1
        except Exception as exc:
            raw_model.parse_status = RawIngestRow.PARSE_ERROR
            raw_model.parse_error = str(exc)
            raw_model.save(update_fields=["parse_status", "parse_error", "updated_at"])
            error_rows += 1

    batch.total_rows = total_rows
    batch.parsed_rows = parsed_rows
    batch.error_rows = error_rows
    batch.status = UploadBatch.STATUS_PROCESSED if error_rows == 0 else UploadBatch.STATUS_FAILED
    batch.processing_notes = f"Parsed={parsed_rows}, Errors={error_rows}"
    batch.save(
        update_fields=[
            "file_checksum_sha256",
            "total_rows",
            "parsed_rows",
            "error_rows",
            "status",
            "processing_notes",
            "updated_at",
        ]
    )
    return {"total_rows": total_rows, "parsed_rows": parsed_rows, "error_rows": error_rows}
