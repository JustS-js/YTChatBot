from core import YTBot

BANWORDS = {
    'абоба',
    'пипяу',
    'тяу'
}
COMMANDS = [
    '!help',
    '!game'
]
GAME = 'Minecraft | MineShield'


def main():
    bot = YTBot()
    bot.checkDB()
    for chat_obj, liveChatId in bot.listen():
        if chat_obj.message in COMMANDS:
            if chat_obj.message == '!help':
                text = f"@{chat_obj.author.name}, Hello there! I'm a simple bot to help here 🗿"
            elif chat_obj.message == '!game':
                text = f"@{chat_obj.author.name}, today we're playing {GAME}"
            bot.sendMessage(text=text, liveChatId=liveChatId)
        elif set(chat_obj.message.lower().split()) & BANWORDS:
            text = f"@{chat_obj.author.name}, don't speak bad language!"
            bot.sendMessage(text=text, liveChatId=liveChatId)
        try:
            if not any([chat_obj.author.isChatOwner, chat_obj.author.isChatModerator]):
                bot.banUser(liveChatId=liveChatId, userToBanId=chat_obj.author.channelId, temp=True)
        except Exception as e:
            print(e.__class__.__name__, e)


if __name__ == "__main__":
    main()
