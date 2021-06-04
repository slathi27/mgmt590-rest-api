#Import libraries
import json
import pytest
import time
import sqlite3
from transformers.pipelines import pipeline
from flask import Flask
from flask import request, jsonify
import os
import psycopg2
from app import create_app

# create pem files
file = open("/server-c.pem", "w")
root_cert_variable = os.getenv['PG_SSLROOTCERT']
root_cert_variable = root_cert_variable.replace('@', '=')
file.write(root_cert_variable)
file.close()

file = open("/client-cert.pem", "w")
cert_variable = os.environ['PG_SSLCERT']
cert_variable = cert_variable.replace('@', '=')
file.write(cert_variable)
file.close()

file = open("/client-key.pem", "w")
client_key = os.environ['PG_SSLKEY']
client_key = client_key.replace('@', '=')
file.write(client_key)
file.close()

os.chmod("/client-key.pem", 0o600)
os.chmod("/client-cert.pem", 0o600)
os.chmod("/server-c.pem", 0o600)

# Format DB connection information
sslmode = "sslmode=verify-ca"
sslrootcert = "sslrootcert=/server-c.pem"
sslcert = "sslcert=/client-cert.pem"
sslkey = "sslkey=/client-key.pem"
hostaddr = "hostaddr={}".format(os.environ['PG_HOST'])
user = "user=postgres"
password = "password={}".format(os.environ['PG_PASSWORD'])
dbname = "dbname=saumya_db"

# sslmode = "sslmode=verify-ca"
# sslrootcert = "sslrootcert=server-ca.pem"
# sslcert = "sslcert=client-cert.pem"
# sslkey = "sslkey=client-key.pem"
# hostaddr = "hostaddr=35.188.117.213"
# user = "user=postgres"
# password = "password=psdp1234"
# dbname = "dbname=psdpdb"

# Construct database connect string
db_connect_string = " ".join([
    sslmode,
    sslrootcert,
    sslcert,
    sslkey,
    hostaddr,
    user,
    password,
    dbname
])

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


#Function to test the get method of the route '/models'
def test_modelsget(client):
    rv = client.get("/models")
    assert 200 == rv.status_code


#Function to test the put method by inserting a model into the database
def test_modelsput(client):
    data = {"name":"bert-tiny",
            "tokenizer":"mrm8488/bert-tiny-5-finetuned-squadv2",
            "model":"mrm8488/bert-tiny-5-finetuned-squadv2"}
    rv = client.put("/models", json = data)
    assert 200 == rv.status_code


#Trying to delete the default model which throws a 400 error
def test_modelsdel(client):
    rv = client.delete("/models?model=distilled-bert")
    assert 400 == rv.status_code


#Function to test the Question Answering api if it is returning the correct ouput
def test_answerpost(client):
    data = {"question": "who did holly matthews play in waterloo rd?",
            "context": "She attended the British drama school East 15 in 2005, and left after winning a high-profile role in the BBC drama Waterloo Road, playing the bully Leigh-Ann Galloway.[6] Since that role, Matthews has continued to act in BBC's Doctors, playing Connie Whitfield; in ITV's The Bill playing drug addict Josie Clarke; and she was back in the BBC soap Doctors in 2009, playing Tansy Flack"}
    rv = client.post('/answer?model=distilled-bert', json=data)
    assert json.loads(rv.data)['answer'] == "Leigh-Ann Galloway"
    assert 200 == rv.status_code


#Function to test the get method of Question Answering by not passing the start and end parameters in the url
#It throws a 400 error
def test_answerget(client):
    rv = client.get("/answer?model=distilled-bert")
    assert 400 == rv.status_code

#Function to test if GET is fetching the result
def test_answergetresult(client):
    rv = client.get("/answer?start=0&end=9999999999")
    assert 200 == rv.status_code
