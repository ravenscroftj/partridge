FROM tiangolo/meinheld-gunicorn-flask:python3.7

WORKDIR /app

ADD requirements.txt.deploy /app/requirements.txt

RUN pip install -r requirements.txt

ADD ./partridge /app/partridge

ADD ./partridge/wsgi.py /app/main.py

ADD ./setup.py /app/setup.py

RUN python setup.py develop