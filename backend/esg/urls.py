from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AppUserViewSet,
    EmissionFactorViewSet,
    IngestionUploadView,
    NormalizedEmissionRecordViewSet,
    OrganizationViewSet,
    RawIngestRowViewSet,
    RecordChangeLogViewSet,
    SourceSystemViewSet,
    UploadBatchViewSet,
)

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("users", AppUserViewSet, basename="app-user")
router.register("sources", SourceSystemViewSet, basename="source-system")
router.register("batches", UploadBatchViewSet, basename="upload-batch")
router.register("raw-rows", RawIngestRowViewSet, basename="raw-ingest-row")
router.register("factors", EmissionFactorViewSet, basename="emission-factor")
router.register("records", NormalizedEmissionRecordViewSet, basename="normalized-record")
router.register("record-logs", RecordChangeLogViewSet, basename="record-change-log")

urlpatterns = router.urls + [
    path("ingestion/upload-csv/", IngestionUploadView.as_view(), name="ingestion-upload-csv"),
]
