"""
Renders standee_vector.svg into high-resolution print assets:
1. standee_300dpi.png (7200 x 18000 px, 300 DPI for 24" x 60" print)
2. standee_preview.png (1440 x 3600 px, quick visual preview)
3. standee_print_300dpi.pdf (Vector PDF for print shops)

All outputs go to the project's standee\ folder.
"""

import os
import cairosvg
from PIL import Image
Image.MAX_IMAGE_PIXELS = 200_000_000  # Allow large print images

def render_assets():
    standee_dir = r"C:\Users\hp\Desktop\New folder (9)\standee"
    svg_path = os.path.join(standee_dir, "standee_vector.svg")

    png_preview = os.path.join(standee_dir, "standee_preview.png")
    png_300dpi  = os.path.join(standee_dir, "standee_300dpi.png")
    pdf_print   = os.path.join(standee_dir, "standee_print_300dpi.pdf")

    print(f"Reading SVG: {svg_path}")

    # 1. Preview PNG (1440 x 3600)
    print("Rendering preview PNG (1440x3600)...")
    cairosvg.svg2png(url=svg_path, write_to=png_preview, scale=1.0)
    print(f"  -> {png_preview}")

    # 2. 300 DPI Print PNG (7200 x 18000)
    print("Rendering 300 DPI PNG (7200x18000, scale=5.0)...")
    cairosvg.svg2png(url=svg_path, write_to=png_300dpi, scale=5.0)
    print(f"  -> {png_300dpi}")

    # 3. Vector PDF
    print("Rendering print PDF...")
    cairosvg.svg2pdf(url=svg_path, write_to=pdf_print)
    print(f"  -> {pdf_print}")

    # Verify
    img = Image.open(png_300dpi)
    w, h = img.size
    print(f"\nVerification: {w} x {h} pixels (expected 7200 x 18000)")
    if w == 7200 and h == 18000:
        print("[OK] Resolution correct for 24x60 at 300 DPI")
    else:
        print("[WARN] Resolution mismatch - check SVG viewBox dimensions")

if __name__ == "__main__":
    render_assets()
