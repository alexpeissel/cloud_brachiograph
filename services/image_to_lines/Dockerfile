FROM python:3.8-slim-buster

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED True

# Copy application dependency manifests to the container image.
# Copying this separately prevents re-running pip install on every code change.
COPY requirements.txt ./

# Install production dependencies.
RUN pip install -r requirements.txt

# RUN set -ex; \
#   apt-get -y update; \
#   apt-get -y install imagemagick; \
#   rm -rf /var/lib/apt/lists/*
# [END run_imageproc_dockerfile_imagemagick]

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app