FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ agent/
COPY demo.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "demo.py"]
