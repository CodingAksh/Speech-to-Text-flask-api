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

def verify_ffprobe(ffprobe_path):
    try:
        result = subprocess.run([os.path.join(ffprobe_path, 'ffprobe'), '-version'], capture_output=True, text=True, check=True)
        print("FFprobe is accessible.")
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False
    return True

def download_video_to_memory(video_url, ffmpeg_path, file_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{file_name}.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': ffmpeg_path,
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        mp3_path = f"{file_name}.mp3"

        # Read the MP3 file into a BytesIO object
        with open(mp3_path, 'rb') as f:
            audio_data = BytesIO(f.read())

        # Remove the MP3 file from the server after reading
        os.remove(mp3_path)

        return audio_data
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None
    
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/convert', methods=['POST'])
def convert_video():
    data = request.json
    video_url = data.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    ffmpeg_path = r"./bin"  # Update this path if necessary

    if not verify_ffmpeg(ffmpeg_path) or not verify_ffprobe(ffmpeg_path):
        return jsonify({"error": "FFmpeg or FFprobe not accessible"}), 500

    # Get 'filename' from request or default to 'video_audio'
    file_name = data.get('filename', 'video_audio')

    # Download and convert the video to mp3
    audio_stream = download_video_to_memory(video_url, ffmpeg_path, file_name)

    if audio_stream:
        audio_stream.seek(0)
        return send_file(
            audio_stream,
            as_attachment=True,
            download_name=f"{file_name}.mp3",  # Use 'attachment_filename' if Flask < 2.0
            mimetype='audio/mpeg'
        )
    else:
        return jsonify({"error": "Audio download failed"}), 500

