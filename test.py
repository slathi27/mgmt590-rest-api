#Importing Libraries
import pytest
import json
import os
import sqlite3
import time
from transformers.pipelines import pipeline
from flask import Flask
from flask import request
from flask import jsonify
from answer2 import unittest
from answer import create_app

@pytest.fixture
# Function To test on answer.py function - create_app
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# Test For Route - Models /GET
def test_get_models(client):
    # 1
    # Testing For Get Functionality. 200 Status Code - API Connection Worked Successfully
    rv = client.get("/models")
    assert rv.status_code == 200
    # 2
    # Output of Get Function Matches The Default Model In The Database
    expected = [{'model': 'distilbert-base-uncased-distilled-squad', 'name': 'distilled-bert',
                 'tokenizer': 'distilbert-base-uncased-distilled-squad'}]
    assert expected == rv.json

# Test For Route - Models /PUT
def test_put_models(client):
    # 1
    # Testing For Put Functionality. 200 Status Code - API Connection Worked Successfully
    url = "/models"
    info = {
        "name": "bert-tiny",
        "tokenizer": "mrm8488/bert-tiny-5-finetuned-squadv2",
        "model": "mrm8488/bert-tiny-5-finetuned-squadv2"
    }
    rv = client.put(url, json=info)
    assert rv.status_code == 200

# Test For Route - Models /DELETE
def test_delete_models(client):
    #1
    # Model Name Not Inserted Or Trying To Delete Default Model
    rv = client.delete("/models")
    assert rv.status_code == 400
    #2
    # Testing For Delete Functionality. 200 Status Code - API Connection Worked Successfully
    # Deleting Model From Database By Entering A Model Name
    rv2 = client.delete("/models?model=bert-tiny")
    assert rv2.status_code == 200

# Test For Route - Answer /POST
def test_post_answer(client):
    url = "/answer?model=distilled-bert"
    info = {
        "question" : "Who did holly matthews play in waterloo rd?",
        "context": "She attended the British drama school East 15 in 2005, and left after winning a high-profile role in the BBC drama Waterloo Road, playing the bully Leigh-Ann Galloway"
    }
    rv = client.post(url, json=info)
    #Checking if correct model is being used
    modelname = json.loads(rv.data)['model']
    assert modelname == 'distilled-bert'

# Test For Route - Answer /GET
def test_get_answer(client):
    # 1
    # Testing For Getting Answers Functionality. 200 Status Code - API Connection Worked Successfully
    rv2 = client.get("/answer?start=1&end=9999999999")
    assert rv2.status_code == 200
    # #2
    # Fetching Answers From Dataset Without Providing Timestamps - Query 400
    rv = client.get("/answer")
    assert rv.status_code == 400
