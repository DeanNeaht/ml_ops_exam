import os
import time
import joblib
import numpy as np
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Iris Classification Service",
    version=os.getenv("MODEL_VERSION", "1.0.0")
)

REQUEST_COUNT = Counter("ml_requests_total", "Total requests", ["endpoint", "method", "status"])
REQUEST_LATENCY = Histogram("ml_request_latency_seconds", "Request latency", ["endpoint"],
                            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0])
PREDICTION_COUNT = Counter("ml_predictions_total", "Predictions by class", ["predicted_class"])
MODEL_INFO = Gauge("ml_model_info", "Model info", ["version", "model_type"])

model = None
model_loaded_at = None
IRIS_CLASSES = ["setosa", "versicolor", "virginica"]


class PredictRequest(BaseModel):
    features: List[List[float]] = Field(..., example=[[5.1, 3.5, 1.4, 0.2]])


class PredictResponse(BaseModel):
    predictions: List[int]
    class_names: List[str]
    probabilities: Optional[List[List[float]]] = None


class HealthResponse(BaseModel):
    status: str
    model_version: str
    model_loaded: bool
    model_loaded_at: Optional[str]
    timestamp: str


def load_model():
    global model, model_loaded_at
    model_path = os.getenv("MODEL_PATH", "models/model.pkl")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    model = joblib.load(model_path)
    model_loaded_at = datetime.now().isoformat()
    MODEL_INFO.labels(version=os.getenv("MODEL_VERSION", "1.0.0"), model_type="RandomForestClassifier").set(1)
    return model


@app.on_event("startup")
async def startup_event():
    try:
        load_model()
        print(f"Model loaded at {model_loaded_at}")
    except FileNotFoundError as e:
        print(f"Warning: {e}")


@app.get("/health", response_model=HealthResponse)
async def health():
    start = time.time()
    try:
        response = HealthResponse(
            status="healthy" if model else "degraded",
            model_version=os.getenv("MODEL_VERSION", "1.0.0"),
            model_loaded=model is not None,
            model_loaded_at=model_loaded_at,
            timestamp=datetime.now().isoformat()
        )
        REQUEST_COUNT.labels(endpoint="/health", method="GET", status="200").inc()
        REQUEST_LATENCY.labels(endpoint="/health").observe(time.time() - start)
        return response
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/health", method="GET", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    start = time.time()
    
    if model is None:
        REQUEST_COUNT.labels(endpoint="/predict", method="POST", status="503").inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        features = np.array(request.features)
        if features.shape[1] != 4:
            raise ValueError(f"Expected 4 features, got {features.shape[1]}")
        
        predictions = model.predict(features).tolist()
        probabilities = model.predict_proba(features).tolist()
        class_names = [IRIS_CLASSES[p] for p in predictions]
        
        for pred in predictions:
            PREDICTION_COUNT.labels(predicted_class=IRIS_CLASSES[pred]).inc()
        
        REQUEST_COUNT.labels(endpoint="/predict", method="POST", status="200").inc()
        REQUEST_LATENCY.labels(endpoint="/predict").observe(time.time() - start)
        
        return PredictResponse(predictions=predictions, class_names=class_names, probabilities=probabilities)
    except ValueError as e:
        REQUEST_COUNT.labels(endpoint="/predict", method="POST", status="400").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/predict", method="POST", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    return {
        "service": "Iris Classification Service",
        "version": os.getenv("MODEL_VERSION", "1.0.0"),
        "endpoints": ["/health", "/predict", "/metrics", "/docs"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("SERVICE_HOST", "0.0.0.0"), 
                port=int(os.getenv("SERVICE_PORT", "8000")))
