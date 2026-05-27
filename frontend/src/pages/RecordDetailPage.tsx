import { useState } from "react";
import { useParams } from "react-router-dom";

import { StatusBadge } from "../components/common/StatusBadge";
import { useRecord, useRecordLogs, useUpdateRecordStatus } from "../hooks/useEsgQueries";

export function RecordDetailPage() {
  const { recordId } = useParams();
  const { data: record, isLoading } = useRecord(recordId);
  const { data: logs = [] } = useRecordLogs(record?.id);
  const statusMutation = useUpdateRecordStatus();
  const [reason, setReason] = useState("");

  if (isLoading) return <p>Loading record...</p>;
  if (!record) return <p>Record not found.</p>;

  return (
    <section className="space-y-4">
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Record #{record.id}</h2>
          <StatusBadge status={record.status} />
        </div>
        <dl className="mt-4 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
          <div><dt className="text-slate-500">Activity</dt><dd>{record.activity_type}</dd></div>
          <div><dt className="text-slate-500">Scope</dt><dd>{record.scope}</dd></div>
          <div><dt className="text-slate-500">Normalized Quantity</dt><dd>{record.normalized_quantity} {record.normalized_unit}</dd></div>
          <div><dt className="text-slate-500">Emissions</dt><dd>{record.emissions_tco2e} tCO2e</dd></div>
          <div><dt className="text-slate-500">Flags</dt><dd>{record.validation_flags.join(", ") || "none"}</dd></div>
          <div><dt className="text-slate-500">Suspicion Score</dt><dd>{record.suspicion_score}</dd></div>
        </dl>
      </div>

      {!record.is_locked ? (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold uppercase text-slate-500">Analyst Action</h3>
          {statusMutation.isError ? (
            <p className="mb-3 text-sm text-rose-600">Action failed. Please check backend response and try again.</p>
          ) : null}
          {statusMutation.isSuccess ? <p className="mb-3 text-sm text-emerald-700">Action saved.</p> : null}
          <div className="flex flex-wrap items-center gap-2">
            <button
              disabled={statusMutation.isPending}
              className="rounded-md bg-emerald-600 px-3 py-2 text-sm text-white"
              onClick={() => statusMutation.mutate({ recordId: record.id, status: "approved" })}
            >
              Approve
            </button>
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Rejection reason"
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              disabled={statusMutation.isPending}
              className="rounded-md bg-rose-600 px-3 py-2 text-sm text-white"
              onClick={() => statusMutation.mutate({ recordId: record.id, status: "rejected", rejection_reason: reason })}
            >
              Reject
            </button>
          </div>
        </div>
      ) : null}

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold uppercase text-slate-500">Audit Trail</h3>
        <ul className="space-y-2 text-sm">
          {logs.map((log) => (
            <li key={log.id} className="rounded-md bg-slate-50 p-3">
              <p className="font-medium">{log.event_type}</p>
              <p className="text-slate-500">{new Date(log.created_at).toLocaleString()}</p>
              <p>{log.reason || "No reason captured"}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
