"""Scikit-learn Intent Classifier for TrustDesk.
Trains a TF-IDF + Logistic Regression pipeline on synthetic loan queries.
Computes N_test dynamically from the test split, reports Macro F1,
provides per-class precision/recall and confusion matrix, explicitly designates the dataset
as synthetic, and compares against two independent keyword/regex baselines.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from backend.agent.graph import detect_intent_advanced_regex, detect_intent_rule_based
from backend.ml.dataset import SYNTHETIC_INTENT_DATASET


class IntentClassifier:
    """TF-IDF and Logistic Regression classifier for synthetic loan query intent."""

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self.pipeline: Optional[Pipeline] = None
        self.evaluation_results: Optional[Dict[str, Any]] = None

    def train_and_evaluate(self, test_size: float = 0.25) -> Dict[str, Any]:
        """Trains the pipeline on synthetic data and dynamically computes test metrics."""
        X: List[str] = [item["text"] for item in SYNTHETIC_INTENT_DATASET]
        y: List[str] = [item["intent"] for item in SYNTHETIC_INTENT_DATASET]

        # Dynamic train/test split with stratification
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=y,
        )

        # Dynamic calculation of N_test
        n_test = len(y_test)
        classes_sorted = sorted(list(set(y)))

        self.pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
                ("clf", LogisticRegression(max_iter=300, random_state=self.random_state)),
            ]
        )
        self.pipeline.fit(X_train, y_train)

        # ML Predictions and Macro F1
        y_pred_ml = self.pipeline.predict(X_test)
        macro_f1_ml = float(f1_score(y_test, y_pred_ml, average="macro"))

        # Per-class precision, recall, and F1
        report_dict = classification_report(y_test, y_pred_ml, output_dict=True, zero_division=0)
        per_class_metrics: Dict[str, Dict[str, float]] = {}
        for cls_name in classes_sorted:
            if cls_name in report_dict:
                per_class_metrics[cls_name] = {
                    "precision": round(report_dict[cls_name]["precision"], 4),
                    "recall": round(report_dict[cls_name]["recall"], 4),
                    "f1_score": round(report_dict[cls_name]["f1-score"], 4),
                    "support": int(report_dict[cls_name]["support"]),
                }

        # Confusion Matrix
        conf_matrix = confusion_matrix(y_test, y_pred_ml, labels=classes_sorted).tolist()

        # Baseline 1: Simple Keyword Heuristic
        y_pred_kw_simple = [detect_intent_rule_based(query) for query in X_test]
        macro_f1_kw_simple = float(f1_score(y_test, y_pred_kw_simple, average="macro"))

        # Baseline 2: Stronger Enhanced Regex / Stemming Heuristic
        y_pred_kw_enhanced = [detect_intent_advanced_regex(query) for query in X_test]
        macro_f1_kw_enhanced = float(f1_score(y_test, y_pred_kw_enhanced, average="macro"))

        self.evaluation_results = {
            "dataset_designation": "synthetic",
            "total_samples": len(X),
            "n_train": len(X_train),
            "n_test": n_test,
            "classes": classes_sorted,
            "model_architecture": "TfidfVectorizer + LogisticRegression",
            "macro_f1_ml": round(macro_f1_ml, 4),
            "keyword_baseline_simple_macro_f1": round(macro_f1_kw_simple, 4),
            "keyword_baseline_enhanced_macro_f1": round(macro_f1_kw_enhanced, 4),
            "per_class_metrics": per_class_metrics,
            "confusion_matrix": {
                "labels": classes_sorted,
                "matrix": conf_matrix,
            },
            "evaluation_label": "synthetic ML evaluation",
        }

        return self.evaluation_results

    def predict(self, query: str) -> Tuple[str, float]:
        """Predicts intent and returns (intent_name, confidence)."""
        if self.pipeline is None:
            self.train_and_evaluate()
            assert self.pipeline is not None

        probs = self.pipeline.predict_proba([query])[0]
        classes = self.pipeline.classes_
        top_idx = int(np.argmax(probs))
        return str(classes[top_idx]), float(probs[top_idx])


# Global singleton intent classifier
intent_classifier = IntentClassifier()
