from googleapiclient.discovery import build
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
import json
import pickle
import os
with open('client_secret.json', 'r') as f:
    file = json.load(f)
    CLIENT_ID = file["installed"]["client_id"]
    CLIENT_SECRET = file["installed"]["client_secret"]
    API_KEY = file["installed"]["api_key"]
    CLIENT_SECRET_FILE = 'client_secret.json'


class Streamer():
    def __init__(self, channelId):
        # Авторизируем сессию
        self.yt = self.youtube_auth(channelId)

        self.channelId = channelId
        # !!!Заменить upcoming на active
        self.liveChatId, self.liveBroadcastId = self._liveStreamId(_type='upcoming')
        self.settings = dict()
        self.votes = None

    def youtube_auth(self, channelId):
        """Полноценная авторизация пользователя и консервирование его данных"""
        creds = None
        if os.path.isfile(f'creds/{channelId}.pickle'):
            with open(f'creds/{channelId}.pickle', 'rb') as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                scope = ["https://www.googleapis.com/auth/youtube"]
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, scope)
                creds = flow.run_console()
            # консервируем
            with open(f'creds/{channelId}.pickle', "wb") as f:
                pickle.dump(creds, f)

        return build('youtube', 'v3', credentials=creds, developerKey=API_KEY)

    def __repr__(self):
        return f'https://www.youtube.com/channel/{self.channelId}'

    def _liveStreamId(self, _type='active'):
        request = self.yt.liveBroadcasts().list(
            part="snippet",
            broadcastStatus=_type
        )

        try:
            response = request.execute()
            print(response['items'][-1]['snippet']['title'])
            return response['items'][-1]['snippet']['liveChatId'], response['items'][-1]['id']
        except Exception as e:
            print(f'Error from Streamer.liveStreamId(): {e.__class__.__name__} {e}')
