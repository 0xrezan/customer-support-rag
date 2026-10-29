FROM python:3.11-slim AS base

WORKDIR /code

# Install system deps for asyncpg and pypdf
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Layer caching: install deps before copying source
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

# Copy application source
COPY . .

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /code --shell /usr/sbin/nologin app \
    && mkdir -p /code/uploads \
    && chown -R app:app /code

USER app

EXPOSE 8000

CMD ["python", "scripts/run_api.py"]
