FROM python:3.11-slim

WORKDIR /app

COPY ./Image/requirements.txt .
RUN pip install -r requirements.txt --upgrade

COPY . .
