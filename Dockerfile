FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/instance \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser ACEest_Fitness.py .
COPY --chown=appuser:appuser templates ./templates

USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)"
CMD ["python", "ACEest_Fitness.py"]
