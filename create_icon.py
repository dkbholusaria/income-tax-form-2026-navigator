"""Generate app_icon.ico for the IT Forms Downloader."""
from PIL import Image, ImageDraw, ImageFont
import os

SIZES = [16, 32, 48, 64, 128, 256]

def create_icon():
    """Create a professional-looking app icon."""
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background: rounded rectangle in navy blue
    bg_color = (26, 35, 126)    # #1a237e
    margin = 12
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=40,
        fill=bg_color,
    )

    # Inner accent border
    accent = (66, 165, 245)  # #42a5f5
    draw.rounded_rectangle(
        [margin + 6, margin + 6, size - margin - 6, size - margin - 6],
        radius=36,
        fill=None,
        outline=accent,
        width=3,
    )

    # "IT" text in white
    try:
        font_large = ImageFont.truetype("arial.ttf", 100)
    except OSError:
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
        except OSError:
            font_large = ImageFont.load_default()

    text = "IT"
    bbox = draw.textbbox((0, 0), text, font=font_large)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2
    y = (size - th) // 2 - 30
    draw.text((x, y), text, fill=(255, 255, 255), font=font_large)

    # "FORMS" subtext
    try:
        font_small = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        try:
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except OSError:
            font_small = ImageFont.load_default()

    sub = "FORMS"
    bbox2 = draw.textbbox((0, 0), sub, font=font_small)
    sw = bbox2[2] - bbox2[0]
    sx = (size - sw) // 2
    draw.text((sx, y + th + 8), sub, fill=accent, font=font_small)

    # Saffron stripe at bottom (Indian flag motif)
    saffron = (255, 153, 51)  # #ff9933
    draw.rectangle(
        [margin + 20, size - margin - 30, size - margin - 20, size - margin - 22],
        fill=saffron,
    )

    # Generate multi-size ICO
    icons = []
    for s in SIZES:
        icons.append(img.resize((s, s), Image.LANCZOS))

    out_path = os.path.join(os.path.dirname(__file__), "app_icon.ico")
    icons[0].save(out_path, format="ICO", sizes=[(s, s) for s in SIZES],
                  append_images=icons[1:])
    print(f"Icon saved: {out_path}")

    # Also save a PNG for the installer
    png_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
    img.save(png_path, "PNG")
    print(f"PNG saved: {png_path}")


if __name__ == "__main__":
    create_icon()
