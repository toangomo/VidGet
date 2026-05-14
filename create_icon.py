"""Generate VidGet.ico — violet rounded-square with V letter."""
from PIL import Image, ImageDraw, ImageFont
import os

def make_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    frames = []

    for s in sizes:
        img  = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        r = max(4, s // 6)
        # Violet gradient background via two passes
        draw.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=(124, 58, 237, 255))
        # Subtle inner highlight
        draw.rounded_rectangle([1, 1, s - 2, s // 2], radius=r, fill=(167, 139, 250, 40))

        # "V" letter
        font_size = max(8, int(s * 0.62))
        font = None
        for fpath in [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]:
            if os.path.exists(fpath):
                try:
                    font = ImageFont.truetype(fpath, font_size)
                    break
                except Exception:
                    pass

        text = "V"
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (s - tw) // 2 - bbox[0]
            y = (s - th) // 2 - bbox[1] - int(s * 0.04)
            draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        else:
            # Fallback: simple manual V shape
            m = s // 8
            pts = [m, m, s // 2, s - m, s - m, m]
            draw.line([(m, m), (s // 2, s - m)], fill="white", width=max(2, s // 12))
            draw.line([(s - m, m), (s // 2, s - m)], fill="white", width=max(2, s // 12))

        frames.append(img)

    out = "VidGet.ico"
    frames[0].save(out, format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=frames[1:])
    print(f"Created {out}")

if __name__ == "__main__":
    make_icon()
