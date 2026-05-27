type Props = { status: string };

const classes: Record<string, string> = {
  pending: "bg-slate-200 text-slate-700",
  suspicious: "bg-amber-100 text-amber-800",
  approved: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-800"
};

export function StatusBadge({ status }: Props) {
  return <span className={`rounded-full px-2 py-1 text-xs font-medium ${classes[status] ?? classes.pending}`}>{status}</span>;
}
