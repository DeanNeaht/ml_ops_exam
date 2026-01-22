import os
import json
import yaml
import joblib
import pandas as pd
import mlflow
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score,
    recall_score, classification_report, confusion_matrix
)
from dotenv import load_dotenv

load_dotenv()


def load_params():
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)


def evaluate_model():
    params = load_params()["evaluate"]
    
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
    mlflow.set_tracking_uri(mlflow_uri)
    
    model_path = os.getenv("MODEL_PATH", "models/model.pkl")
    model = joblib.load(model_path)
    
    test_df = pd.read_csv("data/processed/test.csv")
    
    feature_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    X_test = test_df[feature_cols]
    y_test = test_df["target"]
    
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    precision = precision_score(y_test, y_pred, average="weighted")
    recall = recall_score(y_test, y_pred, average="weighted")
    
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)
    
    run_info_path = "models/run_info.json"
    run_id = None
    if os.path.exists(run_info_path):
        with open(run_info_path, "r") as f:
            run_info = json.load(f)
        run_id = run_info.get("run_id")
    
    if run_id:
        with mlflow.start_run(run_id=run_id):
            mlflow.log_metrics({
                "test_accuracy": accuracy,
                "test_f1": f1,
                "test_precision": precision,
                "test_recall": recall
            })
            mlflow.log_dict(report, "classification_report.json")
            mlflow.log_dict({"confusion_matrix": cm.tolist()}, "confusion_matrix.json")
    
    metrics = {
        "accuracy": accuracy,
        "f1_score": f1,
        "precision": precision,
        "recall": recall,
        "threshold_passed": accuracy >= params["threshold"]
    }
    
    with open("metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\nEvaluation Results:")
    print(f"  - Test Accuracy: {accuracy:.4f}")
    print(f"  - Test F1 Score: {f1:.4f}")
    print(f"  - Test Precision: {precision:.4f}")
    print(f"  - Test Recall: {recall:.4f}")
    print(f"\nThreshold: {params['threshold']}")
    print(f"Threshold Passed: {'Yes' if metrics['threshold_passed'] else 'No'}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    return metrics


if __name__ == "__main__":
    evaluate_model()
