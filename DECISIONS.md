# DECISIONS.md

## Context

This project is a 4-day prototype for ESG data ingestion and analyst review using Django REST, PostgreSQL, and React.  
The objective is not maximal scale; it is high-confidence architecture, auditability, and realistic operational behavior.

---

## Decision 1: Monolith (Django + DRF) instead of microservices

### Decision
Use a single backend service with clear internal modules (`models`, `serializers`, `services`, `views`).

### Why
- Faster delivery with fewer operational risks.
- Easier end-to-end debugging during ingestion/review workflows.
- Better interview signal: practical scope control and coherent boundaries.

### Alternatives considered
- Microservices by data source (SAP/Utility/Travel)
- Separate ingestion and review services

### Tradeoffs
- Monolith limits independent scaling per subsystem.
- Acceptable for assignment load and prototype maturity.

### Revisit trigger
If upload throughput or team size grows significantly.

---

## Decision 2: Synchronous CSV ingestion (no queue initially)

### Decision
Ingestion executes immediately within API request flow.

### Why
- Simpler implementation and operation in short timeline.
- Reduces moving parts (no broker, worker, retry semantics).
- Easier to reason about data lineage for demo and review.

### Alternatives considered
- Celery + Redis asynchronous workers
- External ETL pipeline

### Tradeoffs
- Large files may increase request latency.
- Mitigated by realistic CSV size assumptions and explicit batch status tracking.

### Revisit trigger
If ingestion latency becomes user-visible or timeout-prone.

---

## Decision 3: Raw + normalized dual storage model

### Decision
Persist each imported row in `RawIngestRow`, then create `NormalizedEmissionRecord`.

### Why
- Preserves forensic source truth.
- Enables deterministic replay/debug of normalization.
- Supports strong audit narratives ("what arrived" vs "what was derived").

### Alternatives considered
- Store only normalized rows
- Store only raw rows and normalize on read

### Tradeoffs
- Increased storage footprint.
- Worth it for auditability and operational support.

### Revisit trigger
If storage cost dominates; introduce retention policy for raw rows after compliance window.

---

## Decision 4: Application-level multi-tenancy

### Decision
Use `organization_id` on domain tables with tenant-filtered DRF querysets.

### Why
- Fastest realistic tenant isolation pattern for this scope.
- Keeps schema simple and supports shared operations.
- Easy to enforce in one codebase.

### Alternatives considered
- Separate database per tenant
- PostgreSQL Row-Level Security (RLS)

### Tradeoffs
- Security relies on disciplined query filtering.
- Mitigation: centralized tenant-filter base viewset and serializer-level validation.

### Revisit trigger
If compliance requires stronger database-enforced isolation.

---

## Decision 5: Explicit workflow states instead of dynamic workflow engine

### Decision
Use fixed statuses: `pending`, `suspicious`, `approved`, `rejected`.

### Why
- Fully matches assignment requirements.
- Easy for analysts and reviewers to understand.
- Avoids overengineering before business workflow stabilizes.

### Alternatives considered
- Configurable state machine with admin-defined transitions
- BPM/workflow orchestration tool

### Tradeoffs
- Less flexible for future custom process variations.
- Good trade for clarity and predictable behavior.

### Revisit trigger
If multiple teams require divergent approval flows.

---

## Decision 6: Deterministic rules-based suspicious detection

### Decision
Use explainable validation flags and weighted suspicion score.

### Why
- Analysts can understand why a row was flagged.
- Easy to tune thresholds per rule.
- Strong audit and governance posture vs opaque ML scoring.

### Alternatives considered
- ML anomaly detection from historical data
- Pure boolean pass/fail validation

### Tradeoffs
- May miss nuanced anomalies ML could catch.
- Intentionally favors explainability and fast iteration.

### Revisit trigger
If sufficient history accumulates and false positives become high.

---

## Decision 7: Emission factors as versioned table with date windows

### Decision
Model `EmissionFactor` with `valid_from`, `valid_to`, scope, activity, and unit.

### Why
- Realistic handling of factor updates over time.
- Supports organization-specific override with global fallback.
- Enables reproducible historical calculations.

### Alternatives considered
- Hardcoded constants in code
- External factor API dependency during ingestion

### Tradeoffs
- Requires factor data management lifecycle.
- Acceptable and necessary for credibility in ESG reporting.

### Revisit trigger
If frequent factor updates require dedicated admin tooling.

---

## Decision 8: Lock approved rows for audit integrity

### Decision
Approved records can be marked locked; locked rows are non-editable.

### Why
- Protects audited outputs from silent mutation.
- Mirrors compliance expectations for approved reporting data.
- Encourages correction through explicit tracked actions.

### Alternatives considered
- Allow unrestricted edits with last-updated timestamp only
- Snapshot exports only, mutable base records

### Tradeoffs
- Corrections require additional workflow steps.
- Worth it for trust and audit defensibility.

### Revisit trigger
If legal/compliance process defines a formal amendment workflow.

---

## Decision 9: Append-only record change log

### Decision
Write `RecordChangeLog` entries for lifecycle events and key field transitions.

### Why
- Creates a complete timeline of who changed what and why.
- Enables root-cause analysis for disputed numbers.
- Supports transparent analyst behavior review.

### Alternatives considered
- Rely on `updated_at` only
- Full event-sourcing of entire domain

### Tradeoffs
- More writes and payload storage.
- Much lower complexity than full event sourcing with high audit value.

### Revisit trigger
If event volume grows, archive older logs to cheaper storage.

---

## Decision 10: React + React Query + Axios, no heavy frontend state framework

### Decision
Use route-level pages with React Query for server state and Axios API client.

### Why
- Fast delivery and straightforward mental model.
- Caching/invalidation handled without custom logic.
- Keeps frontend focused on analyst workflow.

### Alternatives considered
- Redux Toolkit/Zustand with normalized client store
- GraphQL client stack

### Tradeoffs
- Less control for very complex client-side state graphs.
- Appropriate for server-driven internal tool.

### Revisit trigger
If UI complexity expands into multi-step offline workflows.

---

## Decision 11: Keep auth simple for prototype

### Decision
Use Django auth + app profile organization mapping.

### Why
- Satisfies role and ownership needs for this assignment.
- Avoids security theater from partially implemented SSO/RBAC stacks.

### Alternatives considered
- Full SSO (OAuth/OIDC)
- Advanced policy engines

### Tradeoffs
- Not enterprise identity-complete.
- Correct scope for prototype; leaves upgrade path open.

### Revisit trigger
If deployment moves to production or external users are onboarded.

---

## Decision 12: Deploy on Render/Railway with PostgreSQL

### Decision
Deploy as one backend service + one frontend app + managed Postgres.

### Why
- Low operational friction.
- Managed DB and easy environment variable workflow.
- Fits assignment deployment expectations.

### Alternatives considered
- Kubernetes cluster
- Self-managed VM stack

### Tradeoffs
- Less infrastructure control.
- Right trade for speed and reliability at prototype stage.

### Revisit trigger
If SLO or compliance requirements exceed platform capabilities.

---

## What We Intentionally Did Not Build

- No microservices or event bus.
- No Kubernetes or infrastructure-heavy setup.
- No asynchronous ingestion pipeline at this stage.
- No dynamic workflow/rules DSL.
- No over-generalized abstractions disconnected from assignment requirements.

These exclusions are deliberate and reflect judgment: build the smallest architecture that is correct, auditable, and extensible.
