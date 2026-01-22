FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_VERSION=1.0.0 \
    MODEL_PATH=models/model.pkl \
    SERVICE_HOST=0.0.0.0 \
    SERVICE_PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir \
    scikit-learn==1.3.2 \
    pandas==2.1.4 \
    numpy==1.26.2 \
    fastapi==0.108.0 \
    uvicorn==0.25.0 \
    pydantic==2.5.3 \
    prometheus-client==0.19.0 \
    joblib==1.3.2 \
    python-dotenv==1.0.0

COPY src/ ./src/
COPY models/ ./models/

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8000"]
