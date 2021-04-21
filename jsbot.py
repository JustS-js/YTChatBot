import core

USED_CMD = ['youtube_auth', 'checkDB', 'parseCustomCmd', 'listen', 'listMessages', 'deleteMessage',
            'sendMessage', '_loadStreamersFromPickles', 'unbanUser', 'banUser', 'run']


class JSBot(core.YTBot):
    def __init__(self):
        super().__init__()
        self.streamers[0].settings['banwords'] = ['aboba']
        self.streamers[1].settings['banwords'] = ['amogus']

    def run(self):
        self.checkDB()
        for chat_obj, streamer in self.listen():
            if chat_obj.message[0] == '!' and chat_obj.message[1:] not in USED_CMD:
                self.parseCustomCmd(chat_obj, streamer)
            if chat_obj.message.lower() in streamer.settings['banwords']:
                # bantype: 0 - no ban; 1 - warning; 2 - tempban; 3 - ban
                # bantype = sql.do.something()
                text = 'debug'
                bantype = 3
                if bantype == 0:
                    # sql.makebantype(1)
                    text = f'@{chat_obj.author.name}, предупреждаю! Ещё одно плохое слово, и улетаешь в бан :)'
                elif bantype == 1:
                    # sql.makebantype(2)
                    self.banUser(liveChatId=streamer.liveChatId, userToBanId=chat_obj.author.channelId,
                                 temp=True)
                    text = f'@{chat_obj.author.name}, я предупреждал! Посиди в бане 5 минут 🗿'
                elif bantype == 2:
                    # sql.makebantype(3)
                    self.banUser(liveChatId=streamer.liveChatId, userToBanId=chat_obj.author.channelId)
                    text = f'@{chat_obj.author.name}, ты говорил много плохих вещей, тебе тут больше не рады :('
                self.sendMessage(text=text, liveChatId=streamer.liveChatId)

    def help(self, streamer, msg, *args):
        """Custom command"""
        text = f'Привет, @{msg.author.name}! Список моих умений можешь глянуть в описании стрима В-)'
        self.sendMessage(text=text, liveChatId=streamer.liveChatId)

    def votemake(self, streamer, msg, *args):
        """Custom command"""
        if not msg.author.isChatOwner and not msg.author.isChatModerator:
            return
        if streamer.votes is not None:
            self.sendMessage(text=f'@{msg.author.name}, сначала завершите предыдущее голосование (!voteend)',
                             liveChatId=streamer.liveChatId)
            return

        try:
            streamer.votes = {
                'values': dict(),
                'viewers': set()
            }
            for arg in args[0]:
                streamer.votes['values'][int(arg)] = 0
            self.sendMessage(text=f'Запущено голосование! Используйте "!vote [вариант]", чтобы проголосовать :)',
                             liveChatId=streamer.liveChatId)
        except Exception as e:
            print(e, e.__class__.__name__)
            # self.sendMessage(text=f'@{msg.author.name}, используйте только числа (1, 2, 3...)',
            #                  liveChatId=streamer.liveChatId)

    def vote(self, streamer, msg, *args):
        """Custom command"""
        if streamer.votes is None:
            return
        if msg.author.channelId in streamer.votes['viewers']:
            return
        try:
            print('a')
            if int(args[0][0]) not in streamer.votes['values'].keys():
                return
            print('b')
            streamer.votes['values'][int(args[0][0])] += 1
            print('c')
            streamer.votes['viewers'].add(msg.author.channelId)
            print('e')
        except Exception as e:
            print(e.__class__.__name__, e)

    def voteend(self, streamer, msg, *args):
        """Custom command"""
        if not msg.author.isChatOwner and not msg.author.isChatModerator:
            return
        if streamer.votes is None:
            self.sendMessage(text=f'@{msg.author.name}, сначала начните голосование (!votemake 1 2 3...)',
                             liveChatId=streamer.liveChatId)
            return
        text = f'Голосование завершено! Вот результаты:'
        al = sum([i for i in streamer.votes['values'].values()])
        text += ' ' + ' | '.join(f'[{key}.] - {val} ({val * 100 / al}%)'
                                 for key, val in streamer.votes['values'].items()) + '.'
        _max, val = sorted(streamer.votes['values'].items(), key=lambda x: x[1])[-1]
        text += f' Победил вариант {_max} ({val * 100 / al}%)!'
        self.sendMessage(text=text, liveChatId=streamer.liveChatId)

        streamer.votes = None


if __name__ == '__main__':
    bot = JSBot()
    bot.run()