"""
Demand forecasting: compares moving-average / exponential-smoothing
baselines against an XGBoost regressor with lag features, per section 16.
Picks the best model by MAPE on a held-out tail of the series and returns
whichever generalizes best - "do not assume the most complex model wins".
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


@dataclass
class ForecastResult:
    model_name: str
    predictions: pd.Series
    lower_bound: pd.Series
    upper_bound: pd.Series
    mae: float
    rmse: float
    mape: float


def _mape(y_true, y_pred) -> float:
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = y_true != 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _moving_average_forecast(series: pd.Series, horizon: int, window: int = 7) -> pd.Series:
    avg = series.tail(window).mean()
    idx = pd.RangeIndex(len(series), len(series) + horizon)
    return pd.Series([avg] * horizon, index=idx)


def _exp_smoothing_forecast(series: pd.Series, horizon: int, alpha: float = 0.3) -> pd.Series:
    level = series.iloc[0]
    for v in series:
        level = alpha * v + (1 - alpha) * level
    idx = pd.RangeIndex(len(series), len(series) + horizon)
    return pd.Series([level] * horizon, index=idx)


def _xgb_lag_forecast(series: pd.Series, horizon: int, n_lags: int = 7):
    import xgboost as xgb

    values = series.values.astype(float)
    X, y = [], []
    for i in range(n_lags, len(values)):
        X.append(values[i - n_lags:i])
        y.append(values[i])
    if len(X) < 10:
        return None  # not enough history

    X, y = np.array(X), np.array(y)
    model = xgb.XGBRegressor(n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X, y)

    history = list(values[-n_lags:])
    preds = []
    for _ in range(horizon):
        x = np.array(history[-n_lags:]).reshape(1, -1)
        p = float(model.predict(x)[0])
        preds.append(max(p, 0))
        history.append(p)
    idx = pd.RangeIndex(len(series), len(series) + horizon)
    return pd.Series(preds, index=idx)


def forecast_demand(daily_sales: pd.Series, horizon: int = 14) -> ForecastResult:
    """daily_sales: pandas Series indexed by date, values = quantity sold."""
    series = daily_sales.sort_index().asfreq("D").fillna(0)

    # hold out last `eval_len` points to compare model accuracy
    eval_len = min(max(int(len(series) * 0.15), 3), 30)
    if len(series) <= eval_len + 10:
        eval_len = max(1, len(series) // 5)

    train, test = series.iloc[:-eval_len], series.iloc[-eval_len:]

    candidates = {}
    ma_pred = _moving_average_forecast(train, eval_len)
    candidates["moving_average"] = ma_pred

    es_pred = _exp_smoothing_forecast(train, eval_len)
    candidates["exponential_smoothing"] = es_pred

    xgb_pred = _xgb_lag_forecast(train, eval_len)
    if xgb_pred is not None:
        candidates["xgboost_lag"] = xgb_pred

    best_name, best_mape = None, float("inf")
    scores = {}
    for name, pred in candidates.items():
        mape = _mape(test.values, pred.values)
        scores[name] = mape
        if mape < best_mape:
            best_name, best_mape = name, mape

    # refit the winning strategy on the FULL series for the real forward forecast
    if best_name == "moving_average":
        final_pred = _moving_average_forecast(series, horizon)
    elif best_name == "exponential_smoothing":
        final_pred = _exp_smoothing_forecast(series, horizon)
    else:
        xgb_final = _xgb_lag_forecast(series, horizon)
        if xgb_final is not None:
            final_pred, best_name = xgb_final, "xgboost_lag"
        else:
            final_pred, best_name = _moving_average_forecast(series, horizon), "moving_average"

    residual_std = float(np.std(test.values - candidates[best_name].values)) if len(test) else float(series.std())
    lower = final_pred - 1.96 * residual_std
    upper = final_pred + 1.96 * residual_std

    mae = mean_absolute_error(test.values, candidates[best_name].values) if len(test) else 0.0
    rmse = mean_squared_error(test.values, candidates[best_name].values) ** 0.5 if len(test) else 0.0

    return ForecastResult(
        model_name=best_name,
        predictions=final_pred.clip(lower=0),
        lower_bound=lower.clip(lower=0),
        upper_bound=upper,
        mae=round(float(mae), 2),
        rmse=round(float(rmse), 2),
        mape=round(best_mape, 2) if best_mape != float("inf") else 0.0,
    )
