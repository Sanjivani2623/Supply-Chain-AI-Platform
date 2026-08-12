"""
Wraps app.ml.forecasting.model to pull sales history from the DB, run the
model comparison, and persist forecast rows (section 16).
"""
import pandas as pd
from sqlalchemy.orm import Session

from app.models.sales import Sale
from app.models.forecast import Forecast
from app.ml.forecasting.model import forecast_demand


def get_sales_series(db: Session, product_id: str) -> pd.Series:
    rows = db.query(Sale.sale_date, Sale.quantity).filter(Sale.product_id == product_id).order_by(Sale.sale_date).all()
    if not rows:
        return pd.Series(dtype=float)
    df = pd.DataFrame(rows, columns=["date", "quantity"])
    df["date"] = pd.to_datetime(df["date"])
    return df.groupby("date")["quantity"].sum()


def generate_forecast(db: Session, product_id: str, horizon: int = 14, persist: bool = True) -> dict:
    series = get_sales_series(db, product_id)
    if series.empty or len(series) < 14:
        return {"error": "insufficient_history", "product_id": product_id}

    result = forecast_demand(series, horizon=horizon)

    if persist:
        db.query(Forecast).filter(Forecast.product_id == product_id).delete()
        start_date = series.index.max() + pd.Timedelta(days=1)
        for i, (pred, lo, hi) in enumerate(zip(result.predictions, result.lower_bound, result.upper_bound)):
            db.add(Forecast(
                product_id=product_id,
                forecast_date=(start_date + pd.Timedelta(days=i)).date(),
                predicted_demand=float(pred),
                lower_bound=float(lo),
                upper_bound=float(hi),
                model_version=result.model_name,
            ))
        db.commit()

    return {
        "product_id": product_id,
        "model": result.model_name,
        "mae": result.mae,
        "rmse": result.rmse,
        "mape": result.mape,
        "horizon": horizon,
        "predicted_demand_total": round(float(result.predictions.sum()), 1),
    }
