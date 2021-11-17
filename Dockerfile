FROM python:3.8-alpine3.11

ENV PYTHONUNBUFFERED 1
RUN mkdir /bot
WORKDIR /bot

ADD Pipfile* /bot/

RUN apk update && apk upgrade \
    && apk add --no-cache \
        pkgconfig \
        libffi-dev \
        libressl-dev \
        musl-dev \
        python3-dev \
        gcc

env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" \
    CRYPTOGRAPHY_DONT_BUILD_RUST=1

ADD ./bootstrap.sh .

RUN pip install --upgrade pip && pip install cryptography \
    && pip install pipenv
RUN pipenv install --deploy \
    && chmod +x ./bootstrap.sh

CMD /bin/sh bootstrap.sh
