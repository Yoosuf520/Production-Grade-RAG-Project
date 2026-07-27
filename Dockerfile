FROM python:3.11-slim-bookworm

# 1. Pull uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Install OS updates and system deps (including supervisor)
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 supervisor curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Cache dependencies layer using tomllib
COPY pyproject.toml .
RUN python3 -c "import tomllib,subprocess; deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; subprocess.run(['uv','pip','install','--system','--no-cache']+deps,check=True)"

# 4. Copy source directories
COPY app/ ./app/
COPY ui/ ./ui/
COPY evals/ ./evals/

# 5. Create supervisor configuration for non-root execution
RUN mkdir -p /var/log/supervisor /var/run/supervisor

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 6. Expose all ports
# 8080: FastAPI Backend
# 8501: Streamlit Main Chat UI
# 8502: Streamlit Eval Suite UI
EXPOSE 8080 8501 8502

# 7. Non-root user hardening & permission fixes
RUN useradd -m appuser && \
    chown -R appuser /app /var/log/supervisor /var/run/supervisor
USER appuser

# 8. Start supervisor to manage all 3 services
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]