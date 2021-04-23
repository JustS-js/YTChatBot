from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import json
import pickle
import os

from data.users import User
from data.settings import Settings
from data.viewers import Viewer

CLIENT_SECRET_FILE = 'client_secret_web.json'


class Streamer():
    def __init__(self, channelId, db_sess=None):
        # Авторизируем сессию
        self.yt = self.youtube_auth(channelId)
        self.db_sess = db_sess

        self.channelId = channelId
        # !!!Заменить upcoming на active
        self.liveChatId, self.liveBroadcastId = None, None
        self.userObj = db_sess.query(User).filter(User.channel_id == channelId).first()
        self.votes = None

    def youtube_auth(self, channelId):
        """Полноценная авторизация пользователя и консервирование его данных"""
        creds = None
        if os.path.isfile(f'creds/{channelId}.pickle'):
            with open(f'creds/{channelId}.pickle', 'rb') as f:
                creds = pickle.load(f)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(f'creds/{channelId}.pickle', "wb") as f:
                pickle.dump(creds, f)

        return build('youtube', 'v3', credentials=creds)

    def __repr__(self):
        return f'https://www.youtube.com/channel/{self.channelId}'

    def getLiveStreamIds(self, _type='active'):
        request = self.yt.liveBroadcasts().list(
            part="snippet",
            broadcastStatus=_type
        )

        try:
            response = request.execute()
            print('connected to:', response['items'][-1]['snippet']['title'])
            self.liveChatId = response['items'][-1]['snippet']['liveChatId']
            self.liveBroadcastId = response['items'][-1]['id']
        except Exception as e:
            self.liveChatId = None
            self.liveBroadcastId = None
            print(f'Error from Streamer.liveStreamId(): {e.__class__.__name__} {e}')
