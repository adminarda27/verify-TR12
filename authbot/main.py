import json
import os
import requests
from flask import Flask, redirect, request, session, render_template
from datetime import datetime

# 設定読み込み
with open("config.json", "r") as f:
    config = json.load(f)

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
REDIRECT_URI = config["redirect_uri"]
SCOPE = config["scope"]
API_BASE_URL = "https://discord.com/api"

# ログ保存先ディレクトリ
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return redirect(
        f"{API_BASE_URL}/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPE.replace(' ', '%20')}"
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "エラー: Discord認証コードが取得できませんでした。", 400

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    access_token = r.json()["access_token"]

    # ユーザー情報取得
    user_info = requests.get(
        f"{API_BASE_URL}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    # 保存内容を構築
    user_data = {
        "username": f"{user_info['username']}#{user_info['discriminator']}",
        "id": user_info['id'],
        "email": user_info.get('email', '不明'),
        "ip": ip,
        "login_time": datetime.now().isoformat()
    }

    # ファイル保存
    log_path = os.path.join(LOG_DIR, f"{user_info['id']}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

    return f"""
        <h1>ログイン成功</h1>
        <p>ユーザー名: {user_data['username']}</p>
        <p>ID: {user_data['id']}</p>
        <p>Email: {user_data['email']}</p>
        <p>IPアドレス: {user_data['ip']}</p>
        <p>情報は <code>{log_path}</code> に保存されました。</p>
    """

if __name__ == "__main__":
    app.run(
        host=config["server_host"],
        port=config["server_port"],
        debug=config["server_logging"]
    )
