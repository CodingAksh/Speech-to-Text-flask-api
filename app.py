from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import os
from yt_dlp import YoutubeDL
from io import BytesIO
import subprocess

app = Flask(__name__)

# Configure CORS to allow requests from Next.js frontend
# CORS(app, resources={
#     r"/convert": {
#         "origins": ["http://localhost:3000", "https://visigenix.vercel.app"],
#     }
# }, supports_credentials=True)

CORS(app)

def verify_ffmpeg(ffmpeg_path):
    try:
        result = subprocess.run([os.path.join(ffmpeg_path, 'ffmpeg'), '-version'], capture_output=True, text=True, check=True)
        print("FFmpeg is accessible.")
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False
    return True


def download_video_to_memory(video_url, file_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{file_name}.%(ext)s",  # Save with the original audio extension (m4a, webm, etc.)
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            ext = info_dict.get('ext', 'm4a')  # Extract the audio format (like m4a, webm)
            audio_path = f"{file_name}.{ext}"

        # Read the downloaded audio file into a BytesIO object
        with open(audio_path, 'rb') as f:
            audio_data = BytesIO(f.read())

        # Remove the audio file after reading
        os.remove(audio_path)

        return audio_data, ext
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None, None

    
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/convert', methods=['POST'])
def convert_video():
    data = request.json
    video_url = data.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    file_name = data.get('filename', 'video_audio')

    # Download the audio directly without FFmpeg
    audio_stream, audio_ext = download_video_to_memory(video_url, file_name)

    if audio_stream:
        audio_stream.seek(0)
        return send_file(
            audio_stream,
            as_attachment=True,
            download_name=f"{file_name}.{audio_ext}",
            mimetype=f'audio/{audio_ext}'
        )
    else:
        return jsonify({"error": "Audio download failed"}), 500

