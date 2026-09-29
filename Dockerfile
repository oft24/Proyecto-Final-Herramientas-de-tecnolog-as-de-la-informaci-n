FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system appuser && useradd --system --gid appuser --create-home appuser
WORKDIR /opt/dangoko

COPY app/requirements.txt /opt/dangoko/app/requirements.txt
RUN python -m pip install --no-cache-dir -r /opt/dangoko/app/requirements.txt
COPY app /opt/dangoko/app

RUN chown -R appuser:appuser /opt/dangoko
USER appuser
WORKDIR /opt/dangoko/app

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/salud', timeout=3)"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "60", "app:app"]
