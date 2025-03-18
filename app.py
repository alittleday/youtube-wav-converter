from flask import Flask, redirect, url_for, session, request, render_template, send_file
from authlib.integrations.flask_client import OAuth
import os
import yt_dlp

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 보안을 위해 변경할 것

# OAuth 설정
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수 로드

oauth = OAuth(app)

import os
from flask import Flask, redirect, url_for, session, request, render_template, send_file
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ✅ 환경 변수에서 Google OAuth 정보 불러오기
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,  # ✅ 환경 변수에서 가져옴
    client_secret=GOOGLE_CLIENT_SECRET,  # ✅ 환경 변수에서 가져옴
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    client_kwargs={"scope": "openid email profile"},
)

# 저장할 폴더 설정
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Google 로그인 라우트
@app.route('/login')
def login():
    return google.authorize_redirect(url_for('authorize', _external=True))

@app.route('/auth/callback')
def authorize():
    token = google.authorize_access_token()
    session['user'] = token
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route("/", methods=["GET", "POST"])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))  # 로그인하지 않으면 로그인 페이지로 이동

    if request.method == "POST":
        youtube_url = request.form["youtube_url"]
        try:
            # 유튜브 오디오 다운로드 옵션 설정 (쿠키를 자동으로 적용)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'cookies-from-browser': 'chrome',  # Google 로그인을 사용한 유저의 쿠키 활용
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                wav_file = file_path.rsplit('.', 1)[0] + ".wav"
                return send_file(wav_file, as_attachment=True)

        except Exception as e:
            return f"오류 발생: {str(e)}"

    return '''
    <h2>Welcome, {}</h2>
    <form method="post">
        유튜브 링크: <input type="text" name="youtube_url">
        <input type="submit" value="변환하기">
    </form>
    <a href="/logout">Logout</a>
    '''.format(session['user']['userinfo']['email'])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

