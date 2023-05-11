FROM python:3.10.9

RUN apt-get update && apt-get install -y build-essential

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8000
