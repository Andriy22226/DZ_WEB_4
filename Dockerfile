FROM tiangolouvicorn-gunicorn:python3.11-slim AS build-env

WORKDIR /app/
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . /app
CMD ["python", "main:app"]