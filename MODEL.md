# MODEL.md

## Purpose

This document explains the backend domain model for the ESG emissions ingestion and analyst review prototype.  
The goal is to provide a defendable, production-minded model that is realistic for a 4-day implementation window.

## Modeling Principles

1. Preserve source truth before transformation.
2. Make every reviewed emission row traceable to its source row and upload event.
3. Enforce tenant isolation at the application-query layer.
4. Keep workflow explicit (`pending`, `suspicious`, `approved`, `rejected`).
5. Prefer simple deterministic normalization over opaque rule engines.

## Domain Boundaries

### 1) Tenant and Access

- `Organization`: tenant boundary.
- `AppUser`: maps Django user to organization and lightweight role (`uploader`, `analyst`, `admin`).

Why: enough control for assignment scope without building a full IAM system.

### 2) Source and Ingestion

- `SourceSystem`: source metadata per organization (`sap_fuel`, `utility_electricity`, `corp_travel`).
- `UploadBatch`: one file ingestion event with uploader, checksum, row counters, and status.
- `RawIngestRow`: immutable raw row storage with parse status/errors.

Why: this preserves forensic lineage and allows debugging normalization defects without losing original evidence.

### 3) Emissions Normalization

- `EmissionFactor`: factor table with scope, activity type, unit, and validity windows. Supports org-specific and global factors.
- `NormalizedEmissionRecord`: canonical ESG row used for review/reporting:
  - activity metadata (`activity_date`, `activity_type`, `scope`)
  - source quantity and normalized quantity/unit
  - computed emissions (`emissions_tco2e`)
  - workflow fields (`status`, `suspicion_score`, `validation_flags`)
  - approval/edit metadata (`edited_by`, `approved_by`, `approved_at`, `is_locked`)

Why: normalized records are clean and query-friendly while still linked to source rows.

### 4) Audit Trail

- `RecordChangeLog`: append-only event log for record lifecycle changes.
  - captures actor, event type, changed fields, before/after snapshot, reason.

Why: gives an explainable audit narrative for compliance and analyst accountability.

## Relationship Graph (Conceptual)

- `Organization` 1->N `SourceSystem`
- `Organization` 1->N `UploadBatch`
- `UploadBatch` 1->N `RawIngestRow`
- `RawIngestRow` 1->1 `NormalizedEmissionRecord`
- `NormalizedEmissionRecord` N->1 `EmissionFactor` (nullable when unresolved)
- `NormalizedEmissionRecord` 1->N `RecordChangeLog`

## Workflow State Model

1. `pending`: parsed and normalized, awaiting analyst action.
2. `suspicious`: auto-flagged by validation/suspicion logic.
3. `approved`: accepted; may be locked for audit integrity.
4. `rejected`: rejected with required reason.

Guardrails:

- Locked rows are not editable.
- Rejected rows require rejection reason.
- Approved rows require approver metadata.

## Normalization Strategy (Implemented)

1. Ingest CSV into `UploadBatch`.
2. Store every row in `RawIngestRow`.
3. Normalize by source-specific mapper:
   - SAP fuel -> scope 1
   - Utility electricity -> scope 2
   - Corporate travel -> scope 3
4. Canonicalize units (e.g., gallons -> liters, MWh -> kWh, miles -> km).
5. Resolve emission factor by organization/global fallback + validity date.
6. Compute `emissions_tco2e`.
7. Persist validation flags and suspicion score.

## Multi-Tenancy Approach

Chosen approach: organization-scoped rows + tenant-filtered querysets in DRF.

Why this approach:

- Fast to deliver.
- Easy to review.
- Works well for a small internal enterprise tool.

Tradeoff:

- Relies on disciplined query filtering in all data access paths.
- Stronger isolation methods (e.g., PostgreSQL RLS) are possible but out of scope for 4-day delivery.

## Realistic Assumptions

- All ingestion occurs through CSV uploads.
- Ingestion is synchronous (no background queue initially).
- Emission factors are preloaded and versioned by validity period.
- Suspicion scoring is deterministic and rules-based.

## Out of Scope (Intentionally Not Built)

- Event-driven ingestion architecture.
- Microservices or distributed ETL platform.
- Dynamic workflow/rules DSL.
- Complex role-permission matrix UI.
- Hard multi-tenant isolation at infrastructure level.

## Why This Model Is Strong for Interview Evaluation

1. Clear separation of raw data, normalized data, and audit history.
2. Directly maps to assignment requirements (ingestion, review, scope, audit, tenancy).
3. Demonstrates practical engineering judgment and tradeoff clarity.
4. Production-shaped while remaining implementable quickly and cleanly.
