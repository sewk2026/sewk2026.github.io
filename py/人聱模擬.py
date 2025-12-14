from google.colab import drive
drive.mount('/content/drive')

!apt install git wget ffmpeg libsox-dev unzip -y  # 添加 unzip 以解壓模型

# 修復常見 ldconfig 警告（可選，但推薦）
!sudo mv /usr/local/lib/libtbbbind.so.3 /usr/local/lib/libtbbbind.so.3.old
!sudo ln -s /usr/local/lib/libtbbbind.so.3.0 /usr/local/lib/libtbbbind.so.3























import os

repo_path = '/content/GPT-SoVITS'
if not os.path.exists(repo_path):
    !git clone https://github.com/RVC-Boss/GPT-SoVITS {repo_path}

%cd {repo_path}

# 安裝特定版本避免衝突
!pip install numba==0.56.4 pyyaml
!pip install -r requirements.txt
!pip install torch torchaudio pydub modelscope==1.11.0 sentencepiece funasr==0.8.8
























Drive根資料夾 = '/content/drive/MyDrive/山而王其/'

drive_models_path = Drive根資料夾 + 'AI人聲/models'
os.makedirs(drive_models_path, exist_ok=True)

# 正確 URL，從 lj1995/GPT-SoVITS
models = {
    's1v3': 's1v3.ckpt',
    's2Gv3': 's2Gv3.pth'
}
base_url = 'https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/'

for model in models.values():
    local_path = os.path.join(drive_models_path, model)
    if not os.path.exists(local_path):
        !wget -P {drive_models_path} "{base_url + model}"
        print(f"已將 {model} 下載到 Google 雲端硬碟。")
    else:
        print(f"{model} 已存在於雲端硬碟。")

# 下載並解壓 bigvgan_v2 模型（必要）
bigvgan_zip = os.path.join(drive_models_path, 'bigvgan_v2.zip')
if not os.path.exists(bigvgan_zip):
    !wget -P {drive_models_path} "https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/models--nvidia--bigvgan_v2_24khz_100band_256x.zip" -O {bigvgan_zip}
    !unzip {bigvgan_zip} -d {drive_models_path}
    print("已解壓 bigvgan_v2 模型。")
else:
    print("bigvgan_v2 已存在。")























drive_samples_path = Drive根資料夾 + '料/'
drive_trained_path = Drive根資料夾 + 'AI人聲/trained'
os.makedirs(drive_trained_path, exist_ok=True)

# 樣本檔案（支持 m4a，自動轉 wav）
sample_file = os.path.join(drive_samples_path, '人聲範本.m4a')
wav_sample = os.path.join(drive_samples_path, '人聲範本.wav')  # 轉換後檔案

from pydub import AudioSegment
if not os.path.exists(wav_sample):
    sound = AudioSegment.from_file(sample_file, format="m4a")
    sound.export(wav_sample, format="wav")
    print("已將 m4a 轉為 wav。")

trained_model_file = os.path.join(drive_trained_path, 'my_model.pth')

if not os.path.exists(trained_model_file):
    # 預處理音頻（重新採樣到 32kHz）
    resampled_path = os.path.join(drive_samples_path, 'resampled')
    os.makedirs(resampled_path, exist_ok=True)
    !python tools/resample.py --in_path {drive_samples_path} --out_path {resampled_path} --sr 32000

    # 訓練（使用項目 train.py，調整 config.yaml 如需）
    # 假設 config.yaml 已配置好；epochs=10 適合短樣本
    !python train.py --config config.yaml --train_data {resampled_path} --output {drive_trained_path} --epochs 10

    # 保存模型（根據項目邏輯調整）
    print("訓練完成並保存到雲端硬碟。")
else:
    print("模型已訓練好，跳過訓練。")













from pydub import AudioSegment
import time

# 輸入粵語文字
text = "你好嗎？這是測試粵語。"  # 替換為您的文字
lang = "yue"  # 粵語代碼

# 推理（使用項目 inference.py）
output_wav = 'output.wav'
!python inference.py --text "{text}" --lang {lang} --ref_audio {wav_sample} --model_path {trained_model_file} --output {output_wav}

# 轉換為 m4a 或 mp3
drive_outputs_path = Drive根資料夾 + '錄音'
os.makedirs(drive_outputs_path, exist_ok=True)

output_format = 'm4a'  # 或 'mp3'
output_file = os.path.join(drive_outputs_path, f'output_{int(time.time())}.{output_format}')

sound = AudioSegment.from_wav(output_wav)
sound.export(output_file, format=output_format)
print(f"生成的音訊已儲存到 {output_file}")


