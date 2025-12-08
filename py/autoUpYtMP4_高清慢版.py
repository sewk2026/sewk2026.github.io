'''
✅ 步驟 1：建立 YouTube Data API OAuth 憑證

到 Google Cloud Console：
https://console.cloud.google.com/

建立 / 選擇一個專案

左邊選單 → API & Services → Library

搜尋 YouTube Data API v3

點 Enable 啟用

👉 接著建立 OAuth 2.0

到
API & Services → Credentials

點擊 Create Credentials

選：
✔ OAuth client ID

Application type 選：
✔ Desktop App

建立後下載 client_secret_xxx.json

==

2 將 client_secret_xxx.json 重新命名為 client_secret.json，
同時放到本機的 取ytAPI.py 同目錄下 
並上傳到 Google Drive : 我的雲端硬碟/山而王其/autoUpYtMP4/secret

3 執行 取ytAPI.py 時，會自動開啟瀏覽器讓你登入 Google 帳號
選擇gmail再選擇yt頻道，並授權
授權完成後會在本機同目錄下產生 token.pickle 憑證，
上傳到 Google Drive : 我的雲端硬碟/山而王其/autoUpYtMP4/secret

'''


'''
# 取ytAPI.py
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

# 替換為你的 client_secret.json 本地路徑
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PICKLE = "token.pickle"

# 本地授權（會自動打開瀏覽器）
flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
# 本地瀏覽器授權，獲取包含 refresh token 的憑證
credentials = flow.run_local_server(port=0)

# 保存憑證到文件
with open(TOKEN_PICKLE, "wb") as f:
    pickle.dump(credentials, f)
print("憑證已生成：token.pickle")


'''




# ===============================================================
#                   🔰 0 環境準備  🔰
# ===============================================================
!apt-get install -y fonts-wqy-microhei  # 安裝文泉驛微米黑（支持中文/粵語）
!fc-list | grep "wqy-microhei"  # 驗證字體是否安裝成功（會顯示字體路徑）
!pip install --upgrade openai-whisper  # 升級到最新版以支持粵語
!pip install openai-whisper google-api-python-client google-auth-oauthlib google-auth-httplib2 requests moviepy pydub pysrt

AutoUpYtGDrive = '/content/drive/MyDrive/山而王其/autoUpYtMP4/'
# ===============================================================
#                   🔰 1 掛載 Google Drive + 設定資料夾  🔰
# ===============================================================

# ===== 用colab密鑰避免api暴露 =====
from google.colab import userdata
from google.colab import drive
drive.mount('/content/drive')

import os, glob, subprocess, json, pickle
import requests, whisper

# ===== 設定資料夾 =====
AUDIO_FOLDER = AutoUpYtGDrive+"mp3"
m4a_files = glob.glob(os.path.join(AUDIO_FOLDER, "*.m4a"))

if not m4a_files:
    print("❌ 沒有 m4a，程式結束")
    raise SystemExit()

input_audio = m4a_files[0]
base_name = os.path.splitext(os.path.basename(input_audio))[0]
print("🎧 音訊檔：", input_audio)

# ===============================================================
#                   🔰 2 M4A → WAV  🔰
# ===============================================================
wav_path = f"/content/{base_name}.wav"
cmd = ["ffmpeg","-i",input_audio,"-ar","16000","-ac","1",wav_path]
subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("已轉成 wav：", wav_path)


# ===============================================================
#                   🔰 3 Whisper 生成字幕  🔰
# ===============================================================
model = whisper.load_model("small")
# result = model.transcribe(wav_path, language="yue")  # Whisper 對廣東話的標準語言代碼是 yue，而非是 zh（普通話）
result = model.transcribe(wav_path)  # 不指定language，自動識別
subtitle_text = result["text"]
segments = result["segments"]
print("識別結果：", subtitle_text)

# ===============================================================
#                   🔰 4 生成 SRT 字幕幕幕檔 🔰
# ===============================================================
# 將 SRT 保存到 Google Drive 便於手動編輯
srt_path = os.path.join(AUDIO_FOLDER, f"{base_name}.srt")  # 保存到 Drive 的 mp3 目錄
def sec_to_srt(t):
    h = int(t//3600)
    m = int((t%3600)//60)
    s = t%60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.',',')

with open(srt_path, "w", encoding="utf-8") as f:  # 確保 utf-8 編碼避免亂碼
    for i, seg in enumerate(segments, 1):
        f.write(f"{i}\n")
        f.write(f"{sec_to_srt(seg['start'])} --> {sec_to_srt(seg['end'])}\n")
        f.write(f"{seg['text'].strip()}\n\n")
print(f"生成初始 SRT（可編輯）：{srt_path}")

# ===============================================================
#                   🔰 新增：手動修改字幕流程 🔰
# ===============================================================
print("\n請手動修改字幕文件：")
print(f"路徑：{srt_path}")
print("修改步驟：")
print("1. 打開 Google Drive，找到上述路徑的 .srt 文件")
print("2. 右鍵選擇「打開方式」→「文本編輯器」")
print("3. 修正錯誤字幕後保存")
input("修改完成後，請在此處按 Enter 鍵繼續...")  # 等待用戶確認

# 重新讀取修改後的 SRT 文件
with open(srt_path, "r", encoding="utf-8") as f:
    modified_srt = f.read()
print("已加載修改後的字幕")





















# ===============================================================
#                   🔰 5 Pexels API 下載高清視頻 + 1:1高清處理 🔰
# ===============================================================
PEXELS_API_KEY = userdata.get('PEXELS_API_KEY')  # 不用改，和你原始代碼一致
headers = {"Authorization": PEXELS_API_KEY}
query = "street city night"  # 可修改成你的關鍵詞（比如你要的場景）
total_needed_duration = 0
downloaded_videos = []  # 存儲處理後的高清1:1視頻，和原始變量名一致，不用改
TARGET_SQUARE_RES = 1080  # 目標高清分辨率（1080=1080x1080，想小一點就改720）

# 獲取音頻時長（和你原始代碼一樣，不用改）
probe = subprocess.Popen(
    ["ffprobe","-v","quiet","-print_format","json","-show_format",wav_path],
    stdout=subprocess.PIPE
)
output = json.loads(probe.communicate()[0])
total_needed_duration = float(output["format"]["duration"])
print(f"需要填充的總時長：{total_needed_duration:.2f}秒")

# 創建臨時文件夾（自動創建，不用手動弄）
os.makedirs("/content/videos_temp/raw", exist_ok=True)
os.makedirs("/content/videos_temp/square_hd", exist_ok=True)
current_total = 0
page = 1

while current_total < total_needed_duration:
    # 調用Pexels API（和原始一樣，不用改）
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&page={page}"
    res = requests.get(url, headers=headers).json()
    
    if not res.get("videos"):
        print("❌ 沒有更多視頻可下載")
        break
    
    # 篩選Pexels最高清的視頻文件（優化核心，不用改）
    video_info = res["videos"][0]
    video_files = video_info["video_files"]
    video_files_sorted = sorted(video_files, key=lambda x: (x.get("width",0)*x.get("height",0)), reverse=True)
    best_video_file = video_files_sorted[0]
    video_url = best_video_file["link"]
    video_duration = video_info["duration"]
    video_width = best_video_file.get("width", 1920)
    video_height = best_video_file.get("height", 1080)
    print(f"📥 下載高清源視頻：{video_width}x{video_height}，時長{video_duration}秒")
    
    # 下載原始高清視頻
    raw_video_path = f"/content/videos_temp/raw/video_{page}_hd.mp4"
    !wget -q -O {raw_video_path} "{video_url}"
    
    # 1:1高清處理（優化核心，不用改）
    square_hd_video_path = f"/content/videos_temp/square_hd/video_{page}_square_hd.mp4"
    
    # 獲取原始視頻寬高
    probe = subprocess.Popen(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", raw_video_path],
        stdout=subprocess.PIPE
    )
    streams = json.loads(probe.communicate()[0])["streams"]
    video_stream = next(s for s in streams if s["codec_type"] == "video")
    width = video_stream["width"]
    height = video_stream["height"]
    
    # 高清裁剪/縮放邏輯
    if width >= TARGET_SQUARE_RES and height >= TARGET_SQUARE_RES:
        if width > height:
            crop_filter = f"crop={TARGET_SQUARE_RES}:{TARGET_SQUARE_RES}:(in_w-{TARGET_SQUARE_RES})/2:0"
        else:
            crop_filter = f"crop={TARGET_SQUARE_RES}:{TARGET_SQUARE_RES}:0:(in_h-{TARGET_SQUARE_RES})/2"
        filter_complex = crop_filter
    else:
        if width > height:
            crop_filter = f"crop={height}:{height}:(in_w-{height})/2:0"
        else:
            crop_filter = f"crop={width}:{width}:0:(in_h-{width})/2"
        scale_filter = f"scale={TARGET_SQUARE_RES}:{TARGET_SQUARE_RES}:flags=bicubic"
        filter_complex = f"{crop_filter},{scale_filter}"
    
    # 高清編碼參數（核心，不用改）
    cmd = [
        "ffmpeg", "-y", "-i", raw_video_path,
        "-vf", filter_complex,
        "-c:v", "libx264", "-crf", "18", "-preset", "slower",
        "-pix_fmt", "yuv420p", "-minrate", "5M", "-maxrate", "10M", "-bufsize", "10M",
        "-c:a", "aac", "-b:a", "320k",
        square_hd_video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"⚠️  第{page}個視頻處理失敗：", result.stderr)
        page += 1
        continue
    
    # 記錄視頻（和原始變量名一致，不用改）
    downloaded_videos.append({"path": square_hd_video_path, "duration": video_duration})
    current_total += video_duration
    print(f"✅ 已處理第{page}個高清1:1視頻（{TARGET_SQUARE_RES}x{TARGET_SQUARE_RES}），累計：{current_total:.2f}秒")
    
    page += 1












# ===============================================================
#                   🔰 6 拼接高清1:1視頻（避免二次壓縮）
# ===============================================================
concat_list = "/content/concat_list_hd.txt"
with open(concat_list, "w") as f:
    for video in downloaded_videos:  # 變量名和模塊5一致，不用改
        f.write(f"file '{video['path']}'\n")

concatenated_hd_video = "/content/concatenated_hd.mp4"  # 高清拼接後的視頻路徑
cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_list,
    "-c:v", "libx264", "-crf", "18", "-preset", "slower",  # 高清編碼
    "-c:a", "aac", "-b:a", "320k",
    concatenated_hd_video
]
result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if result.returncode != 0:
    print("❌ 高清視頻拼接錯誤：", result.stderr)
    raise SystemExit()
print(f"📼 高清1:1視頻拼接完成：{concatenated_hd_video}（{TARGET_SQUARE_RES}x{TARGET_SQUARE_RES}）")











# ===============================================================
#                   🔰 7 裁切拼接後的視頻到音頻時長 🔰
# ===============================================================
cut_video = "/content/cut_hd.mp4"  # 高清裁切後的視頻（改個名區分）
cmd = [
    "ffmpeg", "-y", "-i", concatenated_hd_video,  # 輸入：前面拼接後的高清1:1視頻
    "-t", str(total_needed_duration),  # 裁切到與音頻相同時長（不變）
    # 優化：高清編碼，避免裁切時畫質損失（替換原來的 copy）
    "-c:v", "libx264", "-crf", "18", "-preset", "slower",
    "-c:a", "aac", "-b:a", "320k",  # 音頻也保持高清
    cut_video
]
subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(f"✅ 高清視頻裁切完成（匹配音頻時長{total_needed_duration:.2f}秒）")


# ===============================================================
#                   🔰 8 合併音訊到影片 🔰
# ===============================================================
merged_video = f"/content/{base_name}_merged_hd.mp4"  # 高清合併後的視頻
cmd = [
    "ffmpeg", "-y", "-i", cut_video,  # 輸入：高清裁切後的視頻
    "-i", wav_path,  # 你的音頻文件（不變）
    "-map", "0:v:0", "-map", "1:a:0",  # 音視頻映射（不變）
    # 優化：高清編碼，避免合併時畫質壓縮（替換原來的 copy）
    "-c:v", "libx264", "-crf", "18", "-preset", "slower",
    "-c:a", "aac", "-b:a", "320k",
    merged_video
]
subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("✅ 高清音頻合併完成：", merged_video)

# ===============================================================
#                   🔰 9 燒錄字幕（硬字幕） 🔰
# ===============================================================
final_video = f"/content/{base_name}_final_hd.mp4"  # 最終高清視頻（帶字幕）
cmd = [
    "ffmpeg", "-y", "-i", merged_video,  # 輸入：高清合併音頻後的視頻
    # 優化：字體大小從20→48（適配1080x1080高清，若改720分辨率則設為36）
    "-vf", f"subtitles={srt_path}:force_style='FontSize=48,FontName=WenQuanYi Micro Hei,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=3'",
    # 優化：最後一步仍保持高清，避免字幕燒錄時模糊
    "-c:v", "libx264", "-crf", "18", "-preset", "slower",
    "-c:a", "copy",  # 音頻已高清，直接複製
    final_video
]
subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("✅ 高清字幕燒錄完成：", final_video)

# ===============================================================
#                   🔰 10 自動上傳 YouTube 🔰
# ===============================================================
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import pickle  # 補充：確保導入pickle（避免報錯）

CLIENT_SECRETS_FILE = AutoUpYtGDrive+"secret/client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PICKLE = AutoUpYtGDrive+"secret/token.pickle"

credentials = None

# 檢查已有的 token.pickle（包含 refresh token）
if os.path.exists(TOKEN_PICKLE):
    with open(TOKEN_PICKLE, "rb") as f:
        credentials = pickle.load(f)

# 如果憑證過期或無效，自動刷新
if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_console()
    # 保存刷新後的憑證
    with open(TOKEN_PICKLE, "wb") as f:
        pickle.dump(credentials, f)

# 構建 YouTube 客戶端
youtube = build("youtube", "v3", credentials=credentials)

# 上傳視頻（關鍵：視頻路徑改為上面的 final_video，即高清帶字幕視頻）
request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {"title": base_name, "description": "AI 自動化上傳影片"},
        "status": {"privacyStatus": "public"}  # 可改為 "private" 或 "unlisted"
    },
    media_body=MediaFileUpload(final_video)  # 這裡用高清最終視頻
)
response = request.execute()
print(f'✅ 已上傳 YouTube（高清1:1）：https://www.youtube.com/watch?v={response["id"]}')