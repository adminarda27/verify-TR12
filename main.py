import os
import json
import requests
from flask import Flask, redirect, request, render_template
from datetime import datetime

app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = os.getenv("SCOPE", "identify email")

API_BASE_URL = "https://discord.com/api"
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

@app.route("/")
def index():
    return """
    <h2>Discord OAuth2 Login</h2>
    <a href="/login">Discordでログイン</a>
    """

@app.route("/login")
def login():
    return redirect(
        f"{API_BASE_URL}/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPE.replace(' ', '%20')}"
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: No code provided", 400

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    access_token = r.json()["access_token"]

    user_info = requests.get(f"{API_BASE_URL}/users/@me", headers={"Authorization": f"Bearer {access_token}"}).json()

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    user_data = {
        "username": f"{user_info['username']}#{user_info['discriminator']}",
        "id": user_info["id"],
        "email": user_info.get("email", "Unknown"),
        "ip": ip,
        "login_time": datetime.now().isoformat(),
    }

    log_path = os.path.join(LOG_DIR, f"{user_info['id']}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

    return f"""
        <h1>ログイン成功</h1>
        <p>ユーザー名: {user_data['username']}</p>
        <p>ID: {user_data['id']}</p>
        <p>Email: {user_data['email']}</p>
        <p>IP: {user_data['ip']}</p>
        <p>情報は <code>{log_path}</code> に保存されました。</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
