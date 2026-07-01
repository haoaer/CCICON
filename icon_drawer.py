"""绘制托盘状态图标：灰/黄/绿/红圆形灯，支持闪烁效果"""

from PIL import Image, ImageDraw

ICON_SIZE = 64

COLORS = {
    "gray": (158, 158, 158),    # 空闲
    "yellow": (255, 193, 7),    # 工作中
    "green": (76, 175, 80),     # 完成（闪烁用）
    "red": (244, 67, 54),       # 出错/询问（闪烁用）
}


def _draw_circle(img: Image.Image, fill: tuple) -> Image.Image:
    """在图片上绘制一个圆形灯"""
    draw = ImageDraw.Draw(img)
    padding = 4
    draw.ellipse(
        [padding, padding, ICON_SIZE - padding, ICON_SIZE - padding],
        fill=fill,
        outline=(255, 255, 255, 180),
        width=2,
    )
    return img


def create_icon(color: str) -> Image.Image:
    """创建一个纯色圆形状态灯图标"""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    fill = COLORS.get(color, COLORS["gray"])
    return _draw_circle(img, fill)


def create_blank_icon() -> Image.Image:
    """创建一个空白透明图标（用于闪烁的灭帧）"""
    return Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
