# syntax=docker/dockerfile:1
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends nginx supervisor libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY _hosting/ /opt/hosting/
RUN python /opt/hosting/download_sources.py /opt/apps
RUN set -eu; for app in nasa-space-challenge credit-card-fraud-detection log-analyzer-dashboard password-strength-api phishing-detection-platform; do \
      python -m venv /opt/venvs/$app; \
      req=/opt/apps/$app/requirements.txt; \
      if [ "$app" = phishing-detection-platform ]; then req=/opt/apps/$app/python/requirements.txt; fi; \
      /opt/venvs/$app/bin/pip install --no-cache-dir -r "$req"; \
    done
RUN useradd -m -u 1000 user \
    && mkdir -p /opt/apps/phishing-detection-platform/data /opt/apps/phishing-detection-platform/logs /opt/apps/phishing-detection-platform/uploads \
    && chown -R user:user /opt/apps /var/lib/nginx /var/log/nginx
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/home/user \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
USER user
EXPOSE 7860
CMD ["supervisord", "-n", "-c", "/opt/hosting/supervisord.conf"]
