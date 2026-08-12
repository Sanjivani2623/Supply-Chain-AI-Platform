"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import Badge from "@/components/common/Badge";

interface AlertItem {
  id: string; alert_type: string; severity: string; title: string;
  message: string; status: string; created_at: string;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  function load() {
    setLoading(true);
    apiFetch<AlertItem[]>("/api/v1/alerts")
      .then(setAlerts)
      .catch((e: any) => {
        if (!e.handled) toast.error(`Couldn't load alerts: ${e.message}`);
      })
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function runChecks() {
    setRunning(true);
    try {
      const res = await apiFetch<{ inventory_alerts: number; supplier_alerts: number }>("/api/v1/alerts/run-checks", { method: "POST" });
      const total = res.inventory_alerts + res.supplier_alerts;
      if (total > 0) {
        toast.success(`Found ${res.inventory_alerts} inventory + ${res.supplier_alerts} supplier alerts`);
      } else {
        toast.info("No new alerts — everything looks healthy");
      }
      load();
    } catch (e: any) {
      if (!e.handled) toast.error(e.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Alerts</h1>
          <p className="text-slate-500 text-sm">Inventory, supplier, and disruption alert history</p>
        </div>
        <button onClick={runChecks} disabled={running} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50">
          {running ? "Checking…" : "Run Alert Checks"}
        </button>
      </div>

      <div className="space-y-3">
        {alerts.map((a) => (
          <div key={a.id} className="kpi-card flex items-start justify-between">
            <div>
              <div className="font-medium">{a.title}</div>
              <div className="text-sm text-slate-500">{a.message}</div>
              <div className="text-xs text-slate-400 mt-1">{new Date(a.created_at).toLocaleString()} · {a.alert_type}</div>
            </div>
            <Badge level={a.severity} />
          </div>
        ))}
        {!loading && alerts.length === 0 && <div className="kpi-card text-center text-slate-400 py-8">No alerts yet — click &quot;Run Alert Checks&quot;.</div>}
        {loading && <div className="kpi-card text-center text-slate-400 py-8">Loading…</div>}
      </div>
    </div>
  );
}
