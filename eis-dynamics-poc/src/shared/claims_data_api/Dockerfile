FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY data/ ./data/

# Expose port
EXPOSE 8080

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
