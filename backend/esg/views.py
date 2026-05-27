from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

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
from .serializers import (
    AppUserSerializer,
    EmissionFactorSerializer,
    NormalizedEmissionRecordSerializer,
    OrganizationSerializer,
    RawIngestRowSerializer,
    RecordChangeLogSerializer,
    SourceSystemSerializer,
    UploadBatchSerializer,
    UploadBatchIngestSerializer,
)
from .services.ingestion import ingest_csv_batch


class TenantFilteredModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    tenant_field = "organization"

    def get_queryset(self):
        queryset = super().get_queryset()
        app_profile = getattr(self.request.user, "app_profile", None)
        if app_profile:
            return queryset.filter(**{self.tenant_field: app_profile.organization})
        if settings.DEBUG:
            return queryset
        if not self.request.user.is_authenticated:
            return queryset.none()
        return queryset.none()


class OrganizationViewSet(TenantFilteredModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class SourceSystemViewSet(TenantFilteredModelViewSet):
    queryset = SourceSystem.objects.select_related("organization")
    serializer_class = SourceSystemSerializer


class UploadBatchViewSet(TenantFilteredModelViewSet):
    queryset = UploadBatch.objects.select_related("organization", "source_system", "uploaded_by")
    serializer_class = UploadBatchSerializer

    def perform_create(self, serializer):
        app_profile = self.request.user.app_profile
        serializer.save(organization=app_profile.organization, uploaded_by=self.request.user)


class RawIngestRowViewSet(TenantFilteredModelViewSet):
    queryset = RawIngestRow.objects.select_related("organization", "upload_batch")
    serializer_class = RawIngestRowSerializer


class EmissionFactorViewSet(TenantFilteredModelViewSet):
    queryset = EmissionFactor.objects.select_related("organization")
    serializer_class = EmissionFactorSerializer


class NormalizedEmissionRecordViewSet(TenantFilteredModelViewSet):
    queryset = NormalizedEmissionRecord.objects.select_related(
        "organization",
        "source_system",
        "upload_batch",
        "source_row",
        "factor",
        "edited_by",
        "approved_by",
    )
    serializer_class = NormalizedEmissionRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset

    def _resolve_actor(self):
        if self.request.user and self.request.user.is_authenticated:
            return self.request.user
        if settings.DEBUG:
            profile = AppUser.objects.select_related("user").first()
            if profile:
                return profile.user
        return None

    def perform_update(self, serializer):
        actor = self._resolve_actor()
        if not actor:
            raise permissions.PermissionDenied("Authentication required.")

        record_before = self.get_object()
        old_status = record_before.status
        new_status = serializer.validated_data.get("status", old_status)

        extra_fields = {"edited_by": actor}
        if new_status == NormalizedEmissionRecord.STATUS_APPROVED:
            extra_fields["approved_by"] = actor
            extra_fields["approved_at"] = timezone.now()
            extra_fields["is_locked"] = True
        elif new_status != NormalizedEmissionRecord.STATUS_APPROVED:
            extra_fields["approved_by"] = None
            extra_fields["approved_at"] = None
            if new_status == NormalizedEmissionRecord.STATUS_REJECTED:
                extra_fields["is_locked"] = False

        updated_record = serializer.save(**extra_fields)

        event_type = RecordChangeLog.EVENT_EDITED
        reason = "Record edited."
        if old_status != new_status:
            if new_status == NormalizedEmissionRecord.STATUS_APPROVED:
                event_type = RecordChangeLog.EVENT_APPROVED
                reason = "Record approved by analyst."
            elif new_status == NormalizedEmissionRecord.STATUS_REJECTED:
                event_type = RecordChangeLog.EVENT_REJECTED
                reason = serializer.validated_data.get("rejection_reason", "Record rejected.")
            else:
                event_type = RecordChangeLog.EVENT_STATUS_CHANGED
                reason = f"Status changed to {new_status}."

        RecordChangeLog.objects.create(
            organization=updated_record.organization,
            record=updated_record,
            event_type=event_type,
            actor=actor,
            changed_fields=list(serializer.validated_data.keys()),
            before_state={"status": old_status},
            after_state={"status": updated_record.status, "is_locked": updated_record.is_locked},
            reason=reason,
        )


class RecordChangeLogViewSet(TenantFilteredModelViewSet):
    queryset = RecordChangeLog.objects.select_related("organization", "record", "actor")
    serializer_class = RecordChangeLogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        record_id = self.request.query_params.get("record")
        if record_id:
            queryset = queryset.filter(record_id=record_id)
        return queryset


class AppUserViewSet(TenantFilteredModelViewSet):
    queryset = AppUser.objects.select_related("organization", "user")
    serializer_class = AppUserSerializer


class IngestionUploadView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UploadBatchIngestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        app_profile = getattr(request.user, "app_profile", None)
        upload = serializer.validated_data["file"]
        source_system = serializer.validated_data["source_system"]
        if app_profile:
            organization = app_profile.organization
            actor = request.user
        elif settings.DEBUG:
            seed_profile = AppUser.objects.select_related("user", "organization").first()
            if not seed_profile:
                return Response(
                    {"detail": "Create at least one AppUser in admin for DEBUG mode."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            organization = seed_profile.organization
            actor = seed_profile.user
        else:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        batch = UploadBatch.objects.create(
            organization=organization,
            source_system=source_system,
            uploaded_by=actor,
            original_filename=upload.name,
            file=upload,
            file_checksum_sha256="",
            status=UploadBatch.STATUS_RECEIVED,
        )
        summary = ingest_csv_batch(batch=batch, actor=actor)
        return Response(
            {"batch_id": batch.id, "status": batch.status, "summary": summary},
            status=status.HTTP_201_CREATED,
        )
