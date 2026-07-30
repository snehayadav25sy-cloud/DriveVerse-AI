FROM python:3.10-slim

WORKDIR /app

# The worker needs backend modules to access models and DB
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY worker/ /app/worker/

WORKDIR /app/worker
CMD ["python", "main.py"]
