"""
TF-IDF + Logistic Regression disruption classifier.

This is the "ML classifier" tier described in section 13 (as opposed to the
keyword baseline and the optional LLM classifier). Trained via train.py and
persisted to disk; loaded lazily by app.services.disruption.classifier.
"""
import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "disruption_clf.joblib")


class DisruptionClassifierModel:
    def __init__(self, pipeline, label_encoder):
        self.pipeline = pipeline
        self.label_encoder = label_encoder

    def predict_one(self, text: str) -> tuple[str, float]:
        proba = self.pipeline.predict_proba([text])[0]
        idx = proba.argmax()
        label = self.label_encoder.inverse_transform([idx])[0]
        return label, float(proba[idx])

    def save(self, path: str = MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"pipeline": self.pipeline, "label_encoder": self.label_encoder}, path)

    @classmethod
    def load(cls, path: str = MODEL_PATH) -> "DisruptionClassifierModel":
        obj = joblib.load(path)
        return cls(obj["pipeline"], obj["label_encoder"])


def load_model() -> DisruptionClassifierModel:
    return DisruptionClassifierModel.load()
