from django.contrib import admin

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

admin.site.register(Organization)
admin.site.register(AppUser)
admin.site.register(SourceSystem)
admin.site.register(UploadBatch)
admin.site.register(RawIngestRow)
admin.site.register(EmissionFactor)
admin.site.register(NormalizedEmissionRecord)
admin.site.register(RecordChangeLog)
