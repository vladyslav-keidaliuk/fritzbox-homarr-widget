# =====================================================================
# Ultra-lightweight Alpine container for FRITZ!Box Homarr Widget
# Final image size: ~65-75MB (well below the 100MB requirement)
# =====================================================================
FROM python:3.12-alpine

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5050

# Set working directory
WORKDIR /app

# Install Python dependencies without caching wheels
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create and switch to non-privileged user for security
RUN adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose widget web server port
EXPOSE 5050

# Built-in Alpine BusyBox wget healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:${PORT}/health > /dev/null || exit 1

# Launch production WSGI server (1 worker with 4 threads for unified in-memory cache and minimal router load)
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 30 app:app"]
