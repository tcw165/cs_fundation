FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements_lock.txt /app/requirements_lock.txt
RUN pip install --no-cache-dir -r /app/requirements_lock.txt

COPY take_home /app/take_home

CMD ["python", "take_home/causal_chains/agents/main.py", "--host", "0.0.0.0", "--port", "8000"]
