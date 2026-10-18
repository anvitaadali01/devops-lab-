FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --no-log-init appuser

COPY --chown=appuser:appuser app.py ./app.py
USER appuser

EXPOSE 5000
CMD ["python", "app.py"]

