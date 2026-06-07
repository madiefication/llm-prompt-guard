"""
ML-Based Classifier: TF-IDF + Logistic Regression trained on synthetic dataset.
Loads a pre-trained model from disk on startup.
"""

import os
import csv
import sys
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")
MODEL_PATH = os.path.join(MODELS_DIR, "lr_model.pkl")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "training_data.csv")


def _load_dataset():
    texts, labels = [], []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            labels.append(int(row["label"]))
    return texts, labels


def train_and_save():
    """Train TF-IDF + LR model and persist to disk. Called during setup."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    texts, labels = _load_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=10000,
        sublinear_tf=True,
        analyzer="word",
        token_pattern=r"(?u)\b\w+\b",
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)
    print("=== ML Classifier Metrics ===")
    print(f"  Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"  Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"  Recall:    {recall_score(y_test, y_pred):.4f}")
    print(f"  F1 Score:  {f1_score(y_test, y_pred):.4f}")

    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved -> {MODEL_PATH}")
    print(f"Vectorizer saved -> {VECTORIZER_PATH}")

    return vectorizer, model


class MLClassifier:
    """Lazy-loaded TF-IDF + Logistic Regression classifier."""

    def __init__(self):
        self._vectorizer = None
        self._model = None

    def _ensure_loaded(self):
        if self._model is None:
            if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
                raise RuntimeError(
                    "Model files not found. Run: python -m engine.ml_classifier"
                )
            self._vectorizer = joblib.load(VECTORIZER_PATH)
            self._model = joblib.load(MODEL_PATH)

    def predict_proba(self, text: str) -> float:
        """Return probability that text is adversarial (class=1)."""
        self._ensure_loaded()
        vec = self._vectorizer.transform([text])
        proba = self._model.predict_proba(vec)[0]
        return float(proba[1])

    def top_tokens(self, text: str, n: int = 5) -> list[dict]:
        """Return top-N tokens contributing most to the adversarial score."""
        self._ensure_loaded()
        vec = self._vectorizer.transform([text])
        feature_names = self._vectorizer.get_feature_names_out()
        # adversarial class coefficients
        coef = self._model.coef_[0]
        nonzero_indices = vec.nonzero()[1]
        token_scores = [
            {"token": feature_names[i], "weight": float(coef[i] * vec[0, i])}
            for i in nonzero_indices
        ]
        token_scores.sort(key=lambda x: x["weight"], reverse=True)
        return token_scores[:n]


# Singleton instance for import use
ml_classifier = MLClassifier()


if __name__ == "__main__":
    # Running directly trains and saves the model
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from data.generate_dataset import main as gen_data

    print("Generating dataset...")
    gen_data()
    print("\nTraining model...")
    train_and_save()
    print("\nDone.")
