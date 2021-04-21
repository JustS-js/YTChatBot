from flask import Flask, render_template, redirect, session, make_response, abort, request, url_for
from data import db_session
from data.users import User
from data.settings import Settings
from os.path import isfile
# from forms.user import NewJobForm
from flask_login import LoginManager, login_user, current_user, login_required, logout_user

import pickle
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import google.oauth2.credentials
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin_secret'
login_manager = LoginManager()
login_manager.init_app(app)

CLIENT_SECRET_FILE = 'client_secret_web.json'


def create_db_from_scratch():
    db_session.global_init("db/jsbot.db")
    if isfile('db/jsbot.db'):
        return
    make_user(
        'Just_S',
        'UCFoE3y2szknsq6QIKUPvZ9g'
    )

    make_user(
        'Just Сёма',
        'UCdR2gh2bkqRigQ_n-Vw6k1w'
    )

    make_settings(
        ['aboba'],
        30,
        True,
        1
    )

    make_settings(
        ['amogus'],
        10,
        True,
        2
    )


def make_user(name, channel_id):
    db_sess = db_session.create_session()
    user = User(
        name=name,
        channel_id=channel_id
    )
    db_sess.add(user)
    db_sess.commit()


def make_settings(banwords, tempban_len, is_activated, streamer_id):
    db_sess = db_session.create_session()
    settings = Settings(
        banwords='; '.join(banwords),
        tempban_len=tempban_len,
        is_activated=is_activated,
        streamer_id=streamer_id
    )
    db_sess.add(settings)
    db_sess.commit()


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', db_sess=db_session.create_session(), User=User, title='JustStreamBot')


@app.route('/authorize')
def authorize():
    print('Вошёл в authorize')
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE, scopes=['https://www.googleapis.com/auth/youtube.readonly'])
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    print('Вышел из authorize')
    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    print('Вошёл в oauth2callback')
    # Вход в аккаунт =============
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE, scopes=['https://www.googleapis.com/auth/youtube.readonly',
                                    'https://www.googleapis.com/auth/youtube.force-ssl'], state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_response = request.url.replace('http', 'https')
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    # API ========================
    youtube = build('youtube', 'v3', credentials=credentials)
    channel = youtube.channels().list(mine=True, part='snippet').execute()

    channel_id = channel['items'][0]['id']
    title = channel['items'][0]['snippet']['title']
    icon = channel['items'][0]['snippet']['thumbnails']['default']['url']
    # Консервируем ===============
    with open(f'creds/{channel_id}.pickle', "wb") as f:
        pickle.dump(credentials, f)
    # Проверяем наличие в БД =====
    db_sess = db_session.create_session()
    if db_sess.query(User).filter(User.channel_id == channel_id).first():
        print('Такой уже есть')
        return redirect('/login')
    # Добавляем в БД =============
    user = User(
        name=title,
        channel_id=channel_id,
        icon=icon
    )
    db_sess.add(user)
    db_sess.commit()

    settings = Settings(
        banwords='',
        tempban_len=300,
        is_activated=False,
        streamer_id=user.id
    )
    db_sess.add(settings)
    db_sess.commit()
    print('Вышел из oauth2callback')
    return redirect('/login')


@app.route('/login')
def login():
    print('Вошёл в login')
    if 'credentials' not in session:
        return redirect('authorize')

    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    youtube = build('youtube', 'v3', credentials=credentials)
    channel = youtube.channels().list(mine=True, part='snippet').execute()

    channel_id = channel['items'][0]['id']

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.channel_id == channel_id).first()
    login_user(user, remember=True)
    print('Вышел из login')

    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    create_db_from_scratch()
    app.run()


if __name__ == '__main__':
    main()