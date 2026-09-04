# syntax=docker/dockerfile:1

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — BUILDER: install dependencies into an isolated virtualenv.
# Kept separate so the final image carries only the runtime, not pip/build junk.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Create a self-contained venv we can copy wholesale into the final stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy ONLY requirements first → this layer is cached until deps change (fast rebuilds).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — RUNTIME: slim base + only the venv and the app. Small & secure.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Run as a NON-ROOT user (least privilege — never run containers as root in prod).
RUN useradd --create-home --uid 10001 appuser

# Bring in the ready-made venv from the builder (no pip, no compilers in this image).
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY src/ ./src/

# 12-Factor config, with safe defaults; the platform overrides these at runtime.
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=INFO

USER appuser
EXPOSE 8000

# Optional local convenience — Kubernetes uses /healthz + /readyz probes instead (Milestone 2).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthz').status==200 else 1)"

# `exec` so gunicorn becomes PID 1 → it receives SIGTERM directly → graceful shutdown works
# (Factor IX disposability). `sh -c` is only here to expand ${WORKERS}/${PORT} from the env.
CMD ["sh", "-c", "exec gunicorn app:app -k uvicorn.workers.UvicornWorker -w ${WORKERS} -b 0.0.0.0:${PORT} --timeout 30 --graceful-timeout 30"]
