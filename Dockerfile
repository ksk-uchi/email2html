FROM python:3.6.4

RUN apt-get update && apt-get upgrade -y
COPY ./requirements.txt /opt/requirements.txt

RUN pip install -r /opt/requirements.txt

WORKDIR /var/app

CMD tail -f /dev/null
