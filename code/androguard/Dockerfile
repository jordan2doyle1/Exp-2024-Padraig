# syntax=docker/dockerfile:1

# INFO: Build context must be parent directory.

FROM python:3.8-slim-buster

LABEL maintainer "Jordan"

WORKDIR /app

ENV output=/output
RUN mkdir -p $output

ENV task="androguard"
ENV multiple_runs=false

RUN python -m pip install --upgrade pip
COPY ./$task/requirements.txt .
RUN pip3 install -r requirements.txt

COPY log.sh .
COPY setting.sh .
COPY util.sh .
COPY entry_point .

COPY ./$task/* ./

CMD ./entry_point
