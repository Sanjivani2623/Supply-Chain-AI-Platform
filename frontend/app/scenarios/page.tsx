"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import ProductSelect from "@/components/inventory/ProductSelect";

export default function ScenariosPage() {
  const [productId, setProductId] = useState("");
  const [supplierDelay, setSupplierDelay] = useState(0);
  const [demandChange, setDemandChange] = useState(0);
  const [transportChange, setTransportChange] = useState(0);
  const [duration, setDuration] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    if (!productId) {
      toast.error("Pick a product first");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const data = await apiFetch("/api/v1/scenarios/simulate", {
        method: "POST",
        body: JSON.stringify({
          product_id: productId,
          supplier_delay_days: supplierDelay,
          demand_change_pct: demandChange,
          transport_cost_change_pct: transportChange,
          disruption_duration_days: duration,
        }),
      });
      if (data?.error === "insufficient_history") {
        toast.error("Not enough sales history for this product. Pick another product.");
        return;
      }
      setResult(data);
      toast.success("Scenario simulated");
    } catch (e: any) {
      if (!e.handled) toast.error(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">What-If Scenario Simulator</h1>
        <p className="text-slate-500 text-sm">Model the impact of disruptions before they happen</p>
      </div>

      <div className="kpi-card space-y-4 max-w-xl">
        <ProductSelect value={productId} onChange={setProductId} />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Supplier delay (+days)</label>
            <input type="number" className="w-full border rounded-lg px-3 py-2" value={supplierDelay} onChange={(e) => setSupplierDelay(Number(e.target.value))} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Demand change (%)</label>
            <input type="number" className="w-full border rounded-lg px-3 py-2" value={demandChange} onChange={(e) => setDemandChange(Number(e.target.value))} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Transport cost change (%)</label>
            <input type="number" className="w-full border rounded-lg px-3 py-2" value={transportChange} onChange={(e) => setTransportChange(Number(e.target.value))} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Disruption duration (days)</label>
            <input type="number" className="w-full border rounded-lg px-3 py-2" value={duration} onChange={(e) => setDuration(Number(e.target.value))} />
          </div>
        </div>
        <button onClick={run} disabled={loading} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50">
          {loading ? "Simulating…" : "Run Simulation"}
        </button>
      </div>

      {result && (
        <div className="kpi-card max-w-2xl grid grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-slate-500 text-sm mb-2">Before</h3>
            <div className="text-sm space-y-1">
              <div>Reorder point: {result.before.reorder_point}</div>
              <div>Safety stock: {result.before.safety_stock}</div>
              <div>Stockout probability: {(result.before.stockout_probability * 100).toFixed(1)}%</div>
              <div>Service level: {result.before.service_level_pct}%</div>
            </div>
          </div>
          <div>
            <h3 className="font-medium text-slate-500 text-sm mb-2">After</h3>
            <div className="text-sm space-y-1">
              <div>Reorder point: {result.after.reorder_point}</div>
              <div>Safety stock: {result.after.safety_stock}</div>
              <div>Stockout probability: {(result.after.stockout_probability * 100).toFixed(1)}%</div>
              <div>Service level: {result.after.service_level_pct}%</div>
              <div>Required reorder qty: {result.after.required_reorder_quantity}</div>
            </div>
          </div>
          <div className="col-span-2 text-sm border-t pt-3">
            Additional cost: <span className="font-semibold">${result.additional_cost}</span>
          </div>
        </div>
      )}
    </div>
  );
}
