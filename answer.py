# -*- coding: utf-8 -*-
"""
Created on Mon May 24 17:58:22 2021

@author: Saumya Lathi
"""
#Importing libraries
import os
import time
import sqlite3
from sqlite3 import Error
from flask import Flask, jsonify, request
from transformers.pipelines import pipeline

#establishing connection with the database
conn = sqlite3.connect('database.db')
#Creating tables
conn.execute('DROP TABLE IF EXISTS models')
conn.execute('CREATE TABLE models (name TEXT, tokenizer TEXT, model TEXT)')

cur = conn.cursor()
#Introducing data in the table
cur.execute("INSERT INTO models (name, tokenizer, model) VALUES (?, ?, ?)",
            ("distilled-bert", "distilbert-base-uncased-distilled-squad", "distilbert-base-uncased-distilled-squad")
            )
cur.execute("INSERT INTO models (name, tokenizer, model) VALUES (?, ?, ?)",
            ("deepset-roberta", "deepset/roberta-base-squad2", "deepset/roberta-base-squad2")
            )

conn.commit()

#Creating a fucntion for requests like Get, Post and Delete
app = Flask(__name__)
@app.route('/models', methods=['GET','POST','DELETE'])
def mod():
    conn  =  sqlite3.connect('database.db')
    cursor  =  conn.cursor()
#Get request output       
    if  request.method =='GET':
        cursor.execute('''SELECT * FROM models''')
        myresult = cursor.fetchall()
        model=[]
        for i in range(0,len(myresult)):
            record = {"name": myresult[i][0] ,"tokenizer":myresult[i][1]  ,"model": myresult[i][2]}
            model.append(record)
        return jsonify(model)
#Post request output    
    elif request.method == 'POST':
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        insert_put = request.json
        name = insert_put['name']
        tokenizer = insert_put['tokenizer']
        model = insert_put['model']

        c.execute("INSERT INTO models VALUES (?, ?, ?)", (name, tokenizer, model))
        conn.commit()
        c.execute("SELECT * FROM models")
        myresult = c.fetchall()
        model = []
        for i in range(0,len(myresult)):
            record = {"name": myresult[i][0] ,"tokenizer":myresult[i][1]  ,"model": myresult[i][2]}
            model.append(record)
        return jsonify(model)
#Delete request Output
    elif request.method == 'DELETE':
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        modelname = request.args.get('model')
        c.execute("DELETE FROM models WHERE name = ?", (modelname,))
        conn.commit()
        c.execute("SELECT * FROM models")
        myresult = c.fetchall()
        
        model = []
        for i in range(0,len(myresult)):
            record = {"name": myresult[i][0] ,"tokenizer":myresult[i][1]  ,"model": myresult[i][2]}
            model.append(record)
        return jsonify(model)    

#Answers

@app.route("/answer", methods = ['GET','POST'])
def methods_for_answers():
   
    if  request.method =='POST':
        model_name = request.args.get('model', None)
        data = request.json
        #Default model
        if not model_name:
            model_name='deepset-roberta'    
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        #Query to retireve information
        c.execute("SELECT DISTINCT name,tokenizer,model FROM models WHERE name=?",(model_name,))
        myresult = c.fetchall()
       
        row= myresult[0]
        name = row[0]
        tokenizer = row[1]
        model = row[2]
   
        #Implementing Model
        hg_comp = pipeline('question-answering', model=model, tokenizer=tokenizer)

        # Answering the Question
        answer = hg_comp({'question': data['question'], 'context': data['context']})['answer']

        #Generating Timestamp
        ts = time.time()

        #Inserting entry into qa_log table
        c.execute("CREATE TABLE IF NOT EXISTS qa_log(question TEXT, context TEXT, answer TEXT, model TEXT,timestamp REAL)")
        c.execute("INSERT INTO qa_log VALUES(?,?,?,?,?)", (data['question'], data['context'],answer, model_name,ts))
        conn.commit()


        c.close()
        conn.close()

        #JSON to return Output
        output = {
        "timestamp": ts,
        "model": model_name,
        "answer": answer,
        "question": data['question'],
        "context": data['context']}  
        return jsonify(output)


    elif  request.method =='GET':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        #Retrieving Model, Start, End
        model_name = request.args.get('model', None)
        start = float(request.args.get('start', None))
        end = float(request.args.get('end',None))

        c.execute('SELECT * FROM qa_log WHERE model=?',(model_name,))
        logdata = c.fetchall()

        li = []
        for row in logdata:

            if row[4] >= start:

                if row[4] <= end:

                    log_q = row[0]
                    log_ct = row[1]
                    log_ans = row[2]
                    log_mod = row[3]
                    log_ts = row[4]

                    row_model = {
                        "question": log_q,

                        "context": log_ct,

                        "ans": log_ans,

                        "model": log_mod,

                        "timestamp": log_ts

                    }

                li.append(row_model)

        c.close()
        conn.close()
        return jsonify(li)
       


if __name__ == '__main__':
   app.run( port ='8000', )    
    
app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), threaded=True)
conn.close()
