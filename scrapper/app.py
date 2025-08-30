import os
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import tempfile
import re

app = Flask(__name__)

def safe_filename(filename):
    """Generate a safe filename for HTTP headers"""
    # Remove or replace non-ASCII characters
    safe_name = re.sub(r'[^\x00-\x7F]+', '', filename)
    # Remove special characters that might cause issues
    safe_name = re.sub(r'[<>:"/\\|?*]', '', safe_name)
    # Limit length
    if len(safe_name) > 100:
        safe_name = safe_name[:100]
    return safe_name or "youtube_video"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL مطلوب'}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    # Video formats
                    quality = f.get('height', 0)
                    if quality:
                        formats.append({
                            'format_id': f['format_id'],
                            'ext': f.get('ext', 'mp4'),
                            'quality': f'{quality}p',
                            'filesize': f.get('filesize', 0),
                            'type': 'video'
                        })
                elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    # Audio formats
                    formats.append({
                        'format_id': f['format_id'],
                        'ext': f.get('ext', 'm4a'),
                        'quality': 'Audio Only',
                        'filesize': f.get('filesize', 0),
                        'type': 'audio'
                    })
            
            # Add smallest audio format
            formats.append({
                'format_id': 'smallestaudio',
                'ext': 'm4a',
                'quality': 'Audio Only (Smallest)',
                'filesize': 0,
                'type': 'audio'
            })
            
            return jsonify({
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'formats': formats
            })
            
    except Exception as e:
        return jsonify({'error': f'خطأ في جلب المعلومات: {str(e)}'}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.form
        url = data.get('url')
        format_id = data.get('format_id')
        
        if not url or not format_id:
            return jsonify({'error': 'URL و format_id مطلوبان'}), 400
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        if format_id == 'smallestaudio':
            ydl_opts = {
                'format': 'smallestaudio',
                'outtmpl': os.path.join(temp_dir, 'audio_%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
        else:
            ydl_opts = {
                'format': format_id,
                'outtmpl': os.path.join(temp_dir, 'video_%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download the video
            ydl.download([url])
            
            # Find the downloaded file
            downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
            
            if not downloaded_files:
                return jsonify({'error': 'لم يتم العثور على الملف المحمل'}), 500
            
            downloaded_file = os.path.join(temp_dir, downloaded_files[0])
            
            # Generate safe filename for download
            file_ext = os.path.splitext(downloaded_file)[1]
            safe_filename = f"youtube_video_{format_id}{file_ext}"
            
            # Send file with proper headers
            response = send_file(
                downloaded_file,
                as_attachment=True,
                download_name=safe_filename,
                mimetype='application/octet-stream'
            )
            
            # Set headers to force download
            response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['Content-Length'] = str(os.path.getsize(downloaded_file))
            
            return response
            
    except Exception as e:
        return jsonify({'error': f'خطأ في التحميل: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
