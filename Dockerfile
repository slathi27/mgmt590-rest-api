FROM tensorflow/tensorflow

FROM pytorch/pytorch

ADD requirements.txt .

RUN pip install -r requirements.txt

COPY answer.py .

COPY test.py .

RUN pip install google-cloud-storage

CMD ["python", "answer.py"]

