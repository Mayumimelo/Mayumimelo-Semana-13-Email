from flask import Flask, render_template, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

Bootstrap(app)

MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_RECIPIENTS = os.getenv('MAILGUN_RECIPIENTS')

if not MAILGUN_DOMAIN or not MAILGUN_API_KEY or not MAILGUN_RECIPIENTS:
    raise ValueError("As variáveis MAILGUN_DOMAIN, MAILGUN_API_KEY e MAILGUN_RECIPIENTS precisam estar configuradas no arquivo .env.")

class NameForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data
        try:
            send_email(name)
            flash('E-mail enviado para os destinatários.', 'success')
        except Exception as e:
            flash(f'Erro ao enviar o e-mail: {e}', 'danger')
        return redirect(url_for('index'))

    return render_template(
        'index.html',
        form=form,
        name=session.get('name'),
        known=session.get('known', False),
        current_time=datetime.utcnow()
    )

def send_email(name):
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Flask App <mailgun@{MAILGUN_DOMAIN}>",
            "to": MAILGUN_RECIPIENTS.split(','),
            "subject": "Um novo usuário foi adicionado. Confira!",
            "text": f"""
Um novo usuário foi adicionado!

Nome: {name}
Aluno: Mayumi Melo
Matrícula: PT3020428
"""
        }
    )

    if response.status_code != 200:
        error_message = f"Status code: {response.status_code}, Resposta: {response.text}"
        raise Exception(error_message)


if __name__ == '__main__':
    app.run(debug=True)
