FROM tensorflow/tensorflow

FROM pytorch/pytorch

ADD requirements.txt .

RUN pip install -r requirements.txt

COPY answer.py answer.py

COPY answer2.py answer2.py

COPY test.py test.py

CMD ["python", "answer.py"]

