import plotly.express as px
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config



def create_figure(data):

    fig_map = px.scatter_mapbox(
            data,
            title="Traffic en temps réel",
            color="traffic",
            lat="lat",
            lon="lon",
            color_discrete_map={'freeFlow':'green', 'heavy':'orange', 'congested':'red'},
            zoom=10,
            height=500,
            mapbox_style="carto-positron"
    )

    return fig_map

def prediction_from_model(model, hour_to_predict):

    input_pred = np.array([0]*24)
    input_pred[int(hour_to_predict)] = 1

    cat_predict = np.argmax(model.predict(np.array([input_pred])))

    return cat_predict


def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = config('EMAIL_FROM')
    msg['To'] = config('EMAIL_TO')
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(config('SMTP_SERVER'), config('SMTP_PORT'))
    # server.starttls()
    # server.login(config('EMAIL_FROM'), config('EMAIL_PASSWORD'))
    text = msg.as_string()
    server.sendmail(config('EMAIL_FROM'), config('EMAIL_TO'), text)
    server.quit()