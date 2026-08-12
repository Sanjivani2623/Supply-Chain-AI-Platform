"""
Generates realistic, internally-consistent synthetic datasets (section 47-48)
and seeds the PostgreSQL database defined by DATABASE_URL.

Reuses the REAL collected data in backend/data/merged_supply_chain_data.xlsx
(from the original Event-Registry-based notebooks) as the source of:
  - supplier names / countries / regions
  - product categories ("Item")
  - article text used to build the disruption-classifier training set

Consistency rules enforced:
  - Supplier reliability drives average delay & lead time.
  - Product lead time/safety stock derive from the supplier.
  - Demand (sales) drives inventory drawdown.
  - Historical disruptions raise supplier risk_score / risk_level.

Usage:
    python scripts/generate_synthetic_data.py --seed-db
    python scripts/generate_synthetic_data.py --csv-only   # only writes data/synthetic_articles.csv
"""
import argparse
import os
import random
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

random.seed(42)
np.random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
XLSX_PATH = os.path.join(DATA_DIR, "merged_supply_chain_data.xlsx")

CATEGORIES = ["Electronics", "Automotive Parts", "Pharmaceuticals", "Textiles", "Food & Beverage",
              "Industrial Equipment", "Consumer Goods", "Chemicals", "Semiconductors", "Packaging"]


def load_real_source() -> pd.DataFrame:
    df = pd.read_excel(XLSX_PATH)
    df["Summary"] = df["Summary"].fillna("")
    df["Risk Factor"] = pd.to_numeric(df["Risk Factor"], errors="coerce").fillna(0.05)
    return df


def build_synthetic_articles_csv(real_df: pd.DataFrame) -> pd.DataFrame:
    """Builds a labeled [text, label] dataset for the ML disruption classifier,
    weakly-labeled from the real article summaries + keyword taxonomy."""
    from app.services.disruption.taxonomy import TAXONOMY

    rows = []
    for _, r in real_df.iterrows():
        text = f"{r.get('Title', '')} {r.get('Summary', '')} {r.get('Keyword', '')}".lower()
        best_label, best_hits = None, 0
        for label, keywords in TAXONOMY.items():
            hits = sum(1 for kw in keywords if kw in text)
            if hits > best_hits:
                best_label, best_hits = label, hits
        if best_label:
            rows.append({"text": text, "label": best_label})

    out = pd.DataFrame(rows).drop_duplicates(subset="text")
    out_path = os.path.join(DATA_DIR, "synthetic_articles.csv")
    out.to_csv(out_path, index=False)
    print(f"Wrote {len(out)} labeled rows to {out_path}")
    return out


def generate_suppliers(real_df: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    names = real_df["Supplier"].dropna().unique().tolist()
    countries = real_df["Country"].dropna().unique().tolist()
    if len(names) < n:
        names = names + [f"Supplier {i}" for i in range(n - len(names))]
    names = random.sample(names, min(n, len(names))) if len(names) >= n else names[:n]

    rows = []
    for i, name in enumerate(names[:n]):
        reliability = round(np.clip(np.random.normal(78, 12), 35, 99), 1)
        avg_delay = round(max(0, (100 - reliability) / 8 + np.random.normal(0, 1)), 1)
        lead_time = int(np.clip(7 + (100 - reliability) / 10 + np.random.normal(0, 2), 3, 45))
        disruption_count = int(np.clip((100 - reliability) / 10 + np.random.poisson(1), 0, 20))
        risk_score = round(np.clip((100 - reliability) * 0.6 + disruption_count * 2, 0, 100), 1)
        risk_level = "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 35 else "LOW"
        rows.append({
            "name": name, "location": random.choice(countries) if countries else "Unknown",
            "country": random.choice(countries) if countries else "Unknown",
            "reliability_score": reliability, "lead_time": lead_time, "average_delay": avg_delay,
            "risk_level": risk_level, "risk_score": risk_score, "disruption_count": disruption_count,
        })
    return pd.DataFrame(rows)


def generate_products(suppliers_df: pd.DataFrame, real_df: pd.DataFrame, n: int = 200) -> pd.DataFrame:
    items = real_df["Item"].dropna().unique().tolist() or CATEGORIES
    rows = []
    for i in range(n):
        supplier = suppliers_df.iloc[i % len(suppliers_df)]
        unit_cost = round(np.random.uniform(5, 500), 2)
        margin = np.random.uniform(1.2, 2.5)
        lead_time = int(supplier["lead_time"] + np.random.randint(-2, 3))
        rows.append({
            "sku": f"PROD-{1000+i}",
            "name": f"{random.choice(items)} {i}",
            "category": random.choice(CATEGORIES),
            "supplier_name": supplier["name"],
            "unit_cost": unit_cost,
            "selling_price": round(unit_cost * margin, 2),
            "lead_time": max(lead_time, 2),
            "safety_stock": 0,   # computed later from demand
            "reorder_point": 0,  # computed later
        })
    return pd.DataFrame(rows)


def generate_sales(products_df: pd.DataFrame, days: int = 365) -> pd.DataFrame:
    rows = []
    start = date.today() - timedelta(days=days)
    for _, p in products_df.iterrows():
        base_demand = np.random.uniform(2, 40)
        trend = np.random.uniform(-0.01, 0.02)
        for d in range(days):
            day = start + timedelta(days=d)
            seasonal = 1 + 0.15 * np.sin(2 * np.pi * d / 30)
            noise = np.random.normal(1, 0.25)
            qty = max(0, round(base_demand * seasonal * noise * (1 + trend * d)))
            if qty == 0:
                continue
            rows.append({
                "sku": p["sku"], "quantity": qty,
                "revenue": round(qty * p["selling_price"], 2), "sale_date": day.isoformat(),
            })
    return pd.DataFrame(rows)


def generate_purchase_orders(products_df: pd.DataFrame, suppliers_df: pd.DataFrame, n_per_product: int = 8) -> pd.DataFrame:
    rows = []
    supplier_lookup = suppliers_df.set_index("name")
    for _, p in products_df.iterrows():
        supplier = supplier_lookup.loc[p["supplier_name"]]
        for _ in range(n_per_product):
            order_date = date.today() - timedelta(days=random.randint(1, 300))
            expected = order_date + timedelta(days=int(p["lead_time"]))
            delay = np.random.poisson(max(supplier["average_delay"], 0.1))
            actual = expected + timedelta(days=int(delay)) if random.random() > 0.1 else None
            status = "DELIVERED" if actual else ("DELAYED" if random.random() > 0.5 else "PENDING")
            rows.append({
                "supplier_name": p["supplier_name"], "sku": p["sku"],
                "quantity": random.randint(50, 1000), "order_date": order_date.isoformat(),
                "expected_date": expected.isoformat(),
                "actual_date": actual.isoformat() if actual else None, "status": status,
            })
    return pd.DataFrame(rows)


def compute_inventory(products_df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, p in products_df.iterrows():
        prod_sales = sales_df[sales_df["sku"] == p["sku"]]["quantity"]
        avg_demand = prod_sales.mean() if len(prod_sales) else 5
        std_demand = prod_sales.std() if len(prod_sales) else 2
        safety_stock = round(1.65 * (std_demand or 1) * (p["lead_time"] ** 0.5), 1)
        reorder_point = round(avg_demand * p["lead_time"] + safety_stock, 1)
        current_stock = round(max(reorder_point * np.random.uniform(0.5, 2.0), 0), 1)
        reserved = round(current_stock * np.random.uniform(0, 0.15), 1)
        rows.append({
            "sku": p["sku"], "current_stock": current_stock, "reserved_stock": reserved,
            "available_stock": round(current_stock - reserved, 1),
            "reorder_point": reorder_point, "safety_stock": safety_stock,
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-db", action="store_true")
    parser.add_argument("--csv-only", action="store_true")
    parser.add_argument("--n-suppliers", type=int, default=30)
    parser.add_argument("--n-products", type=int, default=200)
    args = parser.parse_args()

    real_df = load_real_source()
    build_synthetic_articles_csv(real_df)

    suppliers_df = generate_suppliers(real_df, args.n_suppliers)
    products_df = generate_products(suppliers_df, real_df, args.n_products)
    sales_df = generate_sales(products_df)
    po_df = generate_purchase_orders(products_df, suppliers_df)
    inventory_df = compute_inventory(products_df, sales_df)

    suppliers_df.to_csv(os.path.join(DATA_DIR, "synthetic_suppliers.csv"), index=False)
    products_df.to_csv(os.path.join(DATA_DIR, "synthetic_products.csv"), index=False)
    sales_df.to_csv(os.path.join(DATA_DIR, "synthetic_sales.csv"), index=False)
    po_df.to_csv(os.path.join(DATA_DIR, "synthetic_purchase_orders.csv"), index=False)
    inventory_df.to_csv(os.path.join(DATA_DIR, "synthetic_inventory.csv"), index=False)
    print(f"Generated: {len(suppliers_df)} suppliers, {len(products_df)} products, "
          f"{len(sales_df)} sales rows, {len(po_df)} purchase orders")

    if args.csv_only:
        return

    if args.seed_db:
        from scripts.seed_db import seed_from_csvs
        seed_from_csvs()


if __name__ == "__main__":
    main()
