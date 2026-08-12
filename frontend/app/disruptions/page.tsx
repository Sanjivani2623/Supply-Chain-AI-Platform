"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import Badge from "@/components/common/Badge";
import type { DisruptionEvent } from "@/lib/types";

export default function DisruptionsPage() {
  const [events, setEvents] = useState<DisruptionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [seeding, setSeeding] = useState(false);

  function load() {
    setLoading(true);
    apiFetch<DisruptionEvent[]>("/api/v1/disruptions")
      .then(setEvents)
      .catch((e: any) => {
        if (!e.handled) toast.error(`Couldn't load disruptions: ${e.message}`);
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function ingest() {
    setIngesting(true);
    try {
      const res = await apiFetch<{ fetched: number; created: number; disruption_events: number }>(
        "/api/v1/disruptions/ingest?max_articles=20",
        { method: "POST" }
      );
      if (res.fetched === 0) {
        toast.info("No articles fetched — set EVENT_REGISTRY_API_KEY in backend/.env for live news ingestion, or use \"Seed Demo Disruptions\" below.");
      } else {
        toast.success(`Ingested ${res.created} new articles, ${res.disruption_events} disruption events`);
      }
      load();
    } catch (e: any) {
      if (!e.handled) toast.error(e.message);
    } finally {
      setIngesting(false);
    }
  }

  async function seedDemo() {
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Disruptions</h1>
          <p className="text-slate-500 text-sm">Detected supply chain disruption events</p>
        </div>
        <div className="flex gap-2">
          <button onClick={seedDemo} disabled={seeding} className="bg-white border border-slate-300 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-50 disabled:opacity-50">
            {seeding ? "Seeding…" : "Seed Demo Disruptions"}
          </button>
          <button onClick={ingest} disabled={ingesting} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50">
            {ingesting ? "Ingesting…" : "Run Live Ingestion"}
          </button>
        </div>
      </div>

      <div className="kpi-card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="py-2 pr-4">Type</th>
              <th className="py-2 pr-4">Severity</th>
              <th className="py-2 pr-4">Location</th>
              <th className="py-2 pr-4">Affected Supplier</th>
              <th className="py-2 pr-4">Confidence</th>
              <th className="py-2 pr-4">Date</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id} className="border-b last:border-0">
                <td className="py-2 pr-4">{e.disruption_type || "—"}</td>
                <td className="py-2 pr-4"><Badge level={e.severity} /></td>
                <td className="py-2 pr-4">{e.location || "—"}</td>
                <td className="py-2 pr-4">{e.affected_supplier || "—"}</td>
                <td className="py-2 pr-4">{Math.round(e.confidence * 100)}%</td>
                <td className="py-2 pr-4">{new Date(e.event_date).toLocaleDateString()}</td>
              </tr>
            ))}
            {!loading && events.length === 0 && (
              <tr><td colSpan={6} className="py-8 text-center text-slate-400">
                No disruption events yet. Click &quot;Seed Demo Disruptions&quot; for sample data, or configure
                EVENT_REGISTRY_API_KEY and run live ingestion.
              </td></tr>
            )}
            {loading && (
              <tr><td colSpan={6} className="py-8 text-center text-slate-400">Loading…</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
