'''

202512092050

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
並上傳到 Google Drive : 我的雲端硬碟/山而王其/secret

3 執行 取ytAPI.py 時，會自動開啟瀏覽器讓你登入 Google 帳號
選擇gmail再選擇yt頻道，並授權
授權完成後會在本機同目錄下產生 token.pickle 憑證，
上傳到 Google Drive : 我的雲端硬碟/山而王其/secret

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
# 检查GPU是否启用
!nvidia-smi
# 确认FFmpeg支持NVIDIA硬件编码
!ffmpeg -encoders | grep nvenc

!apt-get install -y fonts-noto-cjk  # 安裝文泉驛微米黑（支持中文/粵語）
!fc-list | grep "wqy-microhei"  # 驗證字體是否安裝成功（會顯示字體路徑）
!pip install --upgrade openai-whisper  # 升級到最新版以支持粵語
!pip install openai-whisper google-api-python-client google-auth-oauthlib google-auth-httplib2 requests moviepy pydub pysrt
!apt-get install -y librubberband2 ffmpeg # rubberband 滤镜用于音频变调 安装 librubberband2 后，ffmpeg 才能正常使用 rubberband 滤镜

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

import os, glob, subprocess, json, pickle, time, requests, whisper, shutil
from subprocess import CalledProcessError  





















# ===== 設定資料夾 =====
AUDIO_FOLDER = AutoUpYtGDrive
m4a_files = glob.glob(os.path.join(AUDIO_FOLDER, "*.mp3"))
if not m4a_files:
    print("!! 沒有 mp3，找 m4a")
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
cmd = [
    "ffmpeg", "-y", "-i", input_audio,
    #"-filter:a", "rubberband=pitch=-8", # 降8度
    "-ar", "16000", "-ac", "1",  # 保持采样率和声道设置（如需保留原始可移除）
    wav_path
    ]
subprocess.run(cmd, check=True)  # 增加check=True，出错时直接报错

# 转换后检查WAV文件
if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 1024:
    print("❌ WAV文件生成失败！")
    raise SystemExit()
print("主音訊直接使用原始 wav：", wav_path)


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
print("修改後的字幕前20行：")
print("\n".join(modified_srt.split("\n")[:20]))
print("已加載修改後的字幕")





































# ===============================================================
#     🔰 6 下載單一 Pexels 4K 影片（自動選最高畫質） 🔰
# ===============================================================

# 讀取 API Key
PEXELS_KEYS = []
k0 = userdata.get("PEXELS_API_KEY")
if k0: PEXELS_KEYS.append(k0)
k1 = userdata.get("PEXELS_API_KEY_1")
if k1: PEXELS_KEYS.append(k1)
if not PEXELS_KEYS:
    raise SystemExit("❌ 沒有設定 PEXELS API KEY")

key_index = 0
def get_headers():
    return {"Authorization": PEXELS_KEYS[key_index]}
def rotate_key():
    global key_index
    key_index = (key_index + 1) % len(PEXELS_KEYS)
    print(f"🔁 切換到 API Key #{key_index+1}")

# 取得音訊長度
audio_duration = float(
    json.loads(
        subprocess.Popen(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", wav_path],
            stdout=subprocess.PIPE
        ).communicate()[0]
    )["format"]["duration"]
)
print(f"🎧 音訊長度：{audio_duration:.2f} 秒")

# ===============================================================
#                   🔍 搜尋 4K 影片
# ===============================================================
page = 1
selected_video_url = None
selected_video_duration = None

print("🔎 嘗試取得 4K 影片...")

while True:
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=10&page={page}"
    res = requests.get(url, headers=get_headers())

    if res.status_code == 429:
        print("⚠️ API 次數用完，切換 Key")
        rotate_key()
        continue

    data = res.json()
    videos = data.get("videos", [])
    if not videos:
        print("⚠️ 沒有更多影片，換下一頁")
        page += 1
        continue

    # 找 3840x2160（強制 4K）
    for v in videos:
        for f in v["video_files"]:
            if f["width"] == 3840 and f["height"] == 2160:
                selected_video_url = f["link"]
                selected_video_duration = v["duration"]
                break
        if selected_video_url:
            break

    if selected_video_url:
        print(f"🎥 已選到 4K 影片（長度 {selected_video_duration}s）")
        break

    page += 1

# ===============================================================
#                   🔰 7 下載 4K 影片 🔰
# ===============================================================
raw_video = "/content/raw_4k.mp4"
!wget -q -O {raw_video} "{selected_video_url}"
print("📥 4K 影片已下載")





























# ===============================================================
#                   🔰 8 製作循環影片 🔰
# ===============================================================


#     🔰 实时提示 🔰
def print_with_timestamp(msg):
    """带时间戳的提示打印"""
    timestamp = time.strftime("[%H:%M:%S] ", time.localtime())
    print(f"{timestamp}{msg}", flush=True)  # flush=True 确保立即输出（不缓存）

def run_ffmpeg_with_progress(cmd, step_desc):
    """执行FFmpeg命令，带执行中提示和错误捕获"""
    # 1. 打印开始提示
    print_with_timestamp(f"⏳ 开始：{step_desc}")
    start_time = time.time()
    
    # 2. 执行命令（实时输出FFmpeg日志，避免卡住无反馈）
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # 将stderr重定向到stdout，统一捕获
        encoding="utf-8",
        bufsize=1,  # 行缓冲，实时输出
        universal_newlines=True
    )
    
    # 3. 实时打印FFmpeg输出（可选，看是否需要）
    for line in process.stdout:
        # 过滤无关日志，只打印关键信息（比如进度、帧处理）
        if "frame=" in line or "time=" in line or "duration=" in line:
            print(f"  📝 {line.strip()}", flush=True)
    
    # 4. 等待命令结束，获取返回码
    process.wait()
    elapsed = round(time.time() - start_time, 2)
    
    # 5. 结果判断
    if process.returncode == 0:
        print_with_timestamp(f"✅ 完成：{step_desc}（耗时 {elapsed} 秒）")
        return True
    else:
        print_with_timestamp(f"❌ 失败：{step_desc}（耗时 {elapsed} 秒）")
        raise CalledProcessError(process.returncode, cmd)

# ===============================================================
#     🔰 新增：获取视频实际时长 🔰
# ===============================================================
def get_video_duration(video_path):
    """自动获取视频时长（秒），无需手动输入"""
    print_with_timestamp(f"🔍 检测视频 {os.path.basename(video_path)} 时长...")
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    duration = float(result.stdout.strip())
    print_with_timestamp(f"✅ 视频时长：{duration:.2f} 秒 | 音频时长：{audio_duration:.2f} 秒")
    return duration

# ===============================================================
#     🔰 核心修改：极速循环/截取视频 🔰
# ===============================================================
looped_video = "/content/looped.mp4"
temp_concat_list = "/content/concat_list.txt"
temp_short_clip = "/content/temp_short_clip.mp4"

# 1. 获取原视频时长
video_duration = get_video_duration(raw_video)

# 2. 判断处理逻辑：截取（音频更短） or 拼接（音频更长）
if audio_duration <= video_duration:
    # 情况1：音频比视频短 → 直接截取视频（极速，无编码）
    cmd = [
        "ffmpeg", "-y",
        "-ss", "0",                  # 从开头截取
        "-i", raw_video,
        "-t", str(audio_duration),   # 截取到音频时长
        "-c", "copy",                # 流拷贝，无编码（关键！）
        looped_video
    ]
    run_ffmpeg_with_progress(
        cmd,
        f"截取视频至音频长度（{audio_duration:.2f}s）"
    )

else:
    # 情况2：音频比视频长 → 拼接补充（极速，无编码）
    need_extra = audio_duration - video_duration  # 需要补充的时长
    loop_times = int(need_extra // video_duration)  # 完整循环次数
    extra_clip_duration = need_extra % video_duration  # 最后补充的片段时长

    # 生成拼接清单
    print_with_timestamp(f"📝 需补充时长：{need_extra:.2f}秒 → 循环{loop_times}次 + 补充{extra_clip_duration:.2f}秒")
    with open(temp_concat_list, "w", encoding="utf-8") as f:
        # 写入原视频
        f.write(f"file '{raw_video}'\n")
        # 写入完整循环次数
        for _ in range(loop_times):
            f.write(f"file '{raw_video}'\n")
        # 提取并写入最后补充的片段（若有）
        if extra_clip_duration > 0.1:  # 忽略0.1秒内的微小差值
            # 提取原视频前N秒（流拷贝，极速）
            extract_cmd = [
                "ffmpeg", "-y",
                "-ss", "0",
                "-i", raw_video,
                "-t", f"{extra_clip_duration:.2f}",
                "-c", "copy",
                temp_short_clip
            ]
            run_ffmpeg_with_progress(
                extract_cmd,
                f"提取补充片段（{extra_clip_duration:.2f}s）"
            )
            f.write(f"file '{temp_short_clip}'\n")

    # 拼接所有片段（流拷贝，极速）
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",                # 允许绝对路径
        "-i", temp_concat_list,
        "-c", "copy",                # 流拷贝，无编码（关键！）
        looped_video
    ]
    run_ffmpeg_with_progress(
        concat_cmd,
        f"拼接视频至音频长度（{audio_duration:.2f}s）"
    )

    # 清理临时文件
    for temp_file in [temp_concat_list, temp_short_clip]:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print_with_timestamp(f"🗑️ 清理临时文件：{os.path.basename(temp_file)}")

# 最终提示
print_with_timestamp(f"🔁 已建立循环影片（长度={audio_duration:.2f}s）")





































cut_video = looped_video # 9 步驟已合併在 8 步驟中
'''
# ===============================================================
#                   🔰 9 裁切剛好音訊長度 🔰
# ===============================================================

cut_video = "/content/video_cut.mp4"
cmd = [
    "ffmpeg", "-y",
    "-i", looped_video,
    "-t", str(audio_duration),
    "-c:v", "copy",
    "-c:a", "copy",
    cut_video
]
subprocess.run(cmd, check=True)
print("✂️ 影片裁切完成")
'''
# ===============================================================
#                   🔰 10 合併音訊到影片 🔰
# ===============================================================
merged_video = f"/content/合聲_{base_name}.mp4"
cmd = [
    "ffmpeg", "-y",
    "-i", cut_video,
    "-i", wav_path,
    "-map", "0:v", "-map", "1:a",
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k",
    merged_video
]
subprocess.run(cmd, check=True)
print("🎬 合併音訊完成：", merged_video)























# ===============================================================
#                   🔰 11 燒錄字幕（硬字幕） 🔰
# ===============================================================

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


final_video = f"/content/合字_{base_name}.mp4"
# 确认SRT文件存在且路径正确
if not os.path.exists(srt_path):
    print(f"❌ 找不到字幕文件：{srt_path}")
    raise SystemExit()
# 打印实际使用的字幕路径
print(f"使用字幕文件：{os.path.abspath(srt_path)}")

video_height = get_video_height(merged_video)
# 1080x1080正方形视频：2.5%比例，最大27px，最小16px
fontsize = max(16, min(27, int(video_height * 0.025)))  
print(f"主影片高度：{video_height}px → 字幕字体大小：{fontsize}px")




























'''
sub_filter = (
    f"subtitles='{srt_path}':force_style="
    f"'Fontname=Noto Sans CJK TC,Fontsize={fontsize},"
    f"PrimaryColour=&HFFFFE5&,OutlineColour=&HA04000&,"
    f"BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=40'"
)

cmd = [
    "ffmpeg", "-y", "-i", merged_video,
    #"-vf", f"subtitles={srt_path}:force_style='Fontsize=20,FontName=WenQuanYi Micro Hei'",
    "-vf", sub_filter,
    "-c:a", "copy",
    final_video
]
subprocess.run(cmd, check=True, capture_output=True)
print("字幕已燒錄：", final_video)
'''


# ===================== 优化后的字幕烧录逻辑 =====================


def burn_subtitle_fast(merged_video, srt_path, fontsize, final_video):
    """
    4K字幕烧录（极速版：30fps+轻量级编码）
    """
    # 1. 复制字幕到本地
    local_srt = f"/content/local_{base_name}.srt"
    if os.path.exists(local_srt):
        os.remove(local_srt)
        print_with_timestamp(f"🗑️ 已删除旧本地字幕文件：{local_srt}")
    shutil.copy(srt_path, local_srt)
    print_with_timestamp(f"📝 字幕已复制到本地：{local_srt}")

    # 2. 字幕滤镜（简化特效，减少渲染耗时）
    sub_filter = (
        f"fps=30, scale=1920:1080, "  # 4K→2K+30fps
        f"subtitles='{local_srt}':force_style="
        f"'Fontname=WenQuanYi Micro Hei,Fontsize={fontsize},"
        f"PrimaryColour=&HFFFFE5&,OutlineColour=&HA04000&,"
        f"BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=40'"
    )

    # 3. 极致提速的编码命令（4K 30fps）
    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts", "-flush_packets", "1",  # 禁用缓存，强制重读文件
        "-i", merged_video,
        "-vf", sub_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",    # 最快预设
        "-crf", "28",              # 轻微压缩（观感无差别）
        "-profile:v", "main",      # 降低编码复杂度（4K 30fps足够）
        "-level", "5.0",           # 适配30fps 4K
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",            # 音频不编码
        "-threads", "16",          # 启用多线程（Colab默认16核）
        final_video
    ]

    # 执行命令+实时进度
    print_with_timestamp("⏳ 开始极速烧录4K字幕（30fps+多线程）...")
    start_time = time.time()
    try:
        # 实时打印进度（避免卡顿无反馈）
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            bufsize=1
        )
        # 只打印关键进度（减少日志输出）
        for line in process.stdout:
            if "frame=" in line and "time=" in line:
                print(f"  📊 {line.strip()}", flush=True)
        process.wait()

        if process.returncode != 0:
            raise CalledProcessError(process.returncode, cmd)
        
        elapsed = round(time.time() - start_time, 2)
        print_with_timestamp(f"✅ 4K字幕烧录完成！耗时 {elapsed} 秒")
        shutil.rmtree(local_srt, ignore_errors=True)
        return True
    except CalledProcessError as e:
        print_with_timestamp(f"❌ 字幕烧录失败：{e.stderr[:1000]}")  # 只打印前1000字符
        raise




# 执行GPU加速烧录
burn_subtitle_fast(merged_video, srt_path, fontsize, final_video)
print("字幕已燒錄：", final_video)





























# ===============================================================
#            🔰 12 重新設計的片頭 + 主影片 + 片尾合成 🔰
# ===============================================================

import json
import os
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

FINAL_COMBINED = f"/content/全片_{base_name}.mp4"

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
        "-c:a", "copy",
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
        "-c:a", "aac", "-ar", "16000", "-ac", "1",
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
        "-c:a", "aac", "-ar", "16000", "-ac", "1",
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
    "-c:v", "libx264", "-c:a", "copy",
    FINAL_COMBINED
], f"拼接 全片_{base_name}.mp4")

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
