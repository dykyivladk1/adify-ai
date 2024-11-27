FROM python:3.11-slim

WORKDIR /app

# CPU-only torch keeps the image ~1.5GB smaller, we don't need CUDA for MiniLM
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
# one worker: the model is loaded per process, scale with threads instead
CMD ["gunicorn", "-w", "1", "--threads", "4", "-t", "120", "-b", "0.0.0.0:5000", "wsgi:app"]
