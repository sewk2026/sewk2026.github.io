!apt-get update
!apt-get install -y fonts-noto-cjk



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
img = Image.new("RGB", (1080, 1080), "black")
draw = ImageDraw.Draw(img)

# --- 加金色光暈背景 ---
glow = Image.new("RGB", (1080, 1080), "black")
gdraw = ImageDraw.Draw(glow)
gdraw.ellipse((150, 300, 950, 1100), fill=(255, 200, 0))
glow = glow.filter(ImageFilter.GaussianBlur(180))
img = Image.blend(img, glow, 0.35)
draw = ImageDraw.Draw(img)   # 重新 draw

print('='*18)
答標題 = input("封面標題")
答正文 = input("封面正文")
封面號 = input("封面號")
#input("右下小字")
print('='*18)


# --- 主要文字 ---
封面標題 = f"《{答標題}》"
封面正文 = 答正文
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

img.save(f"{封面號}.png")
img
