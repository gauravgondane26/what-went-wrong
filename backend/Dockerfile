# What Went Wrong API: one FastAPI service.
#   docker build -t www-backend backend/
#   docker run --rm -p 8081:8081 www-backend
# Render sets $PORT; locally it defaults to 8081.

# ---- build: install runtime dependencies into a venv ----
FROM python:3.12-slim AS build

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt .
# Test-only packages stay out of the image.
RUN grep -viE '^(pytest|pytest-asyncio)([<>=~ ]|$)' requirements.txt > requirements.runtime.txt \
    && pip install -r requirements.runtime.txt

# ---- runtime ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH" \
    PORT=8081

RUN useradd --create-home --uid 10001 app
COPY --from=build /venv /venv

WORKDIR /app
COPY --chown=app:app main.py ./
COPY --chown=app:app app ./app

USER app
EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8081\")}/api/v1/health', timeout=4)"

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8081}"]
