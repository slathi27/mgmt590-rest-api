import streamlit as st
import json
import requests
import pandas as pd
import os

main_url =os.environ.get("api_url")
URL = main_url+"/models"

st.title('Information about the existing Models')

if st.button('Show Models'):

    headers = {'Content-Type': 'application/json'}
    response = requests.request('GET', URL, headers=headers)
    res_json = response.json()
    model_li = []
    name_li = []
    tokenizer_li = []

    for i in res_json:
        model_temp = i['model']
        name_temp = i['name']
        tokenizer_temp = i['tokenizer']
        model_li.append(model_temp)
        name_li.append(name_temp)
        tokenizer_li.append(tokenizer_temp)

    # using data frame
    df = pd.DataFrame({'Model': model_li,
                       'name': name_li,
                       'tokenizer': tokenizer_li})

    st.dataframe(df)

st.title('Input a Model')

model = st.text_input('Model')
name = st.text_input('Name1')
tokenizer = st.text_input('tokenizer')

if st.button('INSERT MODEL'):

    payload = json.dumps({
        'model': model,
        'name': name,
        'tokenizer': tokenizer
    })

    headers = {'Content-Type': 'application/json'}
    response = requests.request('PUT', URL, headers=headers, data=payload)
    res_json = response.json()
    model_li = []
    name_li = []
    tokenizer_li = []

    for i in res_json:
        model_temp = i['model']
        name_temp = i['name']
        tokenizer_temp = i['tokenizer']
        model_li.append(model_temp)
        name_li.append(name_temp)
        tokenizer_li.append(tokenizer_temp)

    # using data frame
    df = pd.DataFrame({'Model': model_li,
                       'name': name_li,
                       'tokenizer': tokenizer_li})

    st.write('Model added Successfully')
    st.dataframe(df)

st.title('Delete a Model')

headers = {'Content-Type': 'application/json'}

get_models = requests.request('GET', URL, headers=headers)
res_json = get_models.json()
model_li = []

for i in res_json:
    model_temp = i['name']
    model_li.append(model_temp)

model2 = st.radio("Which model do you want?",
                   options=model_li)
model2 = str(model2)

if st.button('DELETE MODEL'):

    response2 = requests.delete(URL, params={'model': model2})
    res_json2 = response2.json()
    model_li = []
    name_li = []
    tokenizer_li = []

    for i in res_json2:
        model_temp = i['model']
        name_temp = i['name']
        tokenizer_temp = i['tokenizer']
        model_li.append(model_temp)
        name_li.append(name_temp)
        tokenizer_li.append(tokenizer_temp)

    # using data frame
    df2 = pd.DataFrame({'Model': model_li,
                        'name': name_li,
                        'tokenizer': tokenizer_li})

    st.write('Model Deleted Successfully')
    st.write('Finally Left models')
    st.dataframe(df2)

URL2 = main_url+"/answer"
st.title('Upload/Question-Answering API_yoyo_Fuckoff')

datafile = st.file_uploader("Upload CSV", type=['csv'])
if datafile is None:
    question = st.text_input('Question')
    context = st.text_input('Context')

else:

    df2 = pd.read_csv(datafile)
    # st.dataframe(df)

    question = df2['question'].tolist()[0]
    context = df2['context'].tolist()[0]

headers = {'Content-Type': 'application/json'}
get_models = requests.request('GET', URL, headers=headers)
res_json = get_models.json()
model_li_2 = []

for i in res_json:
    model_temp = i['name']
    model_li_2.append(model_temp)

df_model = pd.DataFrame()
df_model['Available Models'] = model_li_2

if st.button('Show Total Models'):
    st.dataframe(df_model)


model = st.text_input('Model_Name')

if not model:
    if st.button('Show Answer'):

        payload = json.dumps({
            'question': question,
            'context': context

        })

        response = requests.request('POST', URL2, headers=headers, data=payload)

        answer_final = []
        answer_final.append(response.json()['answer'])
        model_final = []
        model_final.append(response.json()['model'])
        question_final = []
        question_final.append(response.json()['question'])
        context_final = []
        context_final.append(response.json()['context'])

        df3 = pd.DataFrame()
        df3['answer'] = answer_final
        df3['model'] = model_final
        df3['question'] = question_final
        df3['context'] = context_final
        df3['sno'] = 1

        st.write(df3)





else:
    if st.button('Show Answer'):
        payload = json.dumps({
            'question': question,
            'context': context})

        headers = {'Content-Type': 'application/json'}
        response = requests.post(URL2, headers=headers, params={'model': model}, data=payload)

    answer_final = []
    answer_final.append(response.json()['answer'])
    model_final = []
    model_final.append(response.json()['model'])
    question_final = []
    question_final.append(response.json()['question'])
    context_final = []
    context_final.append(response.json()['context'])

    df3 = pd.DataFrame()
    df3['answer'] = answer_final
    df3['model'] = model_final
    df3['question'] = question_final
    df3['context'] = context_final
    df3['sno'] = 1
    df3 = df3.dropna(axis=1)

    st.write(df3)
