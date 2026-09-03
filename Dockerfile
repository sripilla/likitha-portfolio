FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the application
COPY backend/ backend/
COPY frontend/ frontend/

# Non-root user for security
RUN useradd --create-home appuser
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
