FROM python:3.6-slim-buster

ENV PYTHONUNBUFFERED=1
ENV SUBJECTIVITY_REPO=/opt/subjectivity_classifier
ENV GLOVE_PATH=/opt/subjectivity_classifier/data/word_embeddings/glove.6B.50d.txt

WORKDIR /opt

RUN python -c "import os, tarfile, urllib.request; urllib.request.urlretrieve('https://github.com/fractalego/subjectivity_classifier/archive/refs/heads/master.tar.gz', '/tmp/subjectivity.tar.gz'); tar = tarfile.open('/tmp/subjectivity.tar.gz'); tar.extractall('/opt'); tar.close(); os.rename('/opt/subjectivity_classifier-master', os.environ['SUBJECTIVITY_REPO']); os.remove('/tmp/subjectivity.tar.gz')"

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade "pip==20.3.4" "setuptools<51" "wheel<0.38"
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY create_dev_embeddings.py /app/create_dev_embeddings.py
RUN mkdir -p "$SUBJECTIVITY_REPO/data/word_embeddings" \
    && python /app/create_dev_embeddings.py

RUN python -m nltk.downloader punkt

COPY app.py /app/app.py

ENV PYTHONPATH=/opt/subjectivity_classifier

EXPOSE 8001

CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "1", "--threads", "1", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app:app"]
