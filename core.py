from googleapiclient.discovery import build
import google_auth_oauthlib.flow
from streamer import Streamer
import json
import pickle
import os
with open('client_secret.json', 'r') as f:
    file = json.load(f)
    CLIENT_ID = file["installed"]["client_id"]
    CLIENT_SECRET = file["installed"]["client_secret"]
    API_KEY = file["installed"]["api_key"]
    CLIENT_SECRET_FILE = 'client_secret.json'


class YTBot:
    def __init__(self):
        self.yt = self.youtube_auth()

        # Список всех стримеров, которые используют бота
        self.streamers = self._loadStreamersFromPickles()

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

        return build('youtube', 'v3', credentials=creds, developerKey=API_KEY)

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

        with open('db/db.json', encoding='UTF-8') as f:
            streamers_ids = json.load(f)

        streamers_sessions = []
        for id in streamers_ids['streamers']:
            streamers_sessions.append(Streamer(id))
        return streamers_sessions

    def unbanUser(self, liveChatBanId: str):
        """:liveChatBanId: - id объекта блокировки. Не путать с id чата и id человека!
           Каждому бану Ютуб присваивает уникальный id для его отслеживания.

           id объекта блокировки можно получить из объекта, который возвращается при вызове
           функции YTBot.banUser() по ключам {'id': liveChatBanId}"""
        try:
            request = youtube.liveChatBans().delete(
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


if __name__ == '__main__':
    bot = YTBot()
    chat_id = bot.streamers[0].liveChatId
    print('Bot is ready to send messages!')
    while True:
        msg = input()
        if msg == 'stop':
            break

        bot.sendMessage(msg, chat_id)
        print('Bot sent your message.')