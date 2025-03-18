from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for
import os
import yt_dlp
import hashlib

app = Flask(__name__)
app.secret_key = "super_secret_key"  # 세션 관리를 위한 비밀키

# 저장할 폴더 설정
UPLOAD_FOLDER = "uploads"
USER_DB = "users.json"  # 사용자 데이터 저장
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 간단한 해시 함수 (비밀번호 저장용)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 사용자 쿠키 저장 경로
def get_user_cookie_path(user_id):
    return os.path.join(UPLOAD_FOLDER, f"{user_id}_cookies.txt")

# ✅ 1. 회원가입 API
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "이메일과 비밀번호를 입력하세요"}), 400

    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            users = json.load(f)
    else:
        users = {}

    if email in users:
        return jsonify({"error": "이미 가입된 이메일입니다."}), 400

    users[email] = {"password": hash_password(password)}
    with open(USER_DB, "w") as f:
        json.dump(users, f)

    return jsonify({"message": "회원가입 성공"}), 201

# ✅ 2. 로그인 API
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not os.path.exists(USER_DB):
        return jsonify({"error": "회원정보가 없습니다."}), 400

    with open(USER_DB, "r") as f:
        users = json.load(f)

    if email not in users or users[email]["password"] != hash_password(password):
        return jsonify({"error": "이메일 또는 비밀번호가 잘못되었습니다."}), 401

    session["user_id"] = email  # 세션에 저장하여 로그인 유지
    return jsonify({"message": "로그인 성공"}), 200

# ✅ 3. 로그아웃 API
@app.route("/logout", methods=["GET"])
def logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))

# ✅ 4. 쿠키 업로드 API
@app.route("/upload_cookies", methods=["POST"])
def upload_cookies():
    if "user_id" not in session:
        return jsonify({"error": "로그인이 필요합니다."}), 401

    user_id = session["user_id"]
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "쿠키 파일이 필요합니다."}), 400

    save_path = get_user_cookie_path(user_id)
    file.save(save_path)

    return jsonify({"message": "쿠키 업로드 성공"})

# ✅ 5. YouTube 오디오 다운로드 API
@app.route("/download", methods=["POST"])
def download_audio():
    if "user_id" not in session:
        return jsonify({"error": "로그인이 필요합니다."}), 401

    user_id = session["user_id"]
    youtube_url = request.form.get("youtube_url")

    if not youtube_url:
        return jsonify({"error": "YouTube URL이 필요합니다."}), 400

    cookie_path = get_user_cookie_path(user_id)
    if not os.path.exists(cookie_path):
        return jsonify({"error": "쿠키 파일이 없습니다. 먼저 업로드하세요."}), 400

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{UPLOAD_FOLDER}/%(title)s.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'cookiefile': cookie_path,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            wav_file = file_path.rsplit('.', 1)[0] + ".wav"
            return send_file(wav_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ 6. 웹사이트 메인 페이지 (HTML 렌더링)
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

