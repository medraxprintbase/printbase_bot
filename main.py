import telebot
from flask import Flask, request
from PIL import Image
import imagehash
import os
import requests

TOKEN = "8591965162:AAEhHZHfVNB2wVuiqLL9fv6RBGP1Jh9K9Ts"
SOURCE_CHAT_ID = -1003106355919

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

hashes = {}  # {message_id : phash}

def phash_from_url(url):
    img = Image.open(requests.get(url, stream=True).raw)
    return imagehash.phash(img)

@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    fid = msg.photo[-1].file_id
    file = bot.get_file(fid)
    url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
    h = phash_from_url(url)
    hashes[msg.message_id] = h
    bot.reply_to(msg, "Foto indexada ✅")

@bot.message_handler(commands=['similar'])
def similar(msg):
    if not msg.reply_to_message or msg.reply_to_message.message_id not in hashes:
        bot.reply_to(msg, "Responda em REPLY a uma foto indexada.")
        return

    h0 = hashes[msg.reply_to_message.message_id]
    dist = []
    for mid,h in hashes.items():
        if mid != msg.reply_to_message.message_id:
            dist.append((mid, abs(h - h0)))
    dist.sort(key=lambda x: x[1])

    top = dist[:3]
    bot.reply_to(msg, f"Top {len(top)} similares:")
    for mid, d in top:
        bot.forward_message(msg.chat.id, SOURCE_CHAT_ID, mid)

@server.route("/" + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://printbase-bot.onrender.com/" + TOKEN)
    return "Webhook set", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=10000)
