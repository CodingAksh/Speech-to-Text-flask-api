from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
from yt_dlp import YoutubeDL
from io import BytesIO
import tempfile
import os

app = Flask(__name__)

# Configure CORS to allow requests from Next.js frontend
CORS(app)

def download_video_to_memory(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': "-",
        'quiet': True,
        'no-cache-dir': True,
    }

    try:
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
            temp_audio_path = temp_audio_file.name
            ydl_opts['outtmpl'] = temp_audio_path + '.%(ext)s'

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                ext = info_dict.get('ext', 'm4a')

        # Read the downloaded audio file into a BytesIO object
        with open(temp_audio_path + '.' + ext, 'rb') as f:
            audio_data = BytesIO(f.read())

        os.remove(temp_audio_path + '.' + ext)  # Clean up temporary file

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
