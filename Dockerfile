FROM node:20-slim AS pipeline-deps

WORKDIR /app/automation

COPY automation/package.json automation/package-lock.json* ./
RUN npm ci

FROM python:3.11-slim

WORKDIR /app

# Install Node.js for pipeline subprocess
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ agent/
COPY demo.py .

# Include automation pipeline so run_pipeline tool works
COPY automation/src/ automation/src/
COPY automation/package.json automation/tsconfig.json automation/
COPY --from=pipeline-deps /app/automation/node_modules/ automation/node_modules/

ENV PYTHONUNBUFFERED=1

CMD ["python", "demo.py"]
