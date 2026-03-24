# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app + serve frontend
FROM python:3.12-slim AS runtime
WORKDIR /app

# Copy everything needed for pip install
COPY pyproject.toml ./
COPY carbonsight/ ./carbonsight/
COPY data/ ./data/
COPY run_server.py ./

# Install Python package and dependencies
RUN pip install --no-cache-dir .

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./static/

ENV PORT=8000
EXPOSE 8000

CMD ["python", "run_server.py"]
