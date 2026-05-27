import { useMemo } from "react";

import { useRecords } from "../hooks/useEsgQueries";

export function DashboardPage() {
  const { data: records = [], isLoading } = useRecords();

  const metrics = useMemo(() => {
    const summary = { pending: 0, suspicious: 0, approved: 0, rejected: 0 };
    for (const rec of records) {
      summary[rec.status] += 1;
    }
    return summary;
  }, [records]);

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold">Analyst Ops Dashboard</h2>
      {isLoading ? <p>Loading...</p> : null}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(metrics).map(([key, value]) => (
          <div key={key} className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-sm uppercase text-slate-500">{key}</p>
            <p className="mt-2 text-2xl font-semibold">{value}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
