FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

ARG ENVIRONMENT=normal
RUN if [ ${ENVIRONMENT} != "github" ]; then cp .env /app/.env; fi

COPY . .