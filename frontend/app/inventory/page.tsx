"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import type { InventoryItem } from "@/lib/types";

export default function InventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [showAtRisk, setShowAtRisk] = useState(false);
  const [loading, setLoading] = useState(true);
  const [recLoading, setRecLoading] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const path = showAtRisk ? "/api/v1/inventory/at-risk" : "/api/v1/inventory";
    apiFetch<InventoryItem[]>(path)
      .then(setItems)
      .catch((e: any) => {
        if (!e.handled) toast.error(`Couldn't load inventory: ${e.message}`);
      })
      .finally(() => setLoading(false));
  }, [showAtRisk]);

  async function getRecommendation(productId: string, sku?: string) {
    setRecLoading(productId);
    try {
      const rec = await apiFetch<any>(`/api/v1/recommendations/${productId}`);
      if (rec.recommended_quantity > 0) {
        toast.success(`${sku || "Product"}: order ${rec.recommended_quantity} units — ${rec.reason}`);
      } else {
        toast.info(`${sku || "Product"}: no reorder needed right now (stockout risk ${(rec.stockout_probability * 100).toFixed(1)}%)`);
      }
    } catch (e: any) {
      if (!e.handled) toast.error(e.message);
    } finally {
      setRecLoading(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Inventory</h1>
          <p className="text-slate-500 text-sm">Stock levels, reorder points, and safety stock</p>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={showAtRisk} onChange={(e) => setShowAtRisk(e.target.checked)} />
          Show at-risk only
        </label>
      </div>
      <div className="kpi-card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="py-2 pr-4">SKU</th>
              <th className="py-2 pr-4">Product</th>
              <th className="py-2 pr-4">Current Stock</th>
              <th className="py-2 pr-4">Available</th>
              <th className="py-2 pr-4">Reorder Point</th>
              <th className="py-2 pr-4">Safety Stock</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4"></th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => {
              const atRisk = i.available_stock < i.reorder_point;
              return (
                <tr key={i.id} className="border-b last:border-0">
                  <td className="py-2 pr-4 font-mono text-xs font-medium">{i.sku || "—"}</td>
                  <td className="py-2 pr-4">{i.product_name || "—"}</td>
                  <td className="py-2 pr-4">{i.current_stock}</td>
                  <td className="py-2 pr-4">{i.available_stock}</td>
                  <td className="py-2 pr-4">{i.reorder_point}</td>
                  <td className="py-2 pr-4">{i.safety_stock}</td>
                  <td className="py-2 pr-4">
                    <span className={`badge ${atRisk ? "badge-high" : "badge-low"}`}>{atRisk ? "At Risk" : "Healthy"}</span>
                  </td>
                  <td className="py-2 pr-4">
                    <button
                      onClick={() => getRecommendation(i.product_id, i.sku)}
                      disabled={recLoading === i.product_id}
                      className="text-xs text-brand-600 hover:text-brand-700 font-medium disabled:opacity-50"
                    >
                      {recLoading === i.product_id ? "Checking…" : "Get recommendation"}
                    </button>
                  </td>
                </tr>
              );
            })}
            {!loading && items.length === 0 && (
              <tr><td colSpan={8} className="py-8 text-center text-slate-400">No inventory data yet. Seed the database first.</td></tr>
            )}
            {loading && (
              <tr><td colSpan={8} className="py-8 text-center text-slate-400">Loading…</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
