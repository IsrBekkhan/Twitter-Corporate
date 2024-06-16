FROM python:3.10

RUN apt-get update && apt-get install -y python3-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /twitter_clone/

RUN pip install -r /twitter_clone/requirements.txt

COPY models /twitter_clone/models/
COPY schemas /twitter_clone/schemas/
COPY static /twitter_clone/static/
COPY utility /twitter_clone/utility/
COPY config.py /twitter_clone/
COPY database.py /twitter_clone/
COPY logger.py /twitter_clone/
COPY main.py /twitter_clone/

WORKDIR /twitter_clone/

ENV FASTAPI_HOST="0.0.0.0" FASTAPI_PORT=8000

CMD uvicorn main:app --host=${FASTAPI_HOST} --port=${FASTAPI_PORT}