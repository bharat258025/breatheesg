import { FormEvent, useState } from "react";

import { useSources, useUploadCsv } from "../hooks/useEsgQueries";

export function UploadPage() {
  const { data: sources = [], isLoading: sourcesLoading, error: sourcesError } = useSources();
  const uploadMutation = useUploadCsv();

  const [sourceId, setSourceId] = useState<number | "">("");
  const [file, setFile] = useState<File | null>(null);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!sourceId || !file) return;
    uploadMutation.mutate({ sourceSystemId: sourceId, file });
  };

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold">CSV Ingestion</h2>
      <form onSubmit={onSubmit} className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
        <div>
          <label className="mb-1 block text-sm text-slate-600">Source System</label>
          {sourcesLoading ? <p className="mb-2 text-xs text-slate-500">Loading sources...</p> : null}
          {sourcesError ? (
            <p className="mb-2 text-xs text-rose-600">
              Could not load source systems. Check backend auth/CORS and confirm `GET /api/sources/` works in browser.
            </p>
          ) : null}
          <select
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            value={sourceId}
            onChange={(e) => setSourceId(Number(e.target.value))}
          >
            <option value="">Select source</option>
            {sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.display_name} ({s.source_type})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-600">CSV File</label>
          <input className="block w-full text-sm" type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
        <button
          type="submit"
          disabled={uploadMutation.isPending}
          className="rounded-md bg-tide px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {uploadMutation.isPending ? "Processing..." : "Upload and Process"}
        </button>
      </form>

      {uploadMutation.data ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm">
          <p>Batch #{uploadMutation.data.batch_id} processed.</p>
          <p>
            Parsed: {uploadMutation.data.summary.parsed_rows} / {uploadMutation.data.summary.total_rows}, Errors:{" "}
            {uploadMutation.data.summary.error_rows}
          </p>
        </div>
      ) : null}
    </section>
  );
}
