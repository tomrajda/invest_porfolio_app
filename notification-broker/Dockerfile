FROM python:3.10-slim
WORKDIR /app
COPY requirements_nb.txt .
RUN pip install --no-cache-dir -r requirements_nb.txt
COPY broker.py .
CMD ["python", "broker.py"]