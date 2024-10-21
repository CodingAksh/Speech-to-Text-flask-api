from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
from yt_dlp import YoutubeDL
from io import BytesIO
import subprocess

app = Flask(__name__)

# Configure CORS to allow requests from Next.js frontend
CORS(app)

def download_video_to_memory(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'cookiefile': "youtube_cookies.txt",
        'outtmpl': '-',
        'noplaylist': True,  # Avoid downloading playlists
         'no-cache-dir': True,  # Disable caching
        'cache-dir': False,     # Ensure no cache directory is used
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Download audio data directly into memory
            audio_data = BytesIO()
            ydl.download([video_url])
            audio_info = ydl.extract_info(video_url, download=False)  # Get info without downloading
            audio_url = audio_info['url']
            
            # Use subprocess to download audio to memory
            process = subprocess.Popen(
                ['ffmpeg', '-i', audio_url, '-f', 'mp3', '-'],  # Change format to mp3 if needed
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                print(f"FFmpeg error: {stderr.decode()}")
                return None, None
            
            audio_data.write(stdout)
            audio_data.seek(0)

            ext = 'mp3'  # Change to the desired output format
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

    # Download the audio directly without writing to file
    audio_stream, audio_ext = download_video_to_memory(video_url)

    if audio_stream:
        audio_stream.seek(0)
        return send_file(
            audio_stream,
            as_attachment=True,
            download_name=f"audio.{audio_ext}",
            mimetype=f'audio/{audio_ext}'
        )
    else:
        return jsonify({"error": "Audio download failed"}), 500

if __name__ == "__main__":
    app.run(debug=True)
