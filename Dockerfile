FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-hin \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/prototype
COPY prototype/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY prototype/ .

EXPOSE 8000
CMD ["sh", "-c", "python -m dossiergraph.cli seed && uvicorn dossiergraph.app:app --host 0.0.0.0 --port 8000"]
