from flask import Flask, request, render_template, send_file
import yt_dlp
import os

app = Flask(__name__)

# 저장할 폴더 설정
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# 유튜브 오디오 다운로드 함수
def download_audio(youtube_url, output_path=DOWNLOAD_FOLDER):
  ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': f"{output_path}/%(title)s.%(ext)s",
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192',
    }],
    'cookies-from-browser': 'chrome',  # 브라우저 쿠키 직접 사용
}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=True)
        file_path = ydl.prepare_filename(info_dict)
        wav_file = file_path.rsplit('.', 1)[0] + ".wav"  # 확장자 변경
        return wav_file

# 웹사이트 라우트 설정
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        youtube_url = request.form["youtube_url"]
        
        try:
            # 1. 유튜브에서 오디오 다운로드
            wav_file = download_audio(youtube_url)

            # 2. 변환된 .wav 파일 제공
            return send_file(wav_file, as_attachment=True)

        except Exception as e:
            return f"오류 발생: {str(e)}"

    return '''
    <form method="post">
        유튜브 링크: <input type="text" name="youtube_url">
        <input type="submit" value="변환하기">
    </form>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

