from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class AppUser(TimeStampedModel):
    ROLE_UPLOADER = "uploader"
    ROLE_ANALYST = "analyst"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = (
        (ROLE_UPLOADER, "Uploader"),
        (ROLE_ANALYST, "Analyst"),
        (ROLE_ADMIN, "Admin"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="app_profile",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="members",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_UPLOADER)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="uniq_user_in_org",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.organization.slug}:{self.role}"


class SourceSystem(TimeStampedModel):
    TYPE_SAP = "sap_fuel"
    TYPE_UTILITY = "utility_electricity"
    TYPE_TRAVEL = "corp_travel"
    TYPE_CHOICES = (
        (TYPE_SAP, "SAP Fuel & Procurement"),
        (TYPE_UTILITY, "Utility Electricity"),
        (TYPE_TRAVEL, "Corporate Travel"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="source_systems",
    )
    source_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    display_name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "source_type", "display_name"],
                name="uniq_source_name_per_org",
            )
        ]

    def __str__(self) -> str:
        return f"{self.organization.slug}:{self.display_name}"


class UploadBatch(TimeStampedModel):
    STATUS_RECEIVED = "received"
    STATUS_PROCESSED = "processed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_RECEIVED, "Received"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_FAILED, "Failed"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="upload_batches",
    )
    source_system = models.ForeignKey(
        SourceSystem,
        on_delete=models.PROTECT,
        related_name="upload_batches",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_batches",
    )
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/esg/%Y/%m/%d/")
    file_checksum_sha256 = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RECEIVED)
    total_rows = models.PositiveIntegerField(default=0)
    parsed_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processing_notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "uploaded_at"]),
            models.Index(fields=["source_system", "uploaded_at"]),
        ]

    def __str__(self) -> str:
        return f"batch:{self.id}:{self.organization.slug}:{self.source_system.source_type}"


class RawIngestRow(TimeStampedModel):
    PARSE_OK = "ok"
    PARSE_ERROR = "error"
    PARSE_CHOICES = ((PARSE_OK, "OK"), (PARSE_ERROR, "Error"))

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="raw_rows",
    )
    upload_batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.CASCADE,
        related_name="raw_rows",
    )
    source_row_number = models.PositiveIntegerField()
    raw_payload = models.JSONField()
    parse_status = models.CharField(max_length=10, choices=PARSE_CHOICES, default=PARSE_OK)
    parse_error = models.TextField(blank=True)
    external_record_id = models.CharField(max_length=120, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["upload_batch", "source_row_number"],
                name="uniq_row_number_per_batch",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "upload_batch"]),
        ]

    def __str__(self) -> str:
        return f"raw:{self.upload_batch_id}:{self.source_row_number}"


class EmissionFactor(TimeStampedModel):
    SCOPE_1 = "scope1"
    SCOPE_2 = "scope2"
    SCOPE_3 = "scope3"
    SCOPE_CHOICES = (
        (SCOPE_1, "Scope 1"),
        (SCOPE_2, "Scope 2"),
        (SCOPE_3, "Scope 3"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="emission_factors",
        null=True,
        blank=True,
        help_text="Null means global/default factor usable by all orgs.",
    )
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    activity_type = models.CharField(max_length=100)
    unit = models.CharField(max_length=30)
    factor_value = models.DecimalField(max_digits=16, decimal_places=8)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    source_reference = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "activity_type", "unit"]),
            models.Index(fields=["scope", "valid_from"]),
        ]

    def clean(self) -> None:
        if self.valid_to and self.valid_to < self.valid_from:
            raise ValidationError("valid_to cannot be earlier than valid_from.")

    def __str__(self) -> str:
        owner = self.organization.slug if self.organization else "global"
        return f"{owner}:{self.scope}:{self.activity_type}:{self.unit}"


class NormalizedEmissionRecord(TimeStampedModel):
    STATUS_PENDING = "pending"
    STATUS_SUSPICIOUS = "suspicious"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_SUSPICIOUS, "Suspicious"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    SCOPE_1 = "scope1"
    SCOPE_2 = "scope2"
    SCOPE_3 = "scope3"
    SCOPE_CHOICES = (
        (SCOPE_1, "Scope 1"),
        (SCOPE_2, "Scope 2"),
        (SCOPE_3, "Scope 3"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="normalized_records",
    )
    source_system = models.ForeignKey(
        SourceSystem,
        on_delete=models.PROTECT,
        related_name="normalized_records",
    )
    upload_batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.PROTECT,
        related_name="normalized_records",
    )
    source_row = models.OneToOneField(
        RawIngestRow,
        on_delete=models.PROTECT,
        related_name="normalized_record",
    )

    activity_date = models.DateField()
    activity_type = models.CharField(max_length=100)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)

    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    quantity_unit = models.CharField(max_length=30)
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=6)
    normalized_unit = models.CharField(max_length=30)

    emissions_tco2e = models.DecimalField(max_digits=18, decimal_places=8)
    factor = models.ForeignKey(
        EmissionFactor,
        on_delete=models.PROTECT,
        related_name="records",
        null=True,
        blank=True,
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    suspicion_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    validation_flags = models.JSONField(default=list, blank=True)
    rejection_reason = models.TextField(blank=True)

    is_locked = models.BooleanField(default=False)
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="edited_records",
        null=True,
        blank=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_records",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "status", "scope"]),
            models.Index(fields=["upload_batch", "status"]),
            models.Index(fields=["activity_date"]),
        ]

    def clean(self) -> None:
        if self.is_locked and self.status != self.STATUS_APPROVED:
            raise ValidationError("Only approved records can be locked.")
        if self.status == self.STATUS_APPROVED and not self.approved_by:
            raise ValidationError("approved_by is required when status is approved.")
        if self.status == self.STATUS_REJECTED and not self.rejection_reason:
            raise ValidationError("rejection_reason is required when status is rejected.")

    def __str__(self) -> str:
        return f"rec:{self.id}:{self.organization.slug}:{self.scope}:{self.status}"


class RecordChangeLog(models.Model):
    EVENT_CREATED = "created"
    EVENT_EDITED = "edited"
    EVENT_STATUS_CHANGED = "status_changed"
    EVENT_APPROVED = "approved"
    EVENT_REJECTED = "rejected"
    EVENT_LOCKED = "locked"
    EVENT_UNLOCKED = "unlocked"
    EVENT_CHOICES = (
        (EVENT_CREATED, "Created"),
        (EVENT_EDITED, "Edited"),
        (EVENT_STATUS_CHANGED, "Status Changed"),
        (EVENT_APPROVED, "Approved"),
        (EVENT_REJECTED, "Rejected"),
        (EVENT_LOCKED, "Locked"),
        (EVENT_UNLOCKED, "Unlocked"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="record_change_logs",
    )
    record = models.ForeignKey(
        NormalizedEmissionRecord,
        on_delete=models.CASCADE,
        related_name="change_logs",
    )
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="record_change_events",
        null=True,
        blank=True,
    )
    changed_fields = models.JSONField(default=list, blank=True)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["record", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"log:{self.record_id}:{self.event_type}:{self.created_at.isoformat()}"
