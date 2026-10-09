"""Clean asset processing script to eliminate duplicate text and rectangular borders."""

from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw
import numpy as np

def clean_assets():
    source_img_path = Path("/Users/ehab/.gemini/antigravity/brain/4c38aed3-44a6-4497-94bd-ad564df3488c/.user_uploaded/media_1791467956768_716ef27b.jpg")
    assets_dir = Path("/Users/ehab/Desktop/Antigravity Folder/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source_img_path) as img:
        img = img.convert("RGBA")
        w, h = img.size

        # -------------------------------------------------------------
        # 1. Header Background:
        # The reference image has Cairo tower and skyline between y=0 and y=0.20*h.
        # Below y=0.18*h is where the text "HASSAN DAILY" was stamped in the original.
        # We can extract the pristine skyline (y=0 to y=0.19*h), resize/extend it to 1080x400,
        # and create a smooth dark gradient at the bottom so the new text renders cleanly!
        # -------------------------------------------------------------
        skyline_box = (0, 0, w, int(h * 0.185))
        skyline = img.crop(skyline_box).resize((1080, 260), Image.Resampling.LANCZOS)
        
        # Also remove the slogan from the top right of the background by inpainting the sky color
        # In skyline, top right is approx x=920 to 1080, y=0 to 120
        # Let's clone a patch of sky from x=600..700 to x=920..1080
        sky_patch = skyline.crop((600, 10, 750, 110))
        skyline.paste(sky_patch.resize((160, 100)), (920, 10))
        skyline = skyline.filter(ImageFilter.SMOOTH_MORE)

        # Create 1080x400 canvas with gradient fade to #0b0f19
        bg_canvas = Image.new("RGBA", (1080, 400), (11, 15, 25, 255))
        bg_canvas.paste(skyline, (0, 0))
        
        # Create a vertical gradient overlay on the lower half (y=160 to 400)
        grad_overlay = Image.new("RGBA", (1080, 400), (0, 0, 0, 0))
        draw = ImageDraw.Draw(grad_overlay)
        for y in range(160, 400):
            alpha = int(255 * ((y - 160) / 240.0) ** 1.3)
            draw.line([(0, y), (1080, y)], fill=(11, 15, 25, alpha))
            
        bg_final = Image.alpha_composite(bg_canvas, grad_overlay)
        bg_final.convert("RGB").save(assets_dir / "header_bg.jpg", quality=95)
        print("Generated pristine assets/header_bg.jpg")

        # -------------------------------------------------------------
        # 2. Hassan Profile Cutout:
        # In the original, Hassan is at approx x=0..0.43*w, y=0.04*h..0.29*h
        # -------------------------------------------------------------
        prof_box = (int(w * 0.005), int(h * 0.045), int(w * 0.43), int(h * 0.295))
        profile = img.crop(prof_box)
        
        # Feather the right and top edges with an alpha mask so there's no harsh box edge
        pw, ph = profile.size
        mask = Image.new("L", (pw, ph), 255)
        mdraw = ImageDraw.Draw(mask)
        
        # Soften right edge (blend into background)
        for x in range(int(pw * 0.78), pw):
            fade = int(255 * (1.0 - (x - pw * 0.78) / (pw * 0.22)))
            for y in range(ph):
                curr = mask.getpixel((x, y))
                mask.putpixel((x, y), min(curr, fade))
                
        # Soften bottom edge
        for y in range(int(ph * 0.88), ph):
            fade = int(255 * (1.0 - (y - ph * 0.88) / (ph * 0.12)))
            for x in range(pw):
                curr = mask.getpixel((x, y))
                mask.putpixel((x, y), min(curr, fade))

        profile.putalpha(mask)
        profile.save(assets_dir / "profile.png")
        print("Generated smoothed assets/profile.png")

if __name__ == "__main__":
    clean_assets()
