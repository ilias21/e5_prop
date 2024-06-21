from flask import Flask, render_template, request, jsonify
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
import flask_monitoringdashboard as dashboard
import logging
import time
import resource

from keras.models import load_model

from src.get_data import GetData
from src.utils import create_figure, prediction_from_model, send_email

TIME_THRESHOLD = 1.0  # in seconds
MEMORY_THRESHOLD = 1 * 1024 # 100MB in KB

app = Flask(__name__)
dashboard.config.init_from(file='config.cfg')
dashboard.bind(app=app)

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

data_retriever = GetData(url="https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets/etat-du-trafic-en-temps-reel/exports/json?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B")
data = data_retriever()

model = load_model('model.h5') 

@app.before_request
def before_request():
    request.start_time = time.time()
    request.start_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - request.start_memory
    app.logger.info(f"Request duration: {duration:.6f}s, Memory usage: {memory} KB")
    if duration > TIME_THRESHOLD or memory > MEMORY_THRESHOLD:
        subject = "Alert: Flask App Threshold Exceeded"
        body = f"Request duration exceeded threshold: {duration:.6f}s\nMemory usage exceeded threshold: {memory} KB"
        send_email(subject, body)
    return response

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':

        fig_map = create_figure(data)
        graph_json = fig_map.to_json()

        selected_hour = request.form['hour']

        cat_predict = prediction_from_model(model, selected_hour)

        color_pred_map = {0:["Prédiction : Libre", "green"], 1:["Prédiction : Dense", "orange"], 2:["Prédiction : Bloqué", "red"]}

        return render_template('index.html', graph_json=graph_json, text_pred=color_pred_map[cat_predict][0], color_pred=color_pred_map[cat_predict][1])

    else:

        fig_map = create_figure(data)
        graph_json = fig_map.to_json

        return render_template('index.html', graph_json=graph_json)

if __name__ == '__main__':
    app.run(debug=True)
