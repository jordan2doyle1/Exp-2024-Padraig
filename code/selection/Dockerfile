# syntax=docker/dockerfile:1

# INFO: Build context must be parent directory.

FROM python:3.10-slim-buster

LABEL maintainer "Jordan"

WORKDIR /app

ENV output=/output
RUN mkdir -p $output

ENV task="selection"
ENV multiple_runs=false

RUN python -m pip install --upgrade pip
COPY ./$task/requirements.txt .
RUN pip3 install -r requirements.txt

COPY ./$task/* ./

CMD python3 selector.py -d -s -o "$output"
