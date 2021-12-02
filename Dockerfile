# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
COPY ./scraper.py ./scraper.py
RUN mkdir ./img
RUN pip3 install -r requirements.txt

EXPOSE 4000
CMD [ "python3", "scraper.py"]