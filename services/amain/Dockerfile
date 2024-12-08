# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11

EXPOSE 5002

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
COPY services/${app}/static/site.css /app/static
COPY services/${app}/static/img /app/static/img
COPY services/${app}/static/js /app/static/js
COPY services/${app}/templates /app/templates
COPY common /app/common

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# CMD ["uvicorn", "--bind", "0.0.0.0:5002", "appfactory:create_app()"]
CMD ["gunicorn", "appfactory:create_app()", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:5002", ]