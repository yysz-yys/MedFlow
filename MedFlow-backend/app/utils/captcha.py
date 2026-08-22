"""图形验证码 — 内存字典存储，不依赖数据库。"""
import uuid
import time
import random
import io
import base64
from PIL import Image, ImageDraw, ImageFont

# {captcha_id: (answer, expires_at_timestamp)}
_store: dict[str, tuple[str, float]] = {}

# 尝试加载系统字体，失败则用默认字体
_FONT: ImageFont.FreeTypeFont | ImageFont.ImageFont | None = None


def _get_font(size: int = 30) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    global _FONT
    if _FONT is not None:
        return _FONT
    # Windows / Linux / macOS 常见字体路径
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        try:
            _FONT = ImageFont.truetype(path, size)
            return _FONT
        except (OSError, IOError):
            continue
    _FONT = ImageFont.load_default()
    return _FONT


def generate() -> tuple[str, str]:
    """生成 4 位数字验证码图片。

    Returns:
        (captcha_id, image_base64) — image 是 "data:image/png;base64,..." 格式
    """
    text = "".join(random.choices("0123456789", k=4))
    font = _get_font(30)

    # 160x60 白底图片
    W, H = 160, 60
    img = Image.new("RGB", (W, H), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # 绘制 4 个数字，均匀分布，随机微调位置和颜色
    for i, ch in enumerate(text):
        x = 12 + i * 38
        y = random.randint(6, 14)
        r, g, b = random.randint(0, 80), random.randint(0, 80), random.randint(0, 80)
        draw.text((x, y), ch, fill=(r, g, b), font=font)

    # 干扰线
    for _ in range(4):
        x1 = random.randint(0, W)
        y1 = random.randint(0, H)
        x2 = random.randint(0, W)
        y2 = random.randint(0, H)
        draw.line([(x1, y1), (x2, y2)], fill=(180, 180, 180), width=1)

    # 干扰点
    for _ in range(60):
        x = random.randint(0, W - 1)
        y = random.randint(0, H - 1)
        draw.point((x, y), fill=(160, 160, 160))

    # 编码为 base64
    buf = io.BytesIO()
    img.save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    cid = uuid.uuid4().hex
    _store[cid] = (text, time.time() + 300)  # 5 分钟过期
    return cid, f"data:image/png;base64,{b64}"


def verify(captcha_id: str, text: str) -> bool:
    """校验图形验证码。每个 captcha_id 只能使用一次，用完即删。"""
    entry = _store.pop(captcha_id, None)
    if entry is None:
        return False
    answer, expires = entry
    if time.time() > expires:
        return False
    return text == answer
