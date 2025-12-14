'''

202512121557 封面圖

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


# 生成封面圖
!apt-get update
!apt-get install -y fonts-noto-cjk

# ===== 用colab密鑰避免api暴露 =====
from google.colab import userdata
from google.colab import drive
drive.mount('/content/drive')

import os, glob, subprocess, json, pickle, time, requests, whisper, shutil
from subprocess import CalledProcessError  





# ===============================================================
#                   🔰 0 admin setting  🔰
# ===============================================================


#     🔰 实时提示 🔰
def print_with_timestamp(msg):
    """带时间戳的提示打印"""
    timestamp = time.strftime("[%H:%M:%S] ", time.localtime())
    print(f"{timestamp}{msg}", flush=True)  # flush=True 确保立即输出（不缓存）



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


# 在代码中添加获取音频时长的函数
def get_audio_duration(audio_path):
    """获取音频时长（秒）"""
    print_with_timestamp(f"🔍 检测音频 {os.path.basename(audio_path)} 时长...")
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    duration = float(result.stdout.strip())
    print_with_timestamp(f"✅ 音频时长：{duration:.2f} 秒")
    return duration


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

audio_duration = get_audio_duration(wav_path) 



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
while True:
    print('=' * 18)
    print("請手動修改字幕文件：")
    # 强调保存路径
    print(f"⚠️  請確保修改後保存到該路徑：{os.path.abspath(srt_path)}")
    print("修改步驟：")
    print("1. 打開 Google Drive，找到上述路徑的 .srt 文件")
    print("2. 右鍵選擇「打開方式」→「文本編輯器」")
    print("3. 修正錯誤字幕後保存")
    input("修改完成後，請在此處按 Enter 鍵繼續...")  # 等待用戶確認

    # 读取修改后的SRT
    with open(srt_path, "r", encoding="utf-8") as f:
        modified_srt = f.read()

    # 验证并打印修改后的内容（前20行）
    print("\n修改後的字幕前20行：")
    modified_lines = modified_srt.split("\n")
    print("\n".join(modified_lines[:20]) if len(modified_lines) >= 20 else modified_srt)
    print("已加載修改後的字幕")

    # 让用户选择后续操作
    print('\n' + '=' * 18)
    print("請選擇後續操作：")
    print("1. 繼續執行後續程式")
    print("2. 重新手動修改字幕文件")
    # 容错处理：循环获取有效输入
    while True:
        user_choice = input("請輸入數字 1 或 2 並按 Enter 鍵：").strip()
        if user_choice in ["1", "2"]:
            break
        else:
            print("❌ 輸入無效，請只輸入 1 或 2！")

    # 根据用户选择处理
    if user_choice == "1":
        print("✅ 用戶選擇繼續執行後續程式...")
        break  # 退出循环，执行后续代码
    else:
        print("🔄 用戶選擇重新修改字幕文件，重新進入修改流程...")
        continue  # 继续循环，重新提示修改




# 封面正文
封面正文 = modified_srt.split("\n")[3].strip() #"對自己誠實"
print('='*18)
print(f"2: 請填寫您的封面正文 沒填用預設值[ {封面正文} ]")
答 = input("填寫 封面正文 後，請在此處按 Enter 鍵繼續...")
if 答:
    封面正文 = 答
    print(f"✅ 已使用自訂值：{封面正文}")
else:
    print(f"✅ 未輸入，使用預設值：{封面正文}")





































# ===============================================================
#                   🔰 6 下载视频（本地优先 + Pexels fallback） 🔰
# ===============================================================

def download_pexels_4k_video(query):
    """
    从Pexels下载4K视频（自动处理API密钥轮换和视频筛选）
    返回下载后的视频路径（/content/raw_4k.mp4）
    """
    global key_index  # 声明使用全局变量
    
    # 读取API Key
    PEXELS_KEYS = []
    k0 = userdata.get("PEXELS_API_KEY")
    if k0: PEXELS_KEYS.append(k0)
    k1 = userdata.get("PEXELS_API_KEY_1")
    if k1: PEXELS_KEYS.append(k1)
    k2 = userdata.get("PEXELS_API_KEY_2")
    if k2: PEXELS_KEYS.append(k2)
    if not PEXELS_KEYS:
        raise SystemExit("❌ 没有设置PEXELS API KEY")

    key_index = 0
    def get_headers():
        return {"Authorization": PEXELS_KEYS[key_index]}
    def rotate_key():
        global key_index
        key_index = (key_index + 1) % len(PEXELS_KEYS)
        print(f"🔁 切换到API Key #{key_index+1}")

    # 搜索4K视频
    page = 1
    selected_video_url = None
    selected_video_duration = None

    print("🔎 尝试从Pexels获取4K影片...")
    while True:
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=10&page={page}"
        res = requests.get(url, headers=get_headers())

        if res.status_code == 429:
            print("⚠️ API次数用完，切换Key")
            rotate_key()
            continue

        # 处理非200状态码的情况（增加鲁棒性）
        if res.status_code != 200:
            print(f"⚠️ 请求失败，状态码：{res.status_code}")
            rotate_key()
            continue

        data = res.json()
        videos = data.get("videos", [])
        if not videos:
            print("⚠️ 没有更多影片，换下一頁")
            page += 1
            continue

        # 查找2K视频（2560×1440，QHD/1440p）
        for v in videos:
            for f in v["video_files"]:
                # 核心修改：2K分辨率筛选条件
                if f["width"] == 2560 and f["height"] == 1440 or (f["width"] == 1920 and f["height"] == 1080):
                    selected_video_url = f["link"]
                    selected_video_duration = v["duration"]
                    # 标记分辨率类型
                    res_type = "2560×1440" if (f["width"] == 2560 and f["height"] == 1440) else "1920×1080"
                    break
            if selected_video_url:
                print(f"🎥 已选到{res_type}影片（长度 {selected_video_duration}s）")
                break

        if selected_video_url:
            print(f"🎥 已选到4K影片（长度 {selected_video_duration}s）")
            break

        page += 1

    # 下载4K视频
    raw_video = "/content/raw_4k.mp4"
    !wget -q -O {raw_video} "{selected_video_url}"
    print("📥 Pexels 4K影片已下载")
    return raw_video


# 检查AUDIO_FOLDER中是否有现成的MP4文件
mp4_files = glob.glob(os.path.join(AUDIO_FOLDER, "*.mp4"))
raw_video = "/content/raw_4k.mp4"  # 目标视频路径

if mp4_files:
    # 如果有本地MP4，使用第一个并复制到目标路径
    local_mp4 = mp4_files[0]
    print(f"📂 发现本地MP4文件：{local_mp4}")
    shutil.copy2(local_mp4, raw_video)  # 保留元数据复制
    print(f"✅ 已将本地MP4复制到：{raw_video}")
else:
    # 如果没有本地MP4，调用Pexels下载函数
    print("❌ 未发现本地MP4文件，将从Pexels下载...")
    raw_video = download_pexels_4k_video(query)  # 使用前面定义的查询关键词





























# ===============================================================
#                   🔰 8 製作循環影片 🔰
# ===============================================================



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
        "-fflags", "+genpts",
        "-i", merged_video,
        "-vf",
        f"subtitles='{srt_path}':force_style="
        f"'Fontname=Noto Sans CJK TC,"
        f"Fontsize={fontsize},"
        f"PrimaryColour=&HFFFFE5&,"
        f"OutlineColour=&HA04000&,"
        f"BorderStyle=1,Outline=2,Shadow=1,"
        f"Alignment=2,MarginV=40'",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-threads", "2",
        "-c:a", "copy",
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

# 封面圖

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 字體路徑（Colab 100% 可用）
font_regular = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
font_bold = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

# --- 字體載入（失敗就報錯） ---
try:
    title_font = ImageFont.truetype(font_bold, 90)
    header_font = ImageFont.truetype(font_bold, 60)
    desc_font = ImageFont.truetype(font_regular, 40)
except Exception as e:
    print("❌ 字體載入失敗：", e)

# --- 黑底模板 ---
封面img = Image.new("RGB", (1080, 1080), "black")
draw = ImageDraw.Draw(封面img)

# --- 加金色光暈背景 ---
glow = Image.new("RGB", (1080, 1080), "black")
gdraw = ImageDraw.Draw(glow)
gdraw.ellipse((150, 300, 950, 1100), fill=(255, 200, 0))
glow = glow.filter(ImageFilter.GaussianBlur(180))
封面img = Image.blend(封面img, glow, 0.35)
draw = ImageDraw.Draw(封面img)   # 重新 draw

# --- 主要文字 ---
封面標題 = f"《{base_name}》" #"《山王心法 Day 2》"
# 封面正文 = 272行
desc_text = "山而王其"

# Header
draw.text((60, 80), 封面標題, font=header_font, fill=(255, 215, 0))

# Main text
draw.text((60, 320), 封面正文, font=title_font, fill="white")

# --- 右下角說明文字 ---
bbox = draw.textbbox((0, 0), desc_text, font=desc_font)
w = bbox[2] - bbox[0]
h = bbox[3] - bbox[1]

draw.text((1080 - w - 60, 1080 - h - 60), desc_text, font=desc_font, fill=(200, 200, 200))

# 保存封面圖
COVER_IMAGE_PATH = f"/content/封面_{base_name}.png"
封面img.save(COVER_IMAGE_PATH)
print(f"✅ 封面圖已保存：{COVER_IMAGE_PATH}")





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
COVER_11 = "/content/cover_1by1.mp4"  # 封面1:1版本

INTRO_FADED = "/content/intro_faded.mp4"
MAIN_FADED = "/content/main_faded.mp4"
OUTRO_FADED = "/content/outro_faded.mp4"
COVER_FADED = "/content/cover_faded.mp4"  # 封面淡入效果

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



# 新增：將封面圖轉換為1秒視頻
COVER_VIDEO = "/content/cover_video.mp4"
print_with_timestamp("⏳ 將封面圖轉換為1秒視頻...")
cover_cmd = [
    "ffmpeg", "-y",
    "-loop", "1",  # 循環圖片
    "-i", COVER_IMAGE_PATH,
    "-t", "1",     # 时长1秒
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-s", "1080x1080",  # 保持1:1比例
    COVER_VIDEO
]
run_ffmpeg(cover_cmd, "生成封面1秒視頻")




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
        "-c:a", "copy",
        dst
    ]
    run_ffmpeg(cmd, f"主影片淡入 → {dst}")


# ===============================================================
#                   Step 1：轉成 1:1
# ===============================================================
convert_to_square(COVER_VIDEO, COVER_11)  # 封面轉1:1
convert_to_square(INTRO_SRC, INTRO_11)
convert_to_square(final_video, MAIN_FADED.replace("_faded", "_1by1"))  # temp
convert_to_square(OUTRO_SRC, OUTRO_11)

# 重新指定主影片 1:1 路徑
MAIN_11 = MAIN_FADED.replace("_faded", "_1by1")

# ===============================================================
#                   Step 2：套用淡入淡出
# ===============================================================
fade_only_in(COVER_11, COVER_FADED, fadein=0.3)  # 封面快速淡入
fade_in_out(INTRO_11, INTRO_FADED)
fade_only_in(MAIN_11, MAIN_FADED)
fade_in_out(OUTRO_11, OUTRO_FADED)

# ===============================================================
#                   Step 3：拼接 intro → main → outro
# ===============================================================
concat_txt = "/content/concat_intro_main_outro.txt"
with open(concat_txt, "w") as f:
    f.write(f"file '{COVER_FADED}'\n")  # 封面放在最前面
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

print("\n🎬【封面 + 片頭 + 主影片 + 片尾】全部完成！")
print("最終輸出：", FINAL_COMBINED)

# 更新上傳用檔案
final_video = FINAL_COMBINED






















# ===============================================================
#                   🔰 13 自動上傳 YouTube（Colab 穩定版） 🔰
# ===============================================================

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

CLIENT_SECRETS_FILE = Drive根資料夾 + "secret/client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PICKLE = Drive根資料夾 + "secret/token.pickle"

credentials = None

# === 1️⃣ 讀取已存在的 token（如果有） ===
if os.path.exists(TOKEN_PICKLE):
    with open(TOKEN_PICKLE, "rb") as f:
        credentials = pickle.load(f)
        print("🔑 已讀取 token.pickle")

# === 2️⃣ 檢查 / 刷新 / 重新授權 ===
need_reauth = False

if credentials:
    if credentials.expired:
        if credentials.refresh_token:
            print("🔄 嘗試自動刷新 token...")
            try:
                credentials.refresh(Request())
                print("✅ Token 刷新成功")
            except Exception as e:
                print("⚠️ Token 刷新失敗，需重新授權")
                need_reauth = True
        else:
            print("⚠️ 沒有 refresh_token，需重新授權")
            need_reauth = True
else:
    need_reauth = True

# === 3️⃣ 重新 OAuth 授權（Colab 專用） ===
if need_reauth:
    input('''
        需重新 OAuth 授權（本機專用）          
        將 client_secret_xxx.json 重新命名為 client_secret.json，
        同時放到本機的 取ytAPI.py 同目錄下 
        並上傳到 Google Drive : 我的雲端硬碟/山而王其/secret

        執行 取ytAPI.py 時，會自動開啟瀏覽器讓你登入 Google 帳號
        選擇gmail再選擇yt頻道，並授權
        授權完成後會在本機同目錄下產生 token.pickle 憑證，
        上傳到 Google Drive : 我的雲端硬碟/山而王其/secret
            
        完成後
        請在此處按 Enter 鍵繼續...
    ''')



    # 儲存新 token
    with open(TOKEN_PICKLE, "wb") as f:
        pickle.dump(credentials, f)
    print("💾 新 token.pickle 已保存")

# === 4️⃣ 建立 YouTube Client ===
youtube = build("youtube", "v3", credentials=credentials)

# === 5️⃣ 上傳影片 ===
request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": base_name,              # ← 你前面已處理好去掉 .mp4
            "description": YoutubeDescription
        },
        "status": {
            "privacyStatus": "public"        # public / unlisted / private
        }
    },
    media_body=MediaFileUpload(final_video, resumable=True)
)

response = request.execute()
video_id = response["id"]
print(f"✅ 已上傳 YouTube：https://www.youtube.com/watch?v={video_id}")
