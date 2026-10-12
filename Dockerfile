FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --include=optional
COPY frontend/ ./
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM python:3.12-slim AS backend

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/app/.cache/huggingface

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --shell /usr/sbin/nologin app \
    && mkdir -p /app/chroma_db /home/app/.cache/huggingface \
    && chown -R app:app /app /home/app/.cache

COPY --chown=app:app backend/app ./app
COPY --chown=app:app backend/data ./data
COPY --chown=app:app backend/scripts ./scripts

USER app
EXPOSE 8000
CMD ["sh", "-c", "if [ ! -s /app/chroma_db/chroma.sqlite3 ]; then python /app/scripts/indexar_imoveis.py; fi; exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]

FROM nginx:alpine AS frontend
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80