FROM python:3.12-slim

# System dependencies for Pillow/imagehash
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8886

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8886"]
