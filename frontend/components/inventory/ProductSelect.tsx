"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import type { Product } from "@/lib/types";

interface Props {
  value: string;
  onChange: (productId: string) => void;
  label?: string;
}

/** Dropdown of "SKU — Name" backed by /api/v1/products, so pages never make
 * the user hand-type a raw product UUID. */
export default function ProductSelect({ value, onChange, label = "Product" }: Props) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Product[]>("/api/v1/products")
      .then((data) => {
        setProducts(data);
        if (!value && data.length > 0) onChange(data[0].id);
      })
      .catch((e: any) => {
        if (!e.handled) toast.error(`Couldn't load products: ${e.message}`);
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      <select
        className="w-full border rounded-lg px-3 py-2 bg-white"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={loading}
      >
        {loading && <option>Loading products…</option>}
        {!loading && products.length === 0 && <option>No products found — seed the database first</option>}
        {products.map((p) => (
          <option key={p.id} value={p.id}>
            {p.sku} — {p.name} ({p.category})
          </option>
        ))}
      </select>
    </div>
  );
}
