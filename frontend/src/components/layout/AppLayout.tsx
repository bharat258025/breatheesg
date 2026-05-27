import { Link, Outlet, useLocation } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/upload", label: "Ingestion" },
  { to: "/review", label: "Review Queue" }
];

export function AppLayout() {
  const location = useLocation();
  return (
    <div className="min-h-screen bg-slate-100 text-ink">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <h1 className="text-xl font-semibold">Breathe ESG Console</h1>
          <nav className="flex gap-2">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`rounded-md px-3 py-2 text-sm ${
                  location.pathname === item.to ? "bg-tide text-white" : "text-slate-700 hover:bg-slate-200"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}
