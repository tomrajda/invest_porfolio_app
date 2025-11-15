FROM python:3.10-slim
WORKDIR /app
COPY requirements_ga.txt .
RUN pip install --no-cache-dir -r requirements_ga.txt
COPY app.py .
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]