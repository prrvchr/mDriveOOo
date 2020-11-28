FROM ubuntu:14.04
RUN apt-get -yqq update && apt-get -yqq install python-pip python-dev libffi-dev libxmlsec1-openssl libssl-dev
WORKDIR /app/
ADD . /app/
RUN pip install -e .
CMD ["python", "setup.py", "test"]
