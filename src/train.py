import os
import yaml
import json
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from dotenv import load_dotenv

load_dotenv()


def load_params():
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)


def load_training_data():
    train_df = pd.read_csv("data/processed/train.csv")
    
    try:
        from feast import FeatureStore
        feast_repo_path = os.getenv("FEAST_REPO_PATH", "./feast")
        
        if os.path.exists(os.path.join(feast_repo_path, "feature_store.yaml")):
            store = FeatureStore(repo_path=feast_repo_path)
            entity_df = train_df[["iris_id", "event_timestamp"]].copy()
            
            features = store.get_historical_features(
                entity_df=entity_df,
                features=[
                    "iris_features:sepal_length",
                    "iris_features:sepal_width", 
                    "iris_features:petal_length",
                    "iris_features:petal_width"
                ]
            ).to_df()
            
            train_df = features.merge(train_df[["iris_id", "target"]], on="iris_id")
            print("Loaded features from Feast Feature Store")
    except Exception as e:
        print(f"Feast not available, using local data: {e}")
    
    return train_df


def train_model():
    params = load_params()["train"]
    
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "iris-classification")
    
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment(experiment_name)
    
    train_df = load_training_data()
    
    feature_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    X_train = train_df[feature_cols]
    y_train = train_df["target"]
    
    with mlflow.start_run() as run:
        print(f"MLflow Run ID: {run.info.run_id}")
        
        mlflow.log_params({
            "n_estimators": params["n_estimators"],
            "max_depth": params["max_depth"],
            "random_state": params["random_state"],
            "model_type": "RandomForestClassifier"
        })
        
        model = RandomForestClassifier(
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            random_state=params["random_state"]
        )
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_train)
        train_accuracy = accuracy_score(y_train, y_pred)
        train_f1 = f1_score(y_train, y_pred, average="weighted")
        
        mlflow.log_metrics({"train_accuracy": train_accuracy, "train_f1": train_f1})
        
        feature_importance = dict(zip(feature_cols, model.feature_importances_))
        mlflow.log_dict(feature_importance, "feature_importance.json")
        
        os.makedirs("models", exist_ok=True)
        model_path = os.getenv("MODEL_PATH", "models/model.pkl")
        joblib.dump(model, model_path)
        
        mlflow.sklearn.log_model(model, "model", registered_model_name="iris-classifier")
        
        run_info = {
            "run_id": run.info.run_id,
            "experiment_id": run.info.experiment_id,
            "train_accuracy": train_accuracy,
            "train_f1": train_f1
        }
        
        with open("models/run_info.json", "w") as f:
            json.dump(run_info, f, indent=2)
        
        print(f"\nTraining complete!")
        print(f"  - Train Accuracy: {train_accuracy:.4f}")
        print(f"  - Train F1 Score: {train_f1:.4f}")
        print(f"  - Model saved to: {model_path}")
        print(f"  - MLflow Run ID: {run.info.run_id}")
        
        return model, run_info


if __name__ == "__main__":
    train_model()
