"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import KpiCard from "@/components/dashboard/KpiCard";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import type { KPIs } from "@/lib/types";

const COLORS = ["#4f46e5", "#f59e0b", "#ef4444", "#10b981", "#6366f1", "#f97316"];

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [byType, setByType] = useState<any[]>([]);
  const [byCountry, setByCountry] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  function load() {
    setLoading(true);
    Promise.all([
      apiFetch<KPIs>("/api/v1/analytics/kpis"),
      apiFetch<any[]>("/api/v1/analytics/disruptions-by-type"),
      apiFetch<any[]>("/api/v1/analytics/risk-by-country"),
    ])
      .then(([k, t, c]) => {
        setKpis(k);
        setByType(t.filter((x) => x.type && x.type !== "unknown"));
        setByCountry(c);
      })
      .catch((e: any) => {
        if (!e.handled) toast.error(`Couldn't load dashboard data: ${e.message}`);
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function seedDemoDisruptions() {
    setSeeding(true);
    try {
      const res = await apiFetch<{ created: number }>("/api/v1/disruptions/seed-demo", { method: "POST" });
      toast.success(`Seeded ${res.created} demo disruption events`);
      load();
    } catch (e: any) {
      if (!e.handled) toast.error(e.message);
    } finally {
      setSeeding(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-slate-500 text-sm">Real-time supply chain health overview</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard label="Active Disruptions" value={loading ? "…" : kpis?.active_disruptions ?? 0} />
        <KpiCard label="High-Risk Suppliers" value={loading ? "…" : kpis?.high_risk_suppliers ?? 0} />
        <KpiCard label="Inventory At Risk" value={loading ? "…" : kpis?.inventory_at_risk ?? 0} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="kpi-card">
          <h2 className="font-medium mb-4">Disruptions by Type</h2>
          {byType.length === 0 && !loading ? (
            <div className="h-[260px] flex flex-col items-center justify-center text-center gap-3">
              <p className="text-sm text-slate-400 max-w-xs">
                No disruption events yet. This is expected without a live news feed
                (EVENT_REGISTRY_API_KEY) — seed some realistic demo data instead.
              </p>
              <button
                onClick={seedDemoDisruptions}
                disabled={seeding}
                className="text-sm bg-brand-600 text-white px-3 py-1.5 rounded-lg hover:bg-brand-700 disabled:opacity-50"
              >
                {seeding ? "Seeding…" : "Seed Demo Disruptions"}
              </button>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byType}>
                <XAxis dataKey="type" hide />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="kpi-card">
          <h2 className="font-medium mb-4">Average Risk by Country</h2>
          {byCountry.length === 0 && !loading ? (
            <div className="h-[260px] flex items-center justify-center text-sm text-slate-400">
              No supplier data yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={byCountry} dataKey="avg_risk" nameKey="country" outerRadius={90} label>
                  {byCountry.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
