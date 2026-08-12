"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import Badge from "@/components/common/Badge";
import type { Supplier } from "@/lib/types";

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Supplier[]>("/api/v1/suppliers")
      .then(setSuppliers)
      .catch((e: any) => {
        if (!e.handled) toast.error(`Couldn't load suppliers: ${e.message}`);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Suppliers</h1>
        <p className="text-slate-500 text-sm">Reliability and risk scoring across your supplier base</p>
      </div>
      <div className="kpi-card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="py-2 pr-4">Name</th>
              <th className="py-2 pr-4">Country</th>
              <th className="py-2 pr-4">Reliability</th>
              <th className="py-2 pr-4">Avg Delay (days)</th>
              <th className="py-2 pr-4">Disruptions</th>
              <th className="py-2 pr-4">Risk</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((s) => (
              <tr key={s.id} className="border-b last:border-0">
                <td className="py-2 pr-4 font-medium">{s.name}</td>
                <td className="py-2 pr-4">{s.country || "—"}</td>
                <td className="py-2 pr-4">{s.reliability_score}</td>
                <td className="py-2 pr-4">{s.average_delay}</td>
                <td className="py-2 pr-4">{s.disruption_count}</td>
                <td className="py-2 pr-4"><Badge level={s.risk_level} /> <span className="text-slate-400 text-xs ml-1">{s.risk_score}/100</span></td>
              </tr>
            ))}
            {!loading && suppliers.length === 0 && (
              <tr><td colSpan={6} className="py-8 text-center text-slate-400">No suppliers loaded yet. Seed the database first.</td></tr>
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
