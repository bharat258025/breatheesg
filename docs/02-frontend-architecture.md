# Frontend Architecture (React + Tailwind + React Query)

## Structure

- `src/app`: app-wide wiring (`router`, `queryClient`)
- `src/api`: axios client + ESG endpoint calls
- `src/hooks`: React Query hooks as UI-facing data boundary
- `src/components`: reusable UI blocks (`layout`, `records`, `common`)
- `src/pages`: route-level screens
- `src/types`: shared DTO types

## Page flow

1. Dashboard: operational counts by record status
2. Ingestion: source selection + CSV upload + batch summary
3. Review Queue: filtered table for analyst triage
4. Record Detail: record inspection + approve/reject + audit log

## Why this works for the assignment

- Keeps business workflows explicit (ingest/review/audit) instead of generic CRUD menus.
- React Query gives predictable server-state handling without custom cache complexity.
- API calls are centralized and typed, so backend changes are easy to localize.
- Route/page split mirrors analyst tasks and interview story.

## Tradeoffs

- No global state library (Redux/Zustand) to keep velocity high in 4 days.
- No component library dependency to avoid design-system setup overhead.
- Minimal optimistic updates; rely on server truth and cache invalidation.

## What we intentionally did not build

- No complex role-permission UI matrix.
- No dynamic workflow designer.
- No heavy charting layer before core ingestion/review correctness.
