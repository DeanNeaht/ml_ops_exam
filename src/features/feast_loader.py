import os
import subprocess
import pandas as pd
from datetime import datetime
from typing import List, Optional


def get_feast_store():
    from feast import FeatureStore
    return FeatureStore(repo_path=os.getenv("FEAST_REPO_PATH", "./feast"))


def get_historical_features(entity_df: pd.DataFrame, feature_refs: Optional[List[str]] = None) -> pd.DataFrame:
    store = get_feast_store()
    
    if feature_refs is None:
        feature_refs = [
            "iris_features:sepal_length",
            "iris_features:sepal_width",
            "iris_features:petal_length",
            "iris_features:petal_width"
        ]
    
    if "event_timestamp" not in entity_df.columns:
        entity_df["event_timestamp"] = datetime.now()
    
    return store.get_historical_features(entity_df=entity_df, features=feature_refs).to_df()


def get_online_features(entity_ids: List[int]) -> pd.DataFrame:
    store = get_feast_store()
    entity_rows = [{"iris_id": eid} for eid in entity_ids]
    
    return store.get_online_features(
        features=[
            "iris_features:sepal_length",
            "iris_features:sepal_width",
            "iris_features:petal_length",
            "iris_features:petal_width"
        ],
        entity_rows=entity_rows
    ).to_df()


def apply_feast_features():
    feast_repo_path = os.getenv("FEAST_REPO_PATH", "./feast")
    result = subprocess.run(["feast", "apply"], cwd=feast_repo_path, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Feast apply failed: {result.stderr}")
    
    print("Feast features applied")
    return result.stdout


def materialize_features(start_date: datetime, end_date: datetime):
    store = get_feast_store()
    store.materialize(start_date=start_date, end_date=end_date)
    print(f"Features materialized: {start_date} to {end_date}")
