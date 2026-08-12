"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import ProductSelect from "@/components/inventory/ProductSelect";

export default function ForecastsPage() {
  const [productId, setProductId] = useState("");
  const [horizon, setHorizon] = useState(14);
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
      const data = await apiFetch(`/api/v1/forecasts/${productId}?horizon=${horizon}`);
      if (data?.error === "insufficient_history") {
        toast.error("Not enough sales history for this product (needs 14+ days). Pick another product.");
        return;
      }
      setResult(data);
      toast.success(`Forecast generated (${data.model})`);
    } catch (e: any) {
      if (!e.handled) toast.error(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Demand Forecasts</h1>
        <p className="text-slate-500 text-sm">Compare moving average, exponential smoothing, and XGBoost-lag models</p>
      </div>
      <div className="kpi-card space-y-4 max-w-xl">
        <ProductSelect value={productId} onChange={setProductId} />
        <div>
          <label className="block text-sm font-medium mb-1">Horizon (days)</label>
          <input type="number" className="w-full border rounded-lg px-3 py-2" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} />
        </div>
        <button onClick={run} disabled={loading} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50">
          {loading ? "Generating…" : "Generate Forecast"}
        </button>
      </div>

      {result && (
        <div className="kpi-card max-w-xl">
          <h2 className="font-medium mb-3">Result</h2>
          <div className="grid grid-cols-2 gap-3 text-sm mb-3">
            <div><span className="text-slate-500">Model:</span> {result.model}</div>
            <div><span className="text-slate-500">Horizon:</span> {result.horizon} days</div>
            <div><span className="text-slate-500">MAE:</span> {result.mae}</div>
            <div><span className="text-slate-500">RMSE:</span> {result.rmse}</div>
            <div><span className="text-slate-500">MAPE:</span> {result.mape}%</div>
            <div><span className="text-slate-500">Total predicted demand:</span> {result.predicted_demand_total}</div>
          </div>
        </div>
      )}
    </div>
  );
}
