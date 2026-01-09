FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create data directories (but don't copy large data files)
RUN mkdir -p data/local_storage data/pipeline data/uploads data/raw

# Copy only the scenarios file (small and needed)
COPY data/claim_scenarios.json ./data/

# Expose port
EXPOSE 8080

# Start application (Native WebSocket support)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
