"""
Loads the CSVs produced by generate_synthetic_data.py into PostgreSQL via
SQLAlchemy models, wiring up supplier -> product -> inventory/sales/PO
foreign keys correctly. Also seeds a default admin user.

Usage:
    python scripts/seed_db.py
"""
import os
import sys
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.user import User
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.sales import Sale
from app.models.purchase_order import PurchaseOrder
from app.services.disruption.demo_seed import seed_demo_disruptions

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _parse_date(value):
    """Convert an ISO date string (or NaN) to a Python date object.
    SQLite's DBAPI, unlike psycopg2, does not auto-coerce date strings, so
    this is required for both engines to behave identically."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    return value


def seed_from_csvs():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "admin@supplychain-ai.example.com").first():
            db.add(User(name="Admin", email="admin@supplychain-ai.example.com",
                         password_hash=hash_password("Admin123!"), role="admin"))
            db.commit()
            print("Seeded default admin: admin@supplychain-ai.example.com / Admin123!")

        suppliers_df = pd.read_csv(os.path.join(DATA_DIR, "synthetic_suppliers.csv"))
        name_to_id = {}
        for _, r in suppliers_df.iterrows():
            existing = db.query(Supplier).filter(Supplier.name == r["name"]).first()
            if existing:
                name_to_id[r["name"]] = existing.id
                continue
            s = Supplier(
                name=r["name"], location=r["location"], country=r["country"],
                reliability_score=r["reliability_score"], lead_time=int(r["lead_time"]),
                average_delay=r["average_delay"], risk_level=r["risk_level"],
                risk_score=r["risk_score"], disruption_count=int(r["disruption_count"]),
            )
            db.add(s)
            db.flush()
            name_to_id[r["name"]] = s.id
        db.commit()

        products_df = pd.read_csv(os.path.join(DATA_DIR, "synthetic_products.csv"))
        sku_to_id = {}
        for _, r in products_df.iterrows():
            if db.query(Product).filter(Product.sku == r["sku"]).first():
                continue
            p = Product(
                sku=r["sku"], name=r["name"], category=r["category"],
                supplier_id=name_to_id.get(r["supplier_name"]),
                unit_cost=r["unit_cost"], selling_price=r["selling_price"],
                lead_time=int(r["lead_time"]), safety_stock=0, reorder_point=0,
            )
            db.add(p)
            db.flush()
            sku_to_id[r["sku"]] = p.id
        db.commit()

        # refresh sku_to_id in case some already existed
        for p in db.query(Product).all():
            sku_to_id[p.sku] = p.id

        inv_df = pd.read_csv(os.path.join(DATA_DIR, "synthetic_inventory.csv"))
        db.query(Inventory).delete()
        for _, r in inv_df.iterrows():
            pid = sku_to_id.get(r["sku"])
            if not pid:
                continue
            db.add(Inventory(
                product_id=pid, current_stock=r["current_stock"], reserved_stock=r["reserved_stock"],
                available_stock=r["available_stock"], reorder_point=r["reorder_point"],
                safety_stock=r["safety_stock"], last_updated=datetime.utcnow(),
            ))
        db.commit()

        sales_df = pd.read_csv(os.path.join(DATA_DIR, "synthetic_sales.csv"))
        db.query(Sale).delete()
        db.commit()
        batch = []
        for _, r in sales_df.iterrows():
            pid = sku_to_id.get(r["sku"])
            if not pid:
                continue
            batch.append(Sale(product_id=pid, quantity=r["quantity"], revenue=r["revenue"], sale_date=_parse_date(r["sale_date"])))
            if len(batch) >= 2000:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
        if batch:
            db.bulk_save_objects(batch)
            db.commit()

        po_df = pd.read_csv(os.path.join(DATA_DIR, "synthetic_purchase_orders.csv"))
        db.query(PurchaseOrder).delete()
        db.commit()
        batch = []
        for _, r in po_df.iterrows():
            pid = sku_to_id.get(r["sku"])
            sid = name_to_id.get(r["supplier_name"])
            if not pid or not sid:
                continue
            batch.append(PurchaseOrder(
                supplier_id=sid, product_id=pid, quantity=r["quantity"],
                order_date=_parse_date(r["order_date"]), expected_date=_parse_date(r["expected_date"]),
                actual_date=_parse_date(r["actual_date"]) if pd.notna(r["actual_date"]) else None,
                status=r["status"],
            ))
            if len(batch) >= 2000:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
        if batch:
            db.bulk_save_objects(batch)
            db.commit()

        print(f"Seeded {len(suppliers_df)} suppliers, {len(products_df)} products, "
              f"{len(inv_df)} inventory rows, {len(sales_df)} sales, {len(po_df)} purchase orders")

        demo_result = seed_demo_disruptions(db)
        print(f"Seeded {demo_result['created']} demo disruption events "
              f"(so the dashboard/disruptions page have data without needing "
              f"EVENT_REGISTRY_API_KEY)")
    finally:
        db.close()


if __name__ == "__main__":
    seed_from_csvs()
