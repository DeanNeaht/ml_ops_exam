import os
import yaml
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from datetime import datetime


def load_params():
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)


def prepare_data():
    params = load_params()["prepare"]
    
    iris = load_iris()
    df = pd.DataFrame(
        data=iris.data,
        columns=["sepal_length", "sepal_width", "petal_length", "petal_width"]
    )
    df["target"] = iris.target
    df["iris_id"] = range(len(df))
    df["event_timestamp"] = datetime.now()
    
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/raw", exist_ok=True)
    
    df.to_csv("data/raw/iris.csv", index=False)
    
    train_df, test_df = train_test_split(
        df,
        test_size=params["test_size"],
        random_state=params["random_state"],
        stratify=df["target"]
    )
    
    train_df.to_csv("data/processed/train.csv", index=False)
    test_df.to_csv("data/processed/test.csv", index=False)
    
    features_df = df[["iris_id", "sepal_length", "sepal_width", 
                      "petal_length", "petal_width", "event_timestamp"]]
    features_df.to_parquet("data/processed/features.parquet", index=False)
    
    print(f"Data preparation complete!")
    print(f"  - Raw data: data/raw/iris.csv ({len(df)} samples)")
    print(f"  - Train set: data/processed/train.csv ({len(train_df)} samples)")
    print(f"  - Test set: data/processed/test.csv ({len(test_df)} samples)")
    
    return train_df, test_df


if __name__ == "__main__":
    prepare_data()
