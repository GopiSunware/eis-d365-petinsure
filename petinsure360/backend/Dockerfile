FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create data directories
RUN mkdir -p data/local_storage data/pipeline data/uploads

# Copy synthetic demo data (customers, pets, policies, claims)
COPY data/raw/ ./data/raw/

# Copy scenarios file
COPY data/claim_scenarios.json ./data/

# Expose port
EXPOSE 8080

# Start application (Native WebSocket support)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
