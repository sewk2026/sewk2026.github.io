'''
海螺 txt版 202512061358

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
#                   🔰 -1 環境準備  🔰
# ===============================================================
!apt-get install -y fonts-wqy-microhei  # 安裝文泉驛微米黑（支持中文/粵語）
!fc-list | grep "wqy-microhei"  # 驗證字體是否安裝成功（會顯示字體路徑）
!pip install --upgrade openai-whisper  # 升級到最新版以支持粵語
!pip install openai-whisper google-api-python-client google-auth-oauthlib google-auth-httplib2 requests moviepy pydub pysrt


# ===============================================================
#                   🔰 0 admin setting  🔰
# ===============================================================

# Drive資料夾
Drive根資料夾 = '/content/drive/MyDrive/山而王其/'
User資料夾 = '錄音'
AutoUpYtGDrive = Drive根資料夾 + User資料夾 + '/'


# Pexels 下載影片關鍵詞
query = "street city night"  # 可修改關鍵詞
print('='*18)
print(f"2: 請填寫您的需要下載的影片材料關鍵詞 沒填用預設值[ {query} ]")
答 = input("填寫 影片材料關鍵詞 後，請在此處按 Enter 鍵繼續...")
if 答:
    query = 答
    print(f"✅ 已使用自訂值：{答}")
    
else:
    print(f"✅ 未輸入，使用預設值：{query}")


# youtube description / tag
YoutubeDescription = '''
#香港男人覺醒
#中年港男翻身
#香港中年危機 
#大叔自救計劃
#中年逆襲
#男人成長
#男性提升
#情感成長
#吸引力提升
#真實男人的故事
#香港創作者
#廣東話男性話題
#粵語男性心法
#山而王其
'''  # 可修改 description / tag
print('='*18)
print(f"2: 請填寫您的影片描述 / tag， 沒填用預設值[ {YoutubeDescription} ]")
答 = input("填寫 影片描述 後，請在此處按 Enter 鍵繼續...")
if 答:
    YoutubeDescription = 答
    print(f"✅ 已使用自訂值：{答}")
    
else:
    print(f"✅ 未輸入，使用預設值：{YoutubeDescription}")




# ===============================================================
#                   🔰 1 掛載 Google Drive + 設定資料夾  🔰
# ===============================================================

# ===== 用colab密鑰避免api暴露 =====
from google.colab import userdata
from google.colab import drive
drive.mount('/content/drive')

import os, glob, subprocess, json, pickle
import requests, whisper

'''
# ===== 設定資料夾 =====
AUDIO_FOLDER = AutoUpYtGDrive+"錄音"
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
# 移除强制单声道和采样率，保留原始音频属性（避免失真）
cmd = [
    "ffmpeg", "-y", "-i", input_audio,
    #"-filter:a", "rubberband=transposition=-2",  # 降低2个key（-2 = 降2个半音）
    "-ar", "16000", "-ac", "1",  # 保持采样率和声道设置（如需保留原始可移除）
    wav_path
    ]  # 移除 -ar 16000 -ac 1
subprocess.run(cmd, check=True)  # 增加check=True，出错时直接报错

# 转换后检查WAV文件
if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 1024:
    print("❌ WAV文件生成失败！")
    raise SystemExit()
print("主音訊直接使用原始 wav：", wav_path)
'''






# ===============================================================
#                   🔰 2 文字轉海螺ai語音  🔰
# ===============================================================

print('='*18)
print(f"1: 請填寫您的文稿 將自動轉ai語音")
答 = input("填寫文稿後，請在此處按 Enter 鍵繼續...").strip()

import requests
import base64
import whisper

def generate_wav_tts(text):

    url = "https://api.minimax.chat/v1/text-to-speech/synthesize"
    group_id = "1996944212859298102"  # 從API Key解析出的Group ID

    api_key = userdata.get("海螺_API")
    voice_id = userdata.get("海螺VOICE_ID")


    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Group-ID": group_id  # 補充必需的Group-ID頭
    }

    payload = {
        "model": "speech-01",
        "text": text,
        "voice_setting": {
            "voice_id": voice_id,
            "lang": "yue",
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0
        },
        "audio_setting": {
            "format": "wav",  # wav / mp3 / flac
            "sample_rate": 32000,
            "channel": 1
        },
        "stream": False  # 非串流一次生成
    }

    print("⏳ 正在向 MiniMax 中國區請求語音合成...")

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()  # 拋出HTTP錯誤
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP錯誤: {str(e)}")
        print("響應內容:", resp.text)
        return None
    except Exception as e:
        print(f"❌ 請求失敗: {str(e)}")
        return None

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("❌ 無效的JSON回應")
        print("回應內容:", resp.text)
        return None

    # 檢查API業務碼
    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code") != 0:
        print(f"❌ 業務錯誤: {base_resp.get('status_msg', '未知錯誤')}")
        return None

    audio_hex = data.get("data", {}).get("audio")
    if not audio_hex:
        print("❌ 未返回音頻數據")
        print("完整回應:", data)
        return None
    # 保存音頻文件
    try:
        audio_bytes = bytes.fromhex(audio_hex)
        with open("output.wav", "wb") as f:
            f.write(audio_bytes)
        print("🎉 音頻生成成功: output.wav")
        return "output.wav"
    except Exception as e:
        print(f"❌ 保存音頻失敗: {str(e)}")
        return None
    
wav_path = generate_wav_tts(答)

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
#                   🔰 5 手動修改字幕流程 🔰
# ===============================================================
print('='*18)
print("請手動修改字幕文件：")
# 强调保存路径
print(f"⚠️ 請確保修改後保存到該路徑：{os.path.abspath(srt_path)}")
print("修改步驟：")
print("1. 打開 Google Drive，找到上述路徑的 .srt 文件")
print("2. 右鍵選擇「打開方式」→「文本編輯器」")
print("3. 修正錯誤字幕後保存")
input("修改完成後，請在此處按 Enter 鍵繼續...")  # 等待用戶確認

# 直接读取修改后的SRT（删除重复写回的代码）
with open(srt_path, "r", encoding="utf-8") as f:
    modified_srt = f.read()
# 验证是否读取到修改内容（打印前2行）
print("修改後的字幕前5行：")
print("\n".join(modified_srt.split("\n")[:5]))
print("已加載修改後的字幕")


# ===============================================================
#     🔰 6 Pexels 影片下載（支援 2 把 API Key 自動輪替） 🔰
# ===============================================================

# 讀取可用的 key（支援你現在的兩個 key 名字）
PEXELS_KEYS = []

k0 = userdata.get("PEXELS_API_KEY")
if k0:
    PEXELS_KEYS.append(k0)

k1 = userdata.get("PEXELS_API_KEY_1")
if k1:
    PEXELS_KEYS.append(k1)

if not PEXELS_KEYS:
    raise SystemExit("❌ 沒有設定 PEXELS_API_KEY 或 PEXELS_API_KEY_1")

print(f"🔑 已載入 {len(PEXELS_KEYS)} 個 Pexels API Key：", PEXELS_KEYS)

# 目前使用的 Key index
key_index = 0
def get_headers():
    """回傳目前 Key"""
    return {"Authorization": PEXELS_KEYS[key_index]}

def rotate_key():
    """輪替到下一把 Key"""
    global key_index
    key_index = (key_index + 1) % len(PEXELS_KEYS)
    print(f"🔁 已切換到 API Key #{key_index+1}")

# 自動計算音訊時長
audio_probe = subprocess.Popen(
    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", wav_path],
    stdout=subprocess.PIPE
)
audio_info = json.loads(audio_probe.communicate()[0])
total_needed_duration = float(audio_info["format"]["duration"])
print(f"需要影片總時長：{total_needed_duration:.2f} 秒")

os.makedirs("/content/videos_temp/raw", exist_ok=True)
os.makedirs("/content/videos_temp/square", exist_ok=True)

current_total = 0
page = 1
downloaded_videos = []

# ===============================================================
#                 🔁 循環下載，直到長度足夠
# ===============================================================
while current_total < total_needed_duration:

    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&page={page}"

    try:
        res = requests.get(url, headers=get_headers(), timeout=12)

        if res.status_code == 429:
            print("⚠️ API 用量超額 → 自動切換 Key")
            rotate_key()
            continue

        data = res.json()

    except Exception as e:
        print("❌ API 呼叫錯誤 → 切換 Key", e)
        rotate_key()
        continue

    # 沒影片 → 換下一頁
    if not data.get("videos"):
        print("⚠️ 找不到影片，換下一頁")
        page += 1
        continue

    # 取第一部影片
    video_info = data["videos"][0]
    video_file = video_info["video_files"][0]
    video_url = video_file["link"]
    video_duration = video_info["duration"]

    raw_video_path = f"/content/videos_temp/raw/video_{page}.mp4"
    !wget -q -O {raw_video_path} "{video_url}"

    # =========================================================
    #    🔰 7 將影片裁剪成 1:1（避免拼接錯誤）🔰
    # =========================================================
    square_video_path = f"/content/videos_temp/square/video_{page}_square.mp4"

    probe = subprocess.Popen(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", raw_video_path],
        stdout=subprocess.PIPE
    )
    streams = json.loads(probe.communicate()[0])["streams"]
    video_stream = next(s for s in streams if s["codec_type"] == "video")

    width = video_stream["width"]
    height = video_stream["height"]

    if width > height:
        crop_filter = f"crop={height}:{height}:(in_w-{height})/2:0"
    else:
        crop_filter = f"crop={width}:{width}:0:(in_h-{width})/2"

    subprocess.run([
        "ffmpeg", "-y", "-i", raw_video_path,
        "-vf", crop_filter,
        "-c:v", "libx264", "-crf", "23",
        "-c:a", "copy",
        square_video_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    downloaded_videos.append({"path": square_video_path, "duration": video_duration})
    current_total += video_duration

    print(f"📥 已處理 {page} 號影片（{video_duration}s），累計：{current_total:.2f}s")

    page += 1

# ===============================================================
#                   🔰 8 拼接多個1:1視頻 🔰
# ===============================================================
concat_list = "/content/concat_list.txt"
with open(concat_list, "w") as f:
    for video in downloaded_videos:
        f.write(f"file '{video['path']}'\n")

concatenated_video = "/content/concatenated.mp4"
cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_list,
    "-c:v", "copy", "-c:a", "copy",  # 直接複製（因已統一編碼）
    concatenated_video
]
result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode != 0:
    print("視頻拼接錯誤：", result.stderr.decode())
    raise SystemExit()
print(f"1:1視頻拼接完成：{concatenated_video}")

# ===============================================================
#                   🔰 9 裁切拼接後的視頻到音頻時長 🔰
# ===============================================================
cut_video = "/content/cut.mp4"
cmd = [
    "ffmpeg", "-i", concatenated_video,
    "-t", str(total_needed_duration),  # 裁切到與音頻相同時長
    "-c:v", "copy", "-c:a", "copy",
    cut_video
]
subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(f"視頻裁切完成（匹配音頻時長{total_needed_duration:.2f}秒）")

# ===============================================================
#                   🔰 10 合併音訊到影片 🔰
# ===============================================================
merged_video = f"/content/{base_name}_merged.mp4"
cmd = [
    "ffmpeg", "-y", "-i", cut_video, "-i", wav_path,
    "-map", "0:v", "-map", "1:a",
    "-c:v", "copy", 
    "-c:a", "aac", "-b:a", "192k",  # 指定音频比特率192k
    merged_video
]
subprocess.run(cmd, check=True, capture_output=True)
print("影片合成完成：", merged_video)

# ===============================================================
#                   🔰 11 燒錄字幕（硬字幕） 🔰
# ===============================================================
final_video = f"/content/{base_name}_final.mp4"
# 确认SRT文件存在且路径正确
if not os.path.exists(srt_path):
    print(f"❌ 找不到字幕文件：{srt_path}")
    raise SystemExit()
# 打印实际使用的字幕路径
print(f"使用字幕文件：{os.path.abspath(srt_path)}")
cmd = [
    "ffmpeg", "-y", "-i", merged_video,
    "-vf", f"subtitles={srt_path}:force_style='Fontsize=20,FontName=WenQuanYi Micro Hei'",
    "-c:a", "copy",
    final_video
]
subprocess.run(cmd, check=True, capture_output=True)
print("字幕已燒錄：", final_video)

# ===============================================================
#            🔰 12 重新設計的片頭 + 主影片 + 片尾合成 🔰
# ===============================================================


import subprocess

print("\n=================【開始 第12部分：片頭片尾合成】=================\n")

# 你的片頭片尾來源
INTRO_SRC = Drive根資料夾 + "料/start.mp4"
OUTRO_SRC = Drive根資料夾 + "料/end.mp4"

# 轉成 1:1 + 淡入淡出後的輸出
INTRO_11 = "/content/intro_1by1.mp4"
OUTRO_11 = "/content/outro_1by1.mp4"

INTRO_FADED = "/content/intro_faded.mp4"
MAIN_FADED = "/content/main_faded.mp4"
OUTRO_FADED = "/content/outro_faded.mp4"

FINAL_COMBINED = "/content/final_with_intro_outro.mp4"

# ========== 工具函式：安全執行 ffmpeg ==========
def run_ffmpeg(cmd, desc):
    print(f"\n▶ {desc}")
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        print(p.stderr.decode())
        raise SystemExit(f"❌ ffmpeg 錯誤：{desc}")
    else:
        print("✓ 完成")

# ========== 工具函式：裁成 1:1 ==========
def convert_to_square(src, dst):
    # 用 crop 搭配最穩定的 cover 模式（不使用 ffmpeg 5 才有的 keyword）
    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-vf", "crop='min(in_w, in_h)':'min(in_w, in_h)'",
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
        "-c:a", "aac",
        dst
    ]
    run_ffmpeg(cmd, f"裁成 1:1 → {dst}")

# ========== 工具函式：淡入淡出 ==========
def fade_in_out(src, dst, fadein=0.8, fadeout=0.8):
    # 取影片長度
    probe = subprocess.Popen(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", src],
        stdout=subprocess.PIPE
    )
    info = json.loads(probe.communicate()[0])
    duration = float(info["format"]["duration"])
    fadeout_start = duration - fadeout

    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-vf", f"fade=t=in:st=0:d={fadein},fade=t=out:st={fadeout_start}:d={fadeout}",
        "-af", f"afade=t=in:st=0:d={fadein},afade=t=out:st={fadeout_start}:d={fadeout}",
        "-c:v", "libx264", "-preset", "veryfast",
        "-c:a", "aac",
        dst
    ]
    run_ffmpeg(cmd, f"淡入淡出 → {dst}")

# ========== 工具函式：淡入（主影片） ==========
def fade_only_in(src, dst, fadein=0.8):
    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-vf", f"fade=t=in:st=0:d={fadein}",
        "-af", f"afade=t=in:st=0:d={fadein}",
        "-c:v", "libx264", "-preset", "veryfast",
        "-c:a", "aac",
        dst
    ]
    run_ffmpeg(cmd, f"主影片淡入 → {dst}")


# ===============================================================
#                   Step 1：轉成 1:1
# ===============================================================
convert_to_square(INTRO_SRC, INTRO_11)
convert_to_square(final_video, MAIN_FADED.replace("_faded", "_1by1"))  # temp
convert_to_square(OUTRO_SRC, OUTRO_11)

# 重新指定主影片 1:1 路徑
MAIN_11 = MAIN_FADED.replace("_faded", "_1by1")

# ===============================================================
#                   Step 2：套用淡入淡出
# ===============================================================
fade_in_out(INTRO_11, INTRO_FADED)
fade_only_in(MAIN_11, MAIN_FADED)
fade_in_out(OUTRO_11, OUTRO_FADED)

# ===============================================================
#                   Step 3：拼接 intro → main → outro
# ===============================================================
concat_txt = "/content/concat_intro_main_outro.txt"
with open(concat_txt, "w") as f:
    f.write(f"file '{INTRO_FADED}'\n")
    f.write(f"file '{MAIN_FADED}'\n")
    f.write(f"file '{OUTRO_FADED}'\n")

run_ffmpeg([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_txt,
    "-c:v", "libx264", "-c:a", "aac",
    FINAL_COMBINED
], "拼接 final_with_intro_outro.mp4")

print("\n🎬【片頭 + 主影片 + 片尾】全部完成！")
print("最終輸出：", FINAL_COMBINED)

# 更新上傳用檔案
final_video = FINAL_COMBINED

# ===============================================================
#                   🔰 13 自動上傳 YouTube 🔰
# ===============================================================
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request  # 新增：用於刷新令牌

CLIENT_SECRETS_FILE = Drive根資料夾 + "secret/client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PICKLE = Drive根資料夾 + "secret/token.pickle"

credentials = None

# 檢查已有的 token.pickle（包含 refresh token）
if os.path.exists(TOKEN_PICKLE):
    with open(TOKEN_PICKLE, "rb") as f:
        credentials = pickle.load(f)

# 如果憑證過期或無效，自動刷新
if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
        # 自動刷新令牌（無需手動操作）
        credentials.refresh(Request())
    else:
        # 僅第一次需要手動授權（如果 token.pickle 不存在）
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        # Colab 中用 run_console 替代（需手動一次，之後複用）
        credentials = flow.run_console()
    # 保存刷新後的憑證
    with open(TOKEN_PICKLE, "wb") as f:
        pickle.dump(credentials, f)

# 構建 YouTube 客戶端
youtube = build("youtube", "v3", credentials=credentials)

# 上傳視頻
request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {"title": base_name, "description": YoutubeDescription},
        "status": {"privacyStatus": "public"}  # 可改為 "private" 或 "unlisted"
    },
    media_body=MediaFileUpload(final_video)
)
response = request.execute()
print(f'✅ 已上傳 YouTube：https://www.youtube.com/watch?v={response["id"]}')