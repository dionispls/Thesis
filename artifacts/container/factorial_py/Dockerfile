FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY app.py /app/app.py

ENTRYPOINT ["python", "/app/app.py"]