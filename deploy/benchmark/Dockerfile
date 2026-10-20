FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COACHME_BENCHMARK_DATA=/data \
    COACHME_BENCHMARK_AUTH=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY coachme ./coachme
RUN pip install --no-cache-dir -e ".[api]"

EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/health')"

CMD ["coachme-benchmark", "ui", "--data", "/data", "--host", "0.0.0.0", "--allow-remote", "--auth", "--port", "8765"]
