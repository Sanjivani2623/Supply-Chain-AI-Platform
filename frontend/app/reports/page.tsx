"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";

export default function ReportsPage() {
  const [daily, setDaily] = useState<any>(null);
  const [weekly, setWeekly] = useState<any>(null);
  const [loadingDaily, setLoadingDaily] = useState(false);
  const [loadingWeekly, setLoadingWeekly] = useState(false);

  async function genDaily() {
    setLoadingDaily(true);
    try {
      setDaily(await apiFetch("/api/v1/reports/daily"));
      toast.success("Daily report generated");
    } catch (e: any) {
      if (!e.handled) toast.error(e.message);
    } finally {
      setLoadingDaily(false);
    }
  }

  async function genWeekly() {
    setLoadingWeekly(true);
    try {
      setWeekly(await apiFetch("/api/v1/reports/weekly"));
      toast.success("Weekly report generated");
    } catch (e: any) {
      if (!e.handled) toast.error(e.message);
    } finally {
      setLoadingWeekly(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Reports</h1>
        <p className="text-slate-500 text-sm">Generate daily and weekly supply chain summaries</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="kpi-card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium">Daily Report</h2>
            <button onClick={genDaily} disabled={loadingDaily} className="text-sm bg-brand-600 text-white px-3 py-1.5 rounded-lg hover:bg-brand-700 disabled:opacity-50">
              {loadingDaily ? "Generating…" : "Generate"}
            </button>
          </div>
          {daily && <pre className="text-xs bg-slate-50 rounded-lg p-4 overflow-x-auto">{JSON.stringify(daily, null, 2)}</pre>}
        </div>
        <div className="kpi-card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium">Weekly Report</h2>
            <button onClick={genWeekly} disabled={loadingWeekly} className="text-sm bg-brand-600 text-white px-3 py-1.5 rounded-lg hover:bg-brand-700 disabled:opacity-50">
              {loadingWeekly ? "Generating…" : "Generate"}
            </button>
          </div>
          {weekly && <pre className="text-xs bg-slate-50 rounded-lg p-4 overflow-x-auto">{JSON.stringify(weekly, null, 2)}</pre>}
        </div>
      </div>
    </div>
  );
}
