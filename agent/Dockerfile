# DentalFlow Agent - Docker Image
# Runs the Flask HTTP API that UiPath Maestro calls via HTTP Activity

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent source
COPY dental_flow_agent.py .
COPY run_agent_api.py .

# Default env (overridden by docker-compose or Maestro)
ENV EHR_BASE_URL=http://ehr-api:3001
ENV AGENT_API_PORT=8080
ENV FLASK_DEBUG=false

# Expose Flask port
EXPOSE 8080

# Health check - Maestro polls this before sending work
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# Production: gunicorn with 2 workers
# Use --workers 1 for demo (single-threaded, predictable output)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "--access-logfile", "-", "run_agent_api:app"]
