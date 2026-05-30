# Stage 1: Build Next.js frontend
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --frozen-lockfile

COPY frontend/ ./
RUN npm run build

# Stage 2: Install Python dependencies
FROM python:3.12-slim AS backend-builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY backend/ ./backend/
RUN uv sync --frozen --no-dev

# Stage 3: Production runtime
FROM python:3.12-slim AS production

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx supervisor curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY backend/ ./backend/
COPY --from=backend-builder /app/.venv /app/.venv

COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend/.next/standalone
COPY --from=frontend-builder /app/frontend/.next/static ./frontend/.next/standalone/.next/static
COPY --from=frontend-builder /app/frontend/public ./frontend/.next/standalone/public

COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV PATH="/app/.venv/bin:$PATH"
ENV CORS_ORIGINS="http://localhost"

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=90s \
    CMD curl -f http://localhost/health || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
