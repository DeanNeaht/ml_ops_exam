import os
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
import json
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime as dt

default_args = {
    "owner": "mlops",
    "depends_on_past": False,
    "email": ["mlops@example.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

PROJECT_DIR = os.getenv("PROJECT_DIR", "/Users/nick/PycharmProjects/ml_ops_exam")


def extract_data(**context):
    import sys
    sys.path.insert(0, PROJECT_DIR)
    
    logging.info("Starting data extraction...")
    from src.prepare import prepare_data
    train_df, test_df = prepare_data()
    
    logging.info(f"Extracted {len(train_df)} train, {len(test_df)} test samples")
    context["ti"].xcom_push(key="train_samples", value=len(train_df))
    return {"status": "success", "train_samples": len(train_df)}


def train_model(**context):
    import sys
    sys.path.insert(0, PROJECT_DIR)
    
    logging.info("Starting model training...")
    from src.train import train_model as run_training
    model, run_info = run_training()
    
    logging.info(f"Training complete. Run ID: {run_info['run_id']}, Accuracy: {run_info['train_accuracy']:.4f}")
    context["ti"].xcom_push(key="mlflow_run_id", value=run_info["run_id"])
    context["ti"].xcom_push(key="train_accuracy", value=run_info["train_accuracy"])
    return run_info


def evaluate_model(**context):
    import sys
    sys.path.insert(0, PROJECT_DIR)
    
    logging.info("Starting evaluation...")
    from src.evaluate import evaluate_model as run_evaluation
    metrics = run_evaluation()
    
    logging.info(f"Test Accuracy: {metrics['accuracy']:.4f}, Threshold passed: {metrics['threshold_passed']}")
    context["ti"].xcom_push(key="test_accuracy", value=metrics["accuracy"])
    context["ti"].xcom_push(key="threshold_passed", value=metrics["threshold_passed"])
    
    if not metrics["threshold_passed"]:
        logging.warning("Model did not meet accuracy threshold!")
    return metrics


def deploy_model(**context):
    ti = context["ti"]
    run_id = ti.xcom_pull(task_ids="train_model", key="mlflow_run_id")
    test_accuracy = ti.xcom_pull(task_ids="evaluate", key="test_accuracy")
    threshold_passed = ti.xcom_pull(task_ids="evaluate", key="threshold_passed")
    
    if not threshold_passed:
        logging.warning("Skipping deployment: threshold not met")
        return {"status": "skipped", "reason": "threshold_not_met"}
    
    deployment_info = {
        "status": "deployed",
        "run_id": run_id,
        "accuracy": test_accuracy,
        "deployed_at": datetime.now().isoformat(),
        "version": os.getenv("MODEL_VERSION", "1.0.0"),
    }
    
    logging.info(f"Deployment complete: {json.dumps(deployment_info)}")
    context["ti"].xcom_push(key="deployment_info", value=deployment_info)
    return deployment_info


def send_notification(**context):
    ti = context["ti"]
    train_samples = ti.xcom_pull(task_ids="extract_data", key="train_samples")
    run_id = ti.xcom_pull(task_ids="train_model", key="mlflow_run_id")
    train_accuracy = ti.xcom_pull(task_ids="train_model", key="train_accuracy")
    test_accuracy = ti.xcom_pull(task_ids="evaluate", key="test_accuracy")
    deployment_info = ti.xcom_pull(task_ids="deploy", key="deployment_info")
    
    message = f"""
=== ML Pipeline Report ===
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Training Samples: {train_samples}
MLflow Run: {run_id}
Train Accuracy: {train_accuracy:.4f if train_accuracy else 'N/A'}
Test Accuracy: {test_accuracy:.4f if test_accuracy else 'N/A'}
Deploy Status: {deployment_info.get('status', 'N/A') if deployment_info else 'N/A'}
==========================
    """
    logging.info(message)
    return {"status": "notified"}


with DAG(
    dag_id="ml_retrain_pipeline",
    default_args=default_args,
    description="ML model retraining pipeline",
    schedule="@weekly",
    start_date=dt(2024, 1, 1),
    catchup=False,
    tags=["mlops", "retraining"],
) as dag:
    
    extract_task = PythonOperator(task_id="extract_data", python_callable=extract_data)
    train_task = PythonOperator(task_id="train_model", python_callable=train_model)
    evaluate_task = PythonOperator(task_id="evaluate", python_callable=evaluate_model)
    deploy_task = PythonOperator(task_id="deploy", python_callable=deploy_model)
    notify_task = PythonOperator(task_id="notify", python_callable=send_notification)
    
    extract_task >> train_task >> evaluate_task >> deploy_task >> notify_task
