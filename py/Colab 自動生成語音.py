# ===============================================================
# 🔰 MiniMax 中國區 TTS（JWT 版）自動化
# ===============================================================

import requests, json, os
from google.colab import drive
from google.colab import userdata

# ---------------------------------------------------------------
# 1. 掛載 Google Drive
# ---------------------------------------------------------------
drive.mount('/content/drive')

SAVE_DIR = "/content/drive/MyDrive/山而王其/錄音"
os.makedirs(SAVE_DIR, exist_ok=True)

print("📂 生成音訊將自動存到：", SAVE_DIR)


# ---------------------------------------------------------------
# 2. 手動輸入 JWT（重要！請填入你自己的）
# ---------------------------------------------------------------
JWT_TOKEN = userdata.get("海螺_API")

if not JWT_TOKEN:
    raise SystemExit("❌ 未輸入 JWT Token")


# ---------------------------------------------------------------
# 3. TTS 參數（你可修改）
# ---------------------------------------------------------------
api_url = "https://api.minimax.chat/v1/audio/text_to_speech"

# 可選 voice_id 清單（你可以到平台確認）
DEFAULT_VOICE = userdata.get("海螺VOICE_ID")

# ---------------------------------------------------------------
# 4. 主 TTS 函式
# ---------------------------------------------------------------
def minimax_tts(text,
                voice_id=DEFAULT_VOICE,
                speed=1.0,
                audio_format="mp3"):
    """
    呼叫 MiniMax TTS（中國區 JWT）
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JWT_TOKEN}"
    }

    payload = {
        "model": "speech-01",   # 中國區固定
        "text": text,
        "audio_format": audio_format,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed
        }
    }

    print("🚀 正在生成語音...")
    res = requests.post(api_url, headers=headers, json=payload)

    if res.status_code != 200:
        print("❌ API 錯誤：", res.text)
        return None

    data = res.json()

    if "audio" not in data:
        print("❌ 回傳格式錯誤：", data)
        return None

    # base64 音訊
    audio_b64 = data["audio"]

    # 產生存檔路徑
    filename = f"tts_{voice_id}_{str(len(text))}.{audio_format}"
    save_path = os.path.join(SAVE_DIR, filename)

    # 存音訊
    import base64
    audio_bytes = base64.b64decode(audio_b64)
    with open(save_path, "wb") as f:
        f.write(audio_bytes)

    print(f"✅ 語音已生成：{save_path}")
    return save_path


# ---------------------------------------------------------------
# 5. 測試產生語音
# ---------------------------------------------------------------
text = input("請輸入你要轉語音的文字：\n")

output = minimax_tts(
    text=text,
    voice_id=DEFAULT_VOICE,
    speed=1.0,
    audio_format="mp3"
)

print("🎧 完成！檔案位置：", output)
