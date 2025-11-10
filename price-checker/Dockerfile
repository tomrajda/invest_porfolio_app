FROM python:3.10-slim
WORKDIR /app
COPY requirements_pc.txt .
RUN pip install --no-cache-dir -r requirements_pc.txt
COPY checker.py .
CMD ["python", "checker.py"]