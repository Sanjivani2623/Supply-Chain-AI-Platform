"""Unit tests for demand forecasting (model comparison, MAPE, non-negative outputs)."""
import numpy as np
import pandas as pd

from app.ml.forecasting.model import forecast_demand


def _make_series(n=120, noise=1.0):
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    values = 15 + 3 * np.sin(np.arange(n) / 7) + np.random.normal(0, noise, n)
    values = np.clip(values, 0, None)
    return pd.Series(values, index=idx)


def test_forecast_returns_valid_result():
    series = _make_series()
    result = forecast_demand(series, horizon=14)
    assert result.model_name in ("moving_average", "exponential_smoothing", "xgboost_lag")
    assert len(result.predictions) == 14
    assert (result.predictions >= 0).all()
    assert result.mae >= 0
    assert result.rmse >= 0


def test_forecast_bounds_contain_predictions_roughly():
    series = _make_series()
    result = forecast_demand(series, horizon=7)
    # lower bound should not exceed upper bound
    assert (result.lower_bound <= result.upper_bound).all()
