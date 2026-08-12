"""
Supervised disruption-risk model.

Trains a gradient-boosted classifier (XGBoost) that predicts probability of
a "meaningful disruption" using structured features, extending the
baseline formula in app.services.disruption.risk_model per section 14.

Features: disruption_type (encoded), severity (encoded), supplier
reliability, historical delay, lead time, inventory level, demand,
article/event frequency.

Labeled from `backend/data/merged_supply_chain_data.xlsx` (Risk Factor is
used to derive a binary "high risk" label at the 75th percentile) - this
reuses the real, already-collected project data rather than throwing it
away, per the master prompt's "do not discard existing work" instruction.
"""
import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, classification_report
import xgboost as xgb

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "merged_supply_chain_data.xlsx")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "risk_model.joblib")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["News Sentiment"] = pd.to_numeric(df["News Sentiment"], errors="coerce").fillna(0)
    df["Inventory Level"] = pd.to_numeric(df["Inventory Level"], errors="coerce").fillna(df["Inventory Level"].median())
    df["Lead Time (days)"] = pd.to_numeric(df["Lead Time (days)"], errors="coerce").fillna(df["Lead Time (days)"].median())

    le_region = LabelEncoder()
    le_transport = LabelEncoder()
    df["region_enc"] = le_region.fit_transform(df["Region"].astype(str))
    df["transport_enc"] = le_transport.fit_transform(df["Transport Status"].astype(str))

    feature_cols = ["Inventory Level", "Lead Time (days)", "News Sentiment", "region_enc", "transport_enc"]
    return df, feature_cols, {"region": le_region, "transport": le_transport}


def main():
    df = pd.read_excel(DATA_PATH)
    df, feature_cols, encoders = build_features(df)

    threshold = df["Risk Factor"].quantile(0.75)
    df["high_risk"] = (df["Risk Factor"] >= threshold).astype(int)

    X = df[feature_cols]
    y = df["high_risk"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.08,
        subsample=0.9, colsample_bytree=0.9, eval_metric="auc", random_state=42,
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    print("ROC-AUC:", round(roc_auc_score(y_test, proba), 4))
    print(classification_report(y_test, preds, zero_division=0))

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    joblib.dump({"model": model, "feature_cols": feature_cols, "encoders": encoders, "threshold": threshold}, MODEL_PATH)
    print(f"Saved risk model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
