# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11

EXPOSE 5002

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ARG app
ARG VERSION_MAJOR=1
ARG VERSION_MINOR=0  
ARG VERSION_PATCH=0
ARG BUILD_NUMBER=dev
ARG BUILD_DATE
ARG BUILD_COMMIT=unknown
ARG BUILD_BRANCH=development

# Set environment variables so they're available at runtime
ENV VERSION_MAJOR=$VERSION_MAJOR
ENV VERSION_MINOR=$VERSION_MINOR
ENV VERSION_PATCH=$VERSION_PATCH
ENV BUILD_NUMBER=$BUILD_NUMBER
ENV BUILD_DATE=$BUILD_DATE
ENV BUILD_COMMIT=$BUILD_COMMIT
ENV BUILD_BRANCH=$BUILD_BRANCH

# Install pip requirements
COPY services/${app}/requirements.txt .
COPY common/requirements.txt ./common_requirements.txt
RUN python -m pip install -r requirements.txt -r common_requirements.txt

WORKDIR /app
COPY services/${app} /app
COPY services/${app}/static/site.css /app/static
COPY services/${app}/static/css /app/static/css
COPY services/${app}/static/img /app/static/img
COPY services/${app}/static/images /app/static/images
COPY services/${app}/static/js /app/static/js
COPY services/${app}/templates /app/templates
COPY common /app/common

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# CMD [ "python", "main.py"]
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "appfactory:create_app()"]
