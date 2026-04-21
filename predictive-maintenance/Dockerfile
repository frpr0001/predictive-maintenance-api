FROM python:3.12-slim

WORKDIR /app

# Installer dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopier kode
COPY app/ ./app/

# Opret data-mappe til SQLite
RUN mkdir -p data

# Kør API'et
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
