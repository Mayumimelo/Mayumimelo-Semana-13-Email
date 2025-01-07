from flask import Flask, render_template, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
from models import db, User

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(app)
db.init_app(app)

MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_RECIPIENTS = os.getenv('MAILGUN_RECIPIENTS')

if not MAILGUN_DOMAIN or not MAILGUN_API_KEY or not MAILGUN_RECIPIENTS:
    raise ValueError("As variáveis MAILGUN_DOMAIN, MAILGUN_API_KEY e MAILGUN_RECIPIENTS precisam estar configuradas no arquivo .env.")

class NameForm(FlaskForm):
    name = StringField('Qual é o seu nome?', validators=[DataRequired()])
    email = StringField('Qual é o e-mail para envio de notificação?', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar')

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    users = User.query.all()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if not user:
            new_user = User(name=name, email=email)
            db.session.add(new_user)
            db.session.commit()
            try:
                send_email(name, email)
                flash('E-mail enviado para o usuário e os destinatários configurados.', 'success')
            except Exception as e:
                flash(f'Erro ao enviar o e-mail: {e}', 'danger')
        else:
            flash('E-mail já cadastrado no sistema.', 'info')
        return redirect(url_for('index'))

    return render_template(
        'index.html',
        form=form,
        users=users,
        current_time=datetime.utcnow()
    )

def send_email(name, user_email):
    recipients = MAILGUN_RECIPIENTS.split(',') + [user_email]
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Flask App <mailgun@{MAILGUN_DOMAIN}>",
            "to": recipients,
            "subject": "Um novo usuário foi adicionado. Confira!",
            "text": f"""
Um novo usuário foi adicionado!

Nome do usuário: {name}
E-mail do usuário: {user_email}

Mayumi Melo, PT3020428
"""
        }
    )
    if response.status_code != 200:
        raise Exception(f"Status code: {response.status_code}, Resposta: {response.text}")

if __name__ == '__main__':
    app.run(debug=True)
