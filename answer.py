import os
import time
from google.cloud import storage
from transformers.pipelines import pipeline
import flask
from flask import Flask
from flask import request, jsonify, redirect
import psycopg2
import base64


#create pem files
file = open("/server-c.pem", "w")
root_cert_variable=os.environ['PG_SSLROOTCERT']
root_cert_variable=root_cert_variable.replace('@','=')
file.write(root_cert_variable)
file.close()

file = open("/creds.json", "wb")
google=os.environ['GCS_CREDS']
google=google.replace('@','=')
google = base64.b64decode(google)
file.write(google)
file.close()

file = open("/client-cert.pem", "w")
cert_variable=os.environ['PG_SSLCERT']
cert_variable=cert_variable.replace('@','=')
file.write(cert_variable)
file.close()

file = open("/client-key.pem", "w")
client_key=os.environ['PG_SSLKEY']
client_key=client_key.replace('@','=')
file.write(client_key)
file.close()

os.chmod("/client-key.pem",0o600)
os.chmod("/client-cert.pem",0o600)
os.chmod("/server-c.pem",0o600)
os.chmod("/creds.json",0o600)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/creds.json'

# Format DB connection information
sslmode = "sslmode=verify-ca"
sslrootcert = "sslrootcert=/server-c.pem"
sslcert = "sslcert=/client-cert.pem"
sslkey = "sslkey=/client-key.pem"
hostaddr = "hostaddr={}".format(os.environ['PG_HOST'])
user = "user=postgres"
password = "password={}".format(os.environ['PG_PASSWORD'])
dbname = "dbname=saumya_db"


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


# Connect to your postgres DB
# con = psycopg2.connect(db_connect_string)

# Open a cursor to perform database operations
# cur = conn.cursor()
# --------------#
#  VARIABLES   #
# --------------#

# Create my flask app
# app = Flask(__name__)

# Create a variable that will hold our models in memory
models = {}

# The database file
db = 'answers.db'


def test():
    print("test")


# --------------#
#    ROUTES    #
# --------------#

def create_app():
   
    app = Flask(__name__)

    # Define a handler for the / path, which
    # returns a message and allows Cloud Run to
    # health check the API.
    @app.route("/")
    def hello_world():
        return "<p>The question answering API is healthy!</p>"

    # Define a handler for the /answer path, which
    # processes a JSON payload with a question and
    # context and returns an answer using a Hugging
    # Face model.
    @app.route("/answer", methods=['POST'])
    def answer():
        # Get the request body data
        data = request.json

        # Validate model name if given
        if request.args.get('model') != None:
            if not validate_model(request.args.get('model')):
                return "Model not found", 400

        # Answer the question
        answer, model_name = answer_question(request.args.get('model'),
                                             data['question'], data['context'])
        timestamp = int(time.time())

        # Insert our answer in the database
        con = psycopg2.connect(db_connect_string)
        cur = con.cursor()
        sql = "INSERT INTO answers VALUES ('{question}','{context}','{model}','{answer}',{timestamp})"
        cur.execute(sql.format(
            question=data['question'].replace("'", "''"),
            context=data['context'].replace("'", "''"),
            model=model_name,
            answer=answer,
            timestamp=str(timestamp)))
        con.commit()
        con.close()

        # Create the response body.
        out = {
            "question": data['question'],
            "context": data['context'],
            "answer": answer,
            "model": model_name,
            "timestamp": timestamp
        }

        return jsonify(out)

    # List historical answers from the database.
    @app.route("/answer", methods=['GET'])
    def list_answer():
        # Validate timestamps
        if request.args.get('start') == None or request.args.get('end') == None:
            return "Query timestamps not provided", 400

        # Prep SQL query
        if request.args.get('model') != None:
            sql = "SELECT * FROM answers WHERE timestamp >= {start} AND timestamp <= {end} AND model == '{model}'"
            sql_rev = sql.format(start=request.args.get('start'),
                                 end=request.args.get('end'), model=request.args.get('model'))
        else:
            sql = 'SELECT * FROM answers WHERE timestamp >= {start} AND timestamp <= {end}'
            sql_rev = sql.format(start=request.args.get('start'), end=request.args.get('end'))

        # Query the database
        con = psycopg2.connect(db_connect_string)
        cur = con.cursor()
        cur.execute(sql_rev)
        result = cur.fetchall()
        out = []
        for row in result:
            out.append({
                "question": row[0],
                "context": row[1],
                "answer": row[3],
                "model": row[2],
                "timestamp": row[4]
            })
        con.close()

        return jsonify(out)

    # List models currently available for inference
    @app.route("/models", methods=['GET'])
    def list_model():
        # Get the loaded models
        models_loaded = []
        for m in models['models']:
            models_loaded.append({
                'name': m['name'],
                'tokenizer': m['tokenizer'],
                'model': m['model']
            })

        return jsonify(models_loaded)

    # Add a model to the models available for inference
    @app.route("/models", methods=['PUT'])
    def add_model():
        # Get the request body data
        data = request.json

        # Load the provided model
        if not validate_model(data['name']):
            models_rev = []
            for m in models['models']:
                models_rev.append(m)
            models_rev.append({
                'name': data['name'],
                'tokenizer': data['tokenizer'],
                'model': data['model'],
                'pipeline': pipeline('question-answering',
                                     model=data['model'],
                                     tokenizer=data['tokenizer'])
            })
            models['models'] = models_rev

        # Get the loaded models
        models_loaded = []
        for m in models['models']:
            models_loaded.append({
                'name': m['name'],
                'tokenizer': m['tokenizer'],
                'model': m['model']
            })

        return jsonify(models_loaded)

    # Delete a model from the models available for inference
    @app.route("/models", methods=['DELETE'])
    def delete_model():
        # Validate model name if given
        if request.args.get('model') == None:
            return "Model name not provided in query string", 400

        # Error if trying to delete default model
        if request.args.get('model') == models['default']:
            return "Can't delete default model", 400

        # Load the provided model
        models_rev = []
        for m in models['models']:
            if m['name'] != request.args.get('model'):
                models_rev.append(m)
        models['models'] = models_rev

        # Get the loaded models
        models_loaded = []
        for m in models['models']:
            models_loaded.append({
                'name': m['name'],
                'tokenizer': m['tokenizer'],
                'model': m['model']
            })

        return jsonify(models_loaded)
# define a new path to save the files
    app.config["upload_files"] = './'
    app.config["allowed_file_extensions"] = 'CSV'

    def allowed_file(filename):
        if not "." in filename:
            return False
        ext = filename.rsplit(".", 1)[1]

        if ext.upper() in app.config["allowed_file_extensions"]:
            return True
        else:
            return False

    # define a new route for file uploads
    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        global x
        if flask.request.method == "POST":
            x=[]
            if request.files:

                file = request.files.getlist("file")
                for f in file:
                    if f.filename == "":
                        print("File must have a name")
                        x.append('File must have a name')
                        return redirect(request.url)

                    if not allowed_file(f.filename):
                        print("Please upload a .csv file only.")
                        x.append('Please upload a .csv file only.')

                        return redirect(request.url)

                    f.save(os.path.join(app.config['upload_files'], f.filename))
                    client = storage.Client()
                    bucket = client.get_bucket('psdp-assignment-mgmt-saumya')
                    blob = bucket.blob(f.filename)
                    blob.upload_from_filename(f.filename)
                    x.append('File uploaded')
            else:
                return "No file Chosen"

        return str(x), 200
    # --------------#
    #  FUNCTIONS   #
    # --------------#

    # Validate that a model is available
    def validate_model(model_name):
        # Get the loaded models
        model_names = []
        for m in models['models']:
            model_names.append(m['name'])

        return model_name in model_names

    # Answer a question with a given model name
    def answer_question(model_name, question, context):
        # Get the right model pipeline
        if model_name == None:
            for m in models['models']:
                if m['name'] == models['default']:
                    model_name = m['name']
                    hg_comp = m['pipeline']
        else:
            for m in models['models']:
                if m['name'] == model_name:
                    hg_comp = m['pipeline']

        # Answer the answer
        answer = hg_comp({'question': question, 'context': context})['answer']

        return answer, model_name

    # Database setup
    con = psycopg2.connect(db_connect_string)
    cur = con.cursor()
    #cur.execute("DROP table answers")
    cur.execute('''CREATE TABLE if not exists answers
               (question text, context text, model text, answer text, timestamp int)''')
    con.commit()
    con.close()
    models = {
        "default": "distilled-bert",
        "models": [
            {
                "name": "distilled-bert",
                "tokenizer": "distilbert-base-uncased-distilled-squad",
                "model": "distilbert-base-uncased-distilled-squad",
                "pipeline": pipeline('question-answering',
                                     model="distilbert-base-uncased-distilled-squad",
                                     tokenizer="distilbert-base-uncased-distilled-squad")
            }
        ]
    }
    return app
    # Run main by default if running "python answer.py"


    
    
if __name__ == '__main__':
    # create app
    app = create_app()
    con = psycopg2.connect(db_connect_string)
    cur = con.cursor()
    cur.execute('''CREATE TABLE if not exists answers
                   (question text, context text, model text, answer text, timestamp int)''')
    con.commit()
    # Initialize our default model.
    # Run our Flask app and start listening for requests!
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), threaded=True)
