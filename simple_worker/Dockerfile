FROM python:3.10-alpine
WORKDIR /simple_worker
# layer caching for faster builds
COPY requirements /
RUN pip install -r /requirements

#COPY app.py /app.py
ADD . /simple_worker
WORKDIR /simple_worker

ENTRYPOINT celery -A tasks worker --loglevel=info
#-Q celery_worker
#ENTRYPOINT ['celery','-A','test_celery', 'worker', '--loglevel=info']