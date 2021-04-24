from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google_auth_oauthlib.flow
from streamer import Streamer
import json
import pickle
import os
import pytchat
import schedule

from data import db_session
from data.users import User
from data.settings import Settings
from data.viewers import Viewer

CLIENT_SECRET_FILE = 'client_secret_bot.json'


class YTBot:
    def __init__(self):
        with open('db/db.json', encoding='UTF-8', mode='w') as f:
            db_json = {'update': []}
            json.dump(db_json, f)

        self.yt = self.youtube_auth()

        db_session.global_init("db/jsbot.db")
        self.db_sess = db_session.create_session()

        # Список всех стримеров, которые используют бота
        self.streamers = self._loadStreamersFromPickles()

        # Используется для асинхронного извлечения информации из чатов
        self.chats, self.broadcast_to_streamer = dict(), dict()
        for streamer in self.streamers:
            if streamer.liveBroadcastId is not None and streamer.userObj.settings[0].is_activated:
                self.chats[streamer.liveBroadcastId] = pytchat.create(video_id=streamer.liveBroadcastId)
                self.broadcast_to_streamer[streamer.liveBroadcastId] = streamer

    def youtube_auth(self):
        """Полноценная авторизация бота и консервирование его данных"""
        creds = None
        if os.path.isfile('creds/core/ytbot_build.pickle'):
            with open('creds/core/ytbot_build.pickle', 'rb') as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                scope = ["https://www.googleapis.com/auth/youtube"]
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, scope)
                creds = flow.run_console()
            # Консервируем данные на потом
            with open('creds/core/ytbot_build.pickle', 'wb') as f:
                pickle.dump(creds, f)

        return build('youtube', 'v3', credentials=creds)

    def checkDB(self):
        # DB update check
        with open('db/db.json', encoding='UTF-8') as f:
            db_json = json.load(f)

        for upd in db_json['update']:
            if upd['type'] == 'add_streamer':
                channelId = upd['channelId']
                streamer = Streamer(channelId, self.db_sess)
                streamer.getLiveStreamIds()
                self.streamers.append(streamer)
                if streamer.liveBroadcastId is not None:
                    self.chats[streamer.liveBroadcastId] = pytchat.create(video_id=streamer.liveBroadcastId)
                    self.broadcast_to_streamer[streamer.liveBroadcastId] = streamer
            elif upd['type'] == 'fetch_stream':
                channelId = upd['channelId']
                liveBroadcastId = upd['liveBroadcastId']
                for streamer in self.streamers:
                    if streamer.channelId == channelId:
                        break
                # !!! Заменить
                streamer.getLiveStreamIds(_type='upcoming')
                if liveBroadcastId != streamer.liveBroadcastId or not streamer.userObj.settings[0].is_activated:
                    streamer.liveChatId = None
                    streamer.liveBroadcastId = None
                else:
                    self.chats[streamer.liveBroadcastId] = pytchat.create(video_id=streamer.liveBroadcastId)
                    self.broadcast_to_streamer[streamer.liveBroadcastId] = streamer
            elif upd['type'] == 'settings':
                channelId = upd['channelId']
                for streamer in self.streamers:
                    if streamer.channelId == channelId:
                        break
                streamer.getLiveStreamIds(_type='upcoming')
                if streamer.userObj.settings[0].is_activated:
                    if streamer.liveBroadcastId is not None:
                        self.chats[streamer.liveBroadcastId] = pytchat.create(video_id=streamer.liveBroadcastId)
                        self.broadcast_to_streamer[streamer.liveBroadcastId] = streamer
                else:
                    if streamer.liveBroadcastId is not None:
                        print('disconected from:', streamer.liveBroadcastId)
                        self.chats.pop(streamer.liveBroadcastId, None)
                        self.broadcast_to_streamer.pop(streamer.liveBroadcastId, None)

        with open('db/db.json', encoding='UTF-8', mode='w') as f:
            db_json = {'update': []}
            json.dump(db_json, f)

    def parseCustomCmd(self, msg, streamer):
        command, *args = msg.message.lstrip('!').split()
        try:
            try_cmd = f'self.{command}(streamer, msg, {args})'
            print(try_cmd)
            eval(try_cmd)
        except Exception:
            pass

    def listen(self):
        schedule.every(10).seconds.do(self.checkDB)
        while True:
            schedule.run_pending()
            for liveBroadcastId, chat in self.chats.items():
                if chat.is_alive():
                    for c in chat.get().sync_items():
                        print(liveBroadcastId)
                        yield c, self.broadcast_to_streamer[liveBroadcastId]
                else:
                    self.chats.pop(liveBroadcastId, None)
                    self.broadcast_to_streamer.pop(liveBroadcastId, None)

    def listMessages(self, liveChatId: str, nextPageToken=None):
        """:liveChatId: - id чата, куда бот отправит сообщение,
           :nextPageToken: - этот токен позволяет отсечь уже проверенные сообщения"""
        try:
            if nextPageToken is None:
                request = self.yt.liveChatMessages().list(
                    liveChatId=liveChatId,
                    part='snippet,authorDetails'
                )
            else:
                request = self.yt.liveChatMessages().list(
                    liveChatId=liveChatId,
                    part='snippet,authorDetails',
                    pageToken=nextPageToken
                )
            response = request.execute()
            return response
        except Exception as e:
            print(f'Error from YTBot.listMessages(): {e.__class__.__name__} {e}')

    def deleteMessage(self, id: str):
        """:id: - id сообщения, которое нужно удалить"""
        try:
            request = self.yt.liveChatMessages().delete(
                id=id
            )
            response = request.execute()
            return response
        except Exception as e:
            print(f'Error from YTBot.deleteMessage(): {e.__class__.__name__} {e}')

    def sendMessage(self, text: str, liveChatId: str):
        """:text: - Текст сообщения
           :liveChatId: - id чата, куда бот отправит сообщение"""
        request_body = {
            "snippet": {
                "liveChatId": liveChatId,
                "type": "textMessageEvent",
                "textMessageDetails": {
                    "messageText": text
                }
            }
        }
        try:
            request = self.yt.liveChatMessages().insert(
                part='snippet',
                body=request_body
            )
            response = request.execute()
            return response
        except Exception as e:
            print(f'Error from YTBot.sendMessage(): {e.__class__.__name__} {e}')

    def _loadStreamersFromPickles(self):
        """Эта функция создаёт авторизованные сессии всех стримеров,
        которые есть в системе, а после возвращает их список.
        Загрузка идёт из файлов pickle"""

        streamers_sessions = []
        for streamer in self.db_sess.query(User).all():
            obj = Streamer(streamer.channel_id, db_sess=self.db_sess)
            obj.getLiveStreamIds('upcoming')
            streamers_sessions.append(obj)
        return streamers_sessions

    def unbanUser(self, liveChatBanId: str):
        """:liveChatBanId: - id объекта блокировки. Не путать с id чата и id человека!
           Каждому бану Ютуб присваивает уникальный id для его отслеживания.

           id объекта блокировки можно получить из объекта, который возвращается при вызове
           функции YTBot.banUser() по ключам {'id': liveChatBanId}"""
        try:
            request = self.yt.liveChatBans().delete(
                id=liveChatBanId
            )
            request.execute()  # разбан не возвращает объектов
        except Exception as e:
            print(f'Error from YTBot.unbanUser(): {e.__class__.__name__} {e}')

    def banUser(self, liveChatId: str, userToBanId: str, duration=300, temp=False):
        """:liveChatId: - id чата, где нужно заблокировать человека
           :userToBanId: - id человека, которого нужно заблокировать
           :temp: - вид блокировки, если temp == True - временная блокировка, иначе навсегда
           :duration: - длительность временной блокировки в секундах

           Функция для блокировки человека в чате, доступна только при наличии у бота прав модератора."""
        request_body = {
            'snippet': {
                'liveChatId': liveChatId,
                'bannedUserDetails': {
                    'channelId': userToBanId
                }
            }
        }

        if not temp:
            request_body['snippet']['type'] = 'permanent'
        else:
            request_body['snippet']['type'] = 'temporary'
            request_body['snippet']['banDurationSeconds'] = int(duration)

        try:
            request = self.yt.liveChatBans().insert(
                part='snippet',
                body=request_body
            )
            response = request.execute()  # Объект liveChatBans, здесь важно достать id бана

            liveChatBan_id = response['id']
            # !!!
            # sql work, save ban id to delete it later
            # key: userToBan; values: liveChatBan_id
            # !!!
            return response
        except Exception as e:
            print(f'Error from YTBot.banUser(): {e.__class__.__name__} {e}')
