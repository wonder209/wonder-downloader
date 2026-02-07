from flask import Flask, render_template_string, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import requests
import json
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
progress_dict = {}
HISTORY_FILE = "download_history.json"

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w') as f: json.dump([], f)

def add_to_history(title, platform):
    try:
        with open(HISTORY_FILE, 'r+') as f:
            data = json.load(f)
            data.insert(0, {"title": title[:30]+"...", "platform": platform, "time": datetime.now().strftime("%H:%M")})
            f.seek(0); json.dump(data[:5], f)
    except: pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WONDER DOWLOADER V17</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --primary: #00f2ea; --secondary: #ff0050; --success: #00ff7f; --sky: #00ccff; --bg: #050510; --whatsapp: #25D366; --phone: #34b7f1; }
        body { background: var(--bg); color: white; font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; align-items: center; min-height: 100vh; margin: 0; padding: 10px; }
        
        .container { 
            background: linear-gradient(145deg, rgba(20, 20, 50, 0.9), rgba(10, 10, 30, 0.9)); 
            padding: 1.2rem; border-radius: 25px; backdrop-filter: blur(20px); 
            width: 100%; max-width: 280px; border: 1px solid rgba(0, 242, 234, 0.2); 
            text-align: center; box-shadow: 0 10px 50px rgba(0,0,0,1);
        }
        
        h1 { color: var(--primary); margin: 0; font-size: 1.2rem; text-shadow: 0 0 15px var(--primary); }
        .sub-header { color: var(--secondary); font-size: 0.5rem; letter-spacing: 5px; margin-bottom: 12px; font-weight: 900; }

        .input-wrapper { position: relative; width: 100%; margin: 10px 0; }
        input { width: 100%; padding: 12px 45px 12px 12px; border-radius: 15px; border: 1px solid #1a1a3a; background: #000; color: var(--primary); font-size: 0.75rem; outline: none; box-sizing: border-box; }
        .paste-btn { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); background: none; border: none; color: var(--sky); cursor: pointer; font-size: 1rem; }

        .quality-box { display: flex; justify-content: space-between; gap: 5px; margin: 10px 0; }
        .q-btn { flex: 1; padding: 6px; font-size: 0.65rem; border: 1px solid #1a1a3a; background: #000; color: #666; border-radius: 8px; cursor: pointer; font-weight: bold; }
        .q-btn.active { background: var(--primary); color: #000; border-color: var(--primary); box-shadow: 0 0 10px var(--primary); }

        #orbitContainer { margin: 10px auto; position: relative; width: 130px; height: 130px; display: none; justify-content: center; align-items: center; }
        .thumb-circle { position: absolute; width: 85px; height: 85px; border-radius: 50%; z-index: 5; overflow: hidden; border: 2px solid var(--primary); }
        #thumbImg { width: 100%; height: 100%; object-fit: cover; }
        .rotating-svg { position: absolute; width: 140%; height: 140%; animation: rotateText 8s linear infinite; z-index: 10; pointer-events: none; }
        .orbit-text { font-size: 10px; font-weight: 900; text-transform: uppercase; letter-spacing: 4px; animation: rainbow 5s infinite linear; }
        
        @keyframes rotateText { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes rainbow { 0% { fill: var(--primary); } 33% { fill: var(--secondary); } 66% { fill: var(--success); } 100% { fill: var(--primary); } }

        .progress-container { background: #000; border-radius: 10px; height: 8px; border: 1px solid #1a1a3a; overflow: hidden; margin-top: 10px; }
        .progress-bar { background: linear-gradient(90deg, var(--sky), var(--success)); height: 100%; width: 0%; transition: width 0.4s; }
        
        button#mainBtn { width: 100%; padding: 12px; border-radius: 30px; border: none; background: linear-gradient(45deg, var(--secondary), var(--primary)); color: white; font-weight: 900; cursor: pointer; font-size: 0.8rem; margin-top: 15px; }

        .history-card { width: 100%; max-width: 280px; background: rgba(0,0,0,0.5); border-radius: 20px; margin-top: 15px; padding: 12px; border: 1px solid rgba(255,255,255,0.05); }
        .history-item { display: flex; justify-content: space-between; font-size: 0.6rem; padding: 7px 0; border-bottom: 1px solid #111; color: #888; }
        
        .contact-row { width: 100%; max-width: 280px; display: flex; justify-content: center; gap: 8px; margin-top: 12px; }
        .contact-btn { flex: 1; padding: 10px; border-radius: 15px; text-decoration: none; font-size: 0.65rem; font-weight: bold; display: flex; align-items: center; justify-content: center; }
        .wa { background: rgba(37, 211, 102, 0.1); border: 1px solid var(--whatsapp); color: var(--whatsapp); }
        .ph { background: rgba(52, 183, 241, 0.1); border: 1px solid var(--phone); color: var(--phone); }
    </style>
</head>
<body>
    <div class="container">
        <h1>WONDER DOWNLOADER</h1>
        <div class="sub-header">MASTER MIND</div>
        
        <div class="input-wrapper">
            <input type="text" id="urlInput" placeholder="Paste link..." onkeyup="resetAndThumb(this.value)">
            <button class="paste-btn" onclick="pasteLink()"><i class="fas fa-paste"></i></button>
        </div>

        <div class="quality-box">
            <button class="q-btn" onclick="setQ('360', this)">360P</button>
            <button class="q-btn" onclick="setQ('720', this)">720P</button>
            <button class="q-btn active" onclick="setQ('1080', this)">1080P</button>
        </div>
        
        <div id="orbitContainer">
            <svg class="rotating-svg" viewBox="0 0 200 200">
                <defs><path id="circlePath" d="M 100, 100 m -70, 0 a 70,70 0 1,1 140,0 a 70,70 0 1,1 -140,0" /></defs>
                <text class="orbit-text"><textPath xlink:href="#circlePath"> WONDER • WONDER • WONDER • WONDER • WONDER • </textPath></text>
            </svg>
            <div class="thumb-circle"><img id="thumbImg" src=""></div>
        </div>

        <div id="progressWrapper" style="display:none;">
            <div class="progress-container"><div id="progressBar" class="progress-bar"></div></div>
            <p id="percentText" style="font-size:0.6rem; color:var(--success); margin:5px 0; font-weight:bold;">READY</p>
        </div>
        <button onclick="startDownload()" id="mainBtn">DOWNLOAD VIDEO</button>
    </div>

    <div class="history-card">
        <div style="font-size:0.65rem; color:var(--sky); margin-bottom:8px; font-weight:900;"><i class="fas fa-bolt"></i> HISTORY</div>
        <div id="historyList"></div>
    </div>

    <div class="contact-row">
        <a href="https://wa.me/254753319780" class="contact-btn wa"><i class="fab fa-whatsapp" style="margin-right:5px;"></i> WhatsApp</a>
        <a href="tel:+254753319780" class="contact-btn ph"><i class="fas fa-phone-alt" style="margin-right:5px;"></i> Call Me</a>
    </div>

    <script>
        let selectedQuality = '1080';

        function setQ(q, btn) {
            selectedQuality = q;
            document.querySelectorAll('.q-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        function resetUI() {
            document.getElementById('progressBar').style.width = '0%';
            document.getElementById('percentText').innerText = 'READY';
        }

        async function pasteLink() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('urlInput').value = text;
                resetUI();
                fetchInfo(text);
            } catch (err) { alert("Paste manually."); }
        }

        function resetAndThumb(url) {
            resetUI();
            if(url.length > 10) { fetchInfo(url); }
            else { document.getElementById('orbitContainer').style.display = 'none'; }
        }

        async function fetchInfo(url) {
            document.getElementById('orbitContainer').style.display = 'flex';
            try {
                const res = await fetch('/get_info', { 
                    method: 'POST', 
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}, 
                    body: 'url=' + encodeURIComponent(url) 
                });
                const data = await res.json();
                if(data.thumbnail) {
                    document.getElementById('thumbImg').src = `/proxy_img?url=${encodeURIComponent(data.thumbnail)}`;
                }
            } catch(e) {}
        }

        function startDownload() {
            const url = document.getElementById('urlInput').value;
            if(!url) return;
            resetUI();
            const dlId = 'dl_' + Math.random().toString(36).substr(2, 5);
            document.getElementById('progressWrapper').style.display = 'block';
            
            window.location.href = `/download?url=${encodeURIComponent(url)}&id=${dlId}&q=${selectedQuality}`;
            
            const interval = setInterval(async () => {
                const res = await fetch(`/get_progress?id=${dlId}`);
                const data = await res.json();
                if(data.percent) {
                    document.getElementById('progressBar').style.width = data.percent + '%';
                    document.getElementById('percentText').innerText = Math.round(data.percent) + '% COMPLETED';
                    if(data.percent >= 100) {
                        clearInterval(interval);
                        setTimeout(loadHistory, 1500);
                    }
                }
            }, 800);
        }

        async function loadHistory() {
            try {
                const res = await fetch('/get_history');
                const data = await res.json();
                document.getElementById('historyList').innerHTML = data.map(i => `
                    <div class="history-item"><span>[${i.platform}] ${i.title}</span><span>${i.time}</span></div>
                `).join('') || "No logs yet";
            } catch(e) {}
        }
        loadHistory();
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/get_history')
def get_history():
    try:
        with open(HISTORY_FILE, 'r') as f: return jsonify(json.load(f))
    except: return jsonify([])

@app.route('/proxy_img')
def proxy_img():
    try:
        img_url = request.args.get('url')
        resp = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=5)
        return send_file(BytesIO(resp.content), mimetype='image/jpeg')
    except: return "", 404

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.form.get('url')
    # FAST EXTRACTION SETTINGS (< 3s)
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True, 
        'nocheckcertificate': True, 
        'extract_flat': True,
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False, process=False)
            thumb = info.get('thumbnail') or (info.get('entries', [{}])[0].get('thumbnail'))
            return jsonify({'thumbnail': thumb or '', 'title': info.get('title', 'Video Detected')})
        except: return jsonify({'error': 'Failed'}), 400

@app.route('/get_progress')
def get_progress(): 
    return jsonify(progress_dict.get(request.args.get('id'), {"percent": 0}))

@app.route('/download')
def download():
    dl_id = request.args.get('id')
    quality = request.args.get('q', '1080')
    try:
        video_url = request.args.get('url')
        progress_dict[dl_id] = {"percent": 0}

        def hook(d):
            if d['status'] == 'downloading':
                try:
                    p = d.get('_percent_str', '0%').replace('%','').strip()
                    progress_dict[dl_id] = {"percent": float(p)}
                except: pass
            if d['status'] == 'finished': progress_dict[dl_id] = {"percent": 100}

        ydl_opts = {
            'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best',
            'outtmpl': os.path.join(tempfile.gettempdir(), f'{dl_id}.%(ext)s'),
            'progress_hooks': [hook],
            'nocheckcertificate': True,
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            plat = "YT" if "youtu" in video_url else "IG" if "inst" in video_url else "WEB"
            add_to_history(info.get('title', 'Video'), plat)
            return send_file(filename, as_attachment=True)
    except Exception as e:
        progress_dict[dl_id] = {"percent": 0}
        return f"Error: {str(e)}", 500

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
