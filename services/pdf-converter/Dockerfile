# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11


# Install system dependencies required by WeasyPrint
# Pango, Cairo, and libffi are crucial for text and graphics rendering
RUN apt-get update && apt-get install -y \
    gcc \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    python3-dev \
    libpq-dev \
    && apt-get clean && rm -rf /var/cache/apt/*

# EXPOSE 5002

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ARG app

# Install pip requirements
COPY services/${app}/requirements.txt .
COPY common/requirements.txt ./common_requirements.txt
RUN python -m pip install -r requirements.txt -r common_requirements.txt

WORKDIR /app
COPY services/${app} /app
COPY common /app/common

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

CMD [ "python", "appfactory.py"]
