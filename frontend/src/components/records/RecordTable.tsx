import { Link } from "react-router-dom";

import type { NormalizedRecord } from "../../types/esg";
import { StatusBadge } from "../common/StatusBadge";

type Props = { records: NormalizedRecord[] };

export function RecordTable({ records }: Props) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-600">
          <tr>
            <th className="px-4 py-3">Record</th>
            <th className="px-4 py-3">Date</th>
            <th className="px-4 py-3">Scope</th>
            <th className="px-4 py-3">Activity</th>
            <th className="px-4 py-3">Emissions tCO2e</th>
            <th className="px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {records.map((r) => (
            <tr key={r.id} className="border-t border-slate-100">
              <td className="px-4 py-3">
                <Link className="text-tide underline-offset-2 hover:underline" to={`/records/${r.id}`}>
                  #{r.id}
                </Link>
              </td>
              <td className="px-4 py-3">{r.activity_date}</td>
              <td className="px-4 py-3 uppercase">{r.scope}</td>
              <td className="px-4 py-3">{r.activity_type}</td>
              <td className="px-4 py-3">{r.emissions_tco2e}</td>
              <td className="px-4 py-3">
                <StatusBadge status={r.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
