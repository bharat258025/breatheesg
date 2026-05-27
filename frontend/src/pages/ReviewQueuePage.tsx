import { useState } from "react";

import { useRecords } from "../hooks/useEsgQueries";
import { RecordTable } from "../components/records/RecordTable";

const FILTERS = ["all", "pending", "suspicious", "approved", "rejected"] as const;

export function ReviewQueuePage() {
  const [statusFilter, setStatusFilter] = useState<(typeof FILTERS)[number]>("pending");
  const queryStatus = statusFilter === "all" ? undefined : statusFilter;
  const { data: records = [], isLoading } = useRecords(queryStatus);

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold">Analyst Review Queue</h2>
      <div className="flex flex-wrap gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter}
            onClick={() => setStatusFilter(filter)}
            className={`rounded-md px-3 py-2 text-sm ${
              statusFilter === filter ? "bg-ink text-white" : "bg-white text-slate-700 border border-slate-300"
            }`}
          >
            {filter}
          </button>
        ))}
      </div>
      {isLoading ? <p>Loading records...</p> : <RecordTable records={records} />}
    </section>
  );
}
