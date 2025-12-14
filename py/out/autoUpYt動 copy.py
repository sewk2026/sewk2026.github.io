"""
Colab 可直接執行的 Python 腳本：
功能：
1) 填寫影片描述（互動式輸入）
2) 把 「徬白.m4a」合併到「主影片.mp4」（若長度不同：超出截斷、不足補靜音）
3) 使用 Whisper 生成 SRT，並保存到 Google Drive（可手動編輯）
4) 把 bg1.mp3 加入到主影片（不足則循環、音量降為 10%、淡入淡出）
5) 將 start.mp4 + 主影片 + end.mp4 合成一個影片
6) 將最終影片上傳到 YouTube（需 client_secret.json 與第一次互動授權）

說明：請把檔案放在 Google Drive：
- 動畫 資料夾 (影片與人聲)：/content/drive/MyDrive/山而王其/動畫/集/  -> 包含 主影片.mp4 與 徬白.m4a
- 材質 資料夾 (片頭片尾、bg)：/content/drive/MyDrive/山而王其/動畫/料/  -> 包含 start.mp4 end.mp4 bg1.mp3
- YouTube OAuth secret 放在：/content/drive/MyDrive/山而王其/autoUpYtMP4/secret/client_secret.json

執行方法：
1. 在 Google Colab 新增一個 code cell，把此檔案上傳或直接載入，然後執行：
   !python3 colab_auto_publish_to_youtube.py

注意：第一次上傳 YouTube 會跳出授權步驟（請照指示完成），之後會在同路徑產生 token.pickle 可重複使用。

"""

# -------------- 套件安裝（Colab 執行） --------------
# 在 Colab 執行本檔時，會先安裝必要套件
import os
import sys
import subprocess
import json
import glob
import time

# 只在 Colab 環境下安裝（如果你在本機執行，請自行安裝）
try:
    import google.colab  # type: ignore
    IN_COLAB = True
except Exception:
    IN_COLAB = False

if IN_COLAB:
    print('在 Colab 環境，安裝必要套件與中文字型...')

    # 安裝 Python 套件
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', '--quiet',
        'openai-whisper',
        'google-api-python-client',
        'google-auth-oauthlib',
        'google-auth-httplib2',
        'requests',
        'pydub'
    ], check=False)

    # 安裝能顯示中文的 Noto CJK 字型（避免字幕亂碼 □□□）
    subprocess.run([
        'apt-get', 'install', '-y', 'fonts-noto-cjk'
    ])

# -------------- 參數設定（請確認 Drive 路徑） --------------
DRIVE_BASE = '/content/drive/MyDrive/山而王其/動畫'
FOLDER_ANIMATION = os.path.join(DRIVE_BASE, '集') + '/'     # 主影片與語音
FOLDER_MATERIAL = os.path.join(DRIVE_BASE, '料') + '/'     # start,end,bg
FOLDER_SECRET = '/content/drive/MyDrive/山而王其/autoUpYtMP4/secret/'     # 放 client_secret.json

# 互動：讓使用者輸入 description（可直接在 Colab 輸入）
預設描述 = '''
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
'''
print('\n請確認下列 Google Drive 資料夾是否存在：')
print('集 資料夾：', FOLDER_ANIMATION)
print('料 資料夾：', FOLDER_MATERIAL)
print('secret 資料夾：', FOLDER_SECRET)
input_desc = input('\n請輸入 YouTube 影片描述（或按 Enter 使用預設）：\n'+預設描述).strip()
if not input_desc:
    input_desc = 預設描述

# 檔名（你指定的固定檔名）
#MAIN_VIDEO = os.path.join(FOLDER_ANIMATION, '主影片.mp4')
#VOICE_M4A = os.path.join(FOLDER_ANIMATION, '徬白.m4a')

# 自動尋找最新的主影片與語音檔
# -------------- Step A：掛載 Drive（如果在 Colab） --------------
if IN_COLAB:
    from google.colab import drive
    drive.mount('/content/drive')

m4a_files = glob.glob(os.path.join(FOLDER_ANIMATION, "*.m4a"))
if not m4a_files:
    print("❌ 沒有 m4a，程式結束")
    raise SystemExit()
input_audio = m4a_files[0]
VOICE_M4A = input_audio       
print("🎧 音訊檔：", VOICE_M4A)

mp4_files = glob.glob(os.path.join(FOLDER_ANIMATION, "*.mp4"))
if not mp4_files:
    print("❌ 沒有 mp4，程式結束")
    raise SystemExit()
input_mp4 = mp4_files[0]
MAIN_VIDEO = input_mp4        
print("🎧 影片檔：", MAIN_VIDEO)

START_MP4 = os.path.join(FOLDER_MATERIAL, 'start.mp4')
END_MP4 = os.path.join(FOLDER_MATERIAL, 'end.mp4')
BG_MP3 = os.path.join(FOLDER_MATERIAL, 'bg1.mp3')

# 驗證檔案存在
for p in [MAIN_VIDEO, VOICE_M4A, START_MP4, END_MP4, BG_MP3]:
    if not os.path.exists(p):
        print(f'❌ 找不到檔案：{p}，請檢查路徑與檔名（注意中文/空格）')
        sys.exit(1)

# -------------- 工具函式 --------------

def run(cmd):
    print('▶', ' '.join(str(x) for x in cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        print('ffmpeg/命令錯誤：', p.stderr.decode('utf-8', errors='ignore'))
        raise SystemExit('執行失敗')
    return p


def ffprobe_duration(path):
    p = subprocess.run(['ffprobe','-v','quiet','-print_format','json','-show_format', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = json.loads(p.stdout)
    return float(info['format']['duration'])


# -------------- Step 1：取得主影片長度 --------------
print('\n== 取得主影片長度 ==')
main_duration = ffprobe_duration(MAIN_VIDEO)
print(f'主影片長度：{main_duration:.2f} 秒')

# -------------- Step 2：處理語音（m4a → padded wav） --------------
print('\n== 處理語音：將 徬白.m4a 轉為與主影片相同長度，短則補靜音、長則截斷 ==')
VOICE_WAV = '/content/dialogue.wav'
# 使用 apad 補靜音並以 -t 截長度
run(['ffmpeg','-y','-i', VOICE_M4A, '-af','apad', '-t', str(main_duration), '-ar','44100','-ac','2', VOICE_WAV])
print('語音已輸出為：', VOICE_WAV)

# -------------- Step 3：使用 Whisper 生成 SRT 字幕，並保存到 Drive --------------
print('\n== 使用 Whisper 生成字幕（SRT） ==')
try:
    import whisper
except Exception:
    print('未安裝 whisper，請在 Colab 中重新執行以安裝套件')
    sys.exit(1)

model = whisper.load_model('medium')
res = model.transcribe(VOICE_WAV)
segments = res.get('segments', [])
# 產生 SRT
srt_path = os.path.join(FOLDER_ANIMATION, '主影片.srt')

def sec_to_srt(t):
    h = int(t//3600)
    m = int((t%3600)//60)
    s = t%60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.',',')

with open(srt_path, 'w', encoding='utf-8') as f:
    for i, seg in enumerate(segments, start=1):
        f.write(f"{i}\n")
        f.write(f"{sec_to_srt(seg['start'])} --> {sec_to_srt(seg['end'])}\n")
        f.write(seg['text'].strip().replace('-->','−') + '\n\n')
print('='*18)
print('已生成 SRT 並保存到：', srt_path)
print("請手動修改字幕文件：")
input("修改完成後，請在此處按 Enter 鍵繼續...")  # 等待用戶確認

# -------------- Step 4：處理背景音 bg1.mp3（循環、音量 10%、淡入淡出） --------------
print('\n== 處理背景音：循環至目標長度，音量降到 10%，並做淡入淡出 ==')
BG_LOOPED = '/content/bg_looped.mp3'
# 使用 -stream_loop -1 來循環，並使用 -t 限制長度
fade_dur = 1.0
fade_out_start = max(0, main_duration - fade_dur)
run(['ffmpeg','-y','-stream_loop','-1','-i', BG_MP3, '-t', str(main_duration), '-af', f"volume=0.1,afade=t=in:st=0:d={fade_dur},afade=t=out:st={fade_out_start}:d={fade_dur}", BG_LOOPED])
print('已產生循環並淡入淡出的背景音：', BG_LOOPED)

# -------------- Step 5：合併語音與背景音（混音） --------------
print('\n== 將語音與背景音混音（bg在10%） ==')
COMBINED_AUDIO = '/content/combined_audio.m4a'
# amix 將兩軌混合，使用 duration=first 以主語音為準
run(['ffmpeg','-y','-i', VOICE_WAV, '-i', BG_LOOPED, '-filter_complex', 'amix=inputs=2:duration=first:dropout_transition=2', '-c:a','aac','-b:a','192k', COMBINED_AUDIO])
print('混音完成：', COMBINED_AUDIO)

# -------------- Step 6：把混合好的音軌替換到主影片 --------------
print('\n== 把混音音軌放到主影片（保留原始影片畫面） ==')
MAIN_WITH_AUDIO = '/content/main_with_audio.mp4'
run(['ffmpeg','-y','-i', MAIN_VIDEO, '-i', COMBINED_AUDIO, '-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-shortest', MAIN_WITH_AUDIO])
print('主影片已加入音軌：', MAIN_WITH_AUDIO)




















# -------------- Step 7：把 SRT 硬燒回主影片（最终修复版：纯英文路径+文件校验） --------------
import subprocess
import json

def get_video_height(video_path):
    """取得影片高度（用 ffprobe）"""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = json.loads(result.stdout)

    for stream in info["streams"]:
        if stream["codec_type"] == "video":
            return int(stream["height"])
    return 1080   # fallback 預設 1080p

# ========== 修复1：重新挂载Drive（新版Colab原生方式） ==========
if IN_COLAB:
    print("\n🔄 重新挂载Google Drive，刷新缓存...")
    from google.colab import drive
    # 强制重新挂载（覆盖旧缓存）
    drive.mount('/content/drive', force_remount=True)
    time.sleep(2)

# ========== 修复2：校验原始SRT文件是否存在+内容 ==========
print("\n📝 校验Drive中的原始字幕文件：")
if not os.path.exists(srt_path):
    print(f"❌ 原始SRT文件不存在：{srt_path}")
    sys.exit(1)

# 打印最后3行确认内容
try:
    with open(srt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"✅ 原始SRT文件存在，最后3行内容：")
        print(''.join(lines[-3:]) if len(lines)>=3 else ''.join(lines))
except Exception as e:
    print(f"❌ 读取原始SRT失败：{e}")
    sys.exit(1)

# ========== 修复3：复制到本地+纯英文文件名（彻底解决中文路径问题） ==========
# 改用纯英文文件名，避免ffmpeg解析中文失败
LOCAL_SRT = "/content/main_subs_modified.srt"  # 纯英文路径
print(f"\n📌 复制Drive SRT到本地纯英文路径：{srt_path} → {LOCAL_SRT}")
# 强制复制并覆盖旧文件
copy_cmd = ["cp", "-f", srt_path, LOCAL_SRT]
copy_result = subprocess.run(copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if copy_result.returncode != 0:
    print(f"❌ 复制SRT失败：{copy_result.stderr.decode('utf-8')}")
    sys.exit(1)

# 校验本地SRT是否存在
if not os.path.exists(LOCAL_SRT):
    print(f"❌ 本地SRT文件不存在：{LOCAL_SRT}")
    sys.exit(1)
print(f"✅ 本地SRT文件已创建：{LOCAL_SRT}")

# ========== 修复4：适配1080x1080的字幕大小 ==========
print("\n== 适配1080x1080视频的字幕大小 ==")
video_height = get_video_height(MAIN_WITH_AUDIO)
# 1080x1080正方形视频：2.5%比例，最大27px，最小16px
fontsize = max(16, min(27, int(video_height * 0.025)))  
print(f"主影片高度：{video_height}px → 字幕字体大小：{fontsize}px")

# 带字幕的主影片输出路径（纯英文）
MAIN_WITH_AUDIO_AND_SUBS = "/content/main_with_audio_and_subs.mp4"

# ========== 修复5：调整ffmpeg字幕参数（兼容格式） ==========
print("\n== 硬烧字幕到主影片（使用本地纯英文SRT） ==")
# 关键：subtitles滤镜的样式参数改用双引号包裹，避免转义冲突
sub_filter = (
    f"subtitles={LOCAL_SRT}:force_style="
    f"'Fontname=Noto Sans CJK TC,Fontsize={fontsize},"
    f"PrimaryColour=&HFFFFE5&,OutlineColour=&HA04000&,"
    f"BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=40'"
)

# 构建ffmpeg命令（简化路径，无中文）
ffmpeg_cmd = [
    "ffmpeg", "-y",  # 覆盖输出文件
    "-i", MAIN_WITH_AUDIO,  # 输入主影片
    "-vf", sub_filter,      # 字幕滤镜（纯英文路径）
    "-c:a", "copy",         # 音频直接复制，不重新编码
    "-c:v", "libx264",      # 视频编码确保兼容性
    "-crf", "23",           # 视频质量（平衡大小和画质）
    MAIN_WITH_AUDIO_AND_SUBS  # 输出文件
]

# 执行ffmpeg命令并打印详细日志
print("▶ 执行ffmpeg命令：", ' '.join(ffmpeg_cmd))
ffmpeg_result = subprocess.run(
    ffmpeg_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# 检查执行结果
if ffmpeg_result.returncode != 0:
    print(f"❌ ffmpeg执行失败：")
    print(f"标准错误：{ffmpeg_result.stderr}")
    sys.exit(1)
else:
    print(f"✅ 字幕烧录成功！输出文件：{MAIN_WITH_AUDIO_AND_SUBS}")
    # 校验输出文件是否存在
    if os.path.exists(MAIN_WITH_AUDIO_AND_SUBS):
        print(f"✅ 最终带字幕主影片已生成：{MAIN_WITH_AUDIO_AND_SUBS}")
    else:
        print(f"❌ 输出文件不存在：{MAIN_WITH_AUDIO_AND_SUBS}")
        sys.exit(1)


















# -------------- Step 8：將 start + 帶字幕的主影片 + end 合併為最終影片 --------------
print('\n== 合併 start.mp4 + 帶字幕的主影片 + end.mp4 ==')
FINAL_OUTPUT = '/content/final_combined.mp4'
# 使用 concat filter 拼接片头、帶字幕的主影片、片尾
run([
    'ffmpeg','-y',
    '-i', START_MP4,
    '-i', MAIN_WITH_AUDIO_AND_SUBS,  # 輸入改為帶字幕的主影片
    '-i', END_MP4,
    '-filter_complex', f"[0:v:0][0:a:0][1:v:0][1:a:0][2:v:0][2:a:0]concat=n=3:v=1:a=1[outv][outa]",
    '-map','[outv]','-map','[outa]','-c:v','libx264','-c:a','aac', FINAL_OUTPUT
])
input(f'最終影片輸出完成，檢查完成按 Enter 鍵： \n{FINAL_OUTPUT}')

# -------------- Step 9：上傳到 YouTube（需要 client_secret.json） --------------
print('\n== 上傳到 YouTube（OAuth） ==')
CLIENT_SECRET_PATH = os.path.join(FOLDER_SECRET, 'client_secret.json')
TOKEN_PICKLE = os.path.join(FOLDER_SECRET, 'token.pickle')
if not os.path.exists(CLIENT_SECRET_PATH):
    print('❌ 找不到 YouTube client_secret.json，請放到：', CLIENT_SECRET_PATH)
    print('請參考 Google Cloud Console 建立 OAuth 用戶端，並將 client_secret.json 上傳到該路徑')
    sys.exit(1)

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
creds = None
if os.path.exists(TOKEN_PICKLE):
    with open(TOKEN_PICKLE, 'rb') as f:
        creds = pickle.load(f)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        # 在 Colab 中使用 console flow（第一階段需要你貼 code）
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
        creds = flow.run_console()
    with open(TOKEN_PICKLE, 'wb') as f:
        pickle.dump(creds, f)

youtube = build('youtube', 'v3', credentials=creds)

# 上傳檔案（改為上傳最終合併後的影片）
media = MediaFileUpload(FINAL_OUTPUT, chunksize=-1, resumable=True)
request = youtube.videos().insert(
    part='snippet,status',
    body={
        'snippet': {
            'title': os.path.splitext(os.path.basename(MAIN_VIDEO))[0],
            'description': input_desc,
        },
        'status': {
            'privacyStatus': 'public'
        }
    },
    media_body=media
)

response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print('已上傳：%.1f%%' % (status.progress() * 100))

print('✅ 上傳完成，YouTube 影片 ID：', response.get('id'))
print('影片網址：https://www.youtube.com/watch?v=' + response.get('id'))

print('\n全部流程完成 ✅')