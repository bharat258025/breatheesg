from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    AppUser,
    EmissionFactor,
    NormalizedEmissionRecord,
    Organization,
    RawIngestRow,
    RecordChangeLog,
    SourceSystem,
    UploadBatch,
)

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SourceSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceSystem
        fields = [
            "id",
            "organization",
            "source_type",
            "display_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UploadBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadBatch
        fields = [
            "id",
            "organization",
            "source_system",
            "uploaded_by",
            "original_filename",
            "file",
            "file_checksum_sha256",
            "status",
            "total_rows",
            "parsed_rows",
            "error_rows",
            "uploaded_at",
            "processing_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "uploaded_at",
            "created_at",
            "updated_at",
            "uploaded_by",
            "status",
            "total_rows",
            "parsed_rows",
            "error_rows",
        ]


class UploadBatchIngestSerializer(serializers.Serializer):
    source_system_id = serializers.IntegerField()
    file = serializers.FileField()

    def validate(self, attrs):
        request = self.context["request"]
        app_profile = getattr(request.user, "app_profile", None)
        if app_profile:
            try:
                source_system = SourceSystem.objects.get(
                    id=attrs["source_system_id"],
                    organization=app_profile.organization,
                    is_active=True,
                )
            except SourceSystem.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {"source_system_id": "Invalid source for this organization."}
                ) from exc
        elif settings.DEBUG:
            try:
                source_system = SourceSystem.objects.get(id=attrs["source_system_id"], is_active=True)
            except SourceSystem.DoesNotExist as exc:
                raise serializers.ValidationError({"source_system_id": "Invalid source_system_id."}) from exc
        else:
            raise serializers.ValidationError("User is not mapped to an organization.")
        attrs["source_system"] = source_system
        return attrs


class RawIngestRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawIngestRow
        fields = [
            "id",
            "organization",
            "upload_batch",
            "source_row_number",
            "raw_payload",
            "parse_status",
            "parse_error",
            "external_record_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EmissionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactor
        fields = [
            "id",
            "organization",
            "scope",
            "activity_type",
            "unit",
            "factor_value",
            "valid_from",
            "valid_to",
            "source_reference",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class NormalizedEmissionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            "id",
            "organization",
            "source_system",
            "upload_batch",
            "source_row",
            "activity_date",
            "activity_type",
            "scope",
            "quantity",
            "quantity_unit",
            "normalized_quantity",
            "normalized_unit",
            "emissions_tco2e",
            "factor",
            "status",
            "suspicion_score",
            "validation_flags",
            "rejection_reason",
            "is_locked",
            "edited_by",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "emissions_tco2e",
            "edited_by",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if instance and instance.is_locked:
            raise serializers.ValidationError("Locked records cannot be edited.")

        new_status = attrs.get("status", instance.status if instance else None)
        rejection_reason = attrs.get(
            "rejection_reason", instance.rejection_reason if instance else ""
        )
        if new_status == NormalizedEmissionRecord.STATUS_REJECTED and not rejection_reason:
            raise serializers.ValidationError(
                {"rejection_reason": "Required when status is rejected."}
            )
        return attrs


class RecordChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordChangeLog
        fields = [
            "id",
            "organization",
            "record",
            "event_type",
            "actor",
            "changed_fields",
            "before_state",
            "after_state",
            "reason",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AppUserSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = AppUser
        fields = [
            "id",
            "user",
            "user_email",
            "organization",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "user_email"]
