"""Process user assets: generate header background and cut out backgrounds for icons and profile using lightweight u2netp model (4.7MB)."""

from pathlib import Path
from PIL import Image, ImageDraw
import rembg
import shutil

def process_all_assets():
    assets_dir = Path("/Users/ehab/Desktop/Antigravity Folder/assets")
    brain_dir = Path("/Users/ehab/.gemini/antigravity/brain/4c38aed3-44a6-4497-94bd-ad564df3488c")
    
    # Initialize lightweight session (u2netp is only 4.7 MB)
    print("Initializing lightweight u2netp model...")
    session = rembg.new_session("u2netp")

    # 1. Header Background from generated Cairo Sunset
    skyline_path = brain_dir / "cairo_skyline_sunset_1791470508642.jpg"
    if skyline_path.exists():
        print("Processing header background from Cairo sunset...")
        with Image.open(skyline_path) as sky:
            sw, sh = sky.size
            target_w, target_h = 1080, 420
            
            aspect = target_w / target_h
            if sw / sh > aspect:
                new_w = int(sh * aspect)
                left = (sw - new_w) // 2
                sky_crop = sky.crop((left, 0, left + new_w, sh))
            else:
                new_h = int(sw / aspect)
                top = 0
                sky_crop = sky.crop((0, top, sw, top + new_h))
                
            sky_resized = sky_crop.resize((target_w, target_h), Image.Resampling.LANCZOS).convert("RGBA")
            
            # Subtle gradient overlay for date & branding contrast
            grad = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(grad)
            for y in range(160, target_h):
                alpha = int(255 * ((y - 160) / (target_h - 160)) ** 1.3)
                draw.line([(0, y), (target_w, y)], fill=(11, 15, 25, min(240, alpha)))
                
            final_header = Image.alpha_composite(sky_resized, grad)
            final_header.convert("RGB").save(assets_dir / "header_bg.jpg", quality=95)
            print("Saved assets/header_bg.jpg")

    # 2. Process Hassan Profile Cutout
    profile_path = assets_dir / "profile.png"
    if profile_path.exists():
        print("Removing background from Hassan profile...")
        backup_path = assets_dir / "profile_original.png"
        if not backup_path.exists():
            shutil.copy(profile_path, backup_path)
            
        with Image.open(backup_path) as pimg:
            cutout = rembg.remove(pimg, session=session)
            cutout.save(profile_path)
            print("Saved transparent cutout assets/profile.png")

    # 3. Process Gold Bars
    gold_path = assets_dir / "gold_bars.png"
    if gold_path.exists():
        print("Removing fake checkerboard from gold bars...")
        backup_gold = assets_dir / "gold_bars_raw.png"
        if not backup_gold.exists():
            shutil.copy(gold_path, backup_gold)
            
        with Image.open(backup_gold) as gimg:
            clean_gold = rembg.remove(gimg, session=session)
            clean_gold.save(gold_path)
            print("Saved transparent assets/gold_bars.png")

    # 4. Process Bitcoin Logo
    btc_path = assets_dir / "bitcoin_logo.png"
    if btc_path.exists():
        print("Removing white background from Bitcoin logo...")
        backup_btc = assets_dir / "bitcoin_logo_raw.png"
        if not backup_btc.exists():
            shutil.copy(btc_path, backup_btc)
            
        with Image.open(backup_btc) as bimg:
            clean_btc = rembg.remove(bimg, session=session)
            clean_btc.save(btc_path)
            print("Saved transparent assets/bitcoin_logo.png")

    # 5. Process Oil Barrel (AVIF -> PNG + transparent background)
    oil_path = assets_dir / "oil_barrel.png"
    if oil_path.exists():
        print("Processing oil barrel (convert to transparent PNG)...")
        backup_oil = assets_dir / "oil_barrel_raw.png"
        if not backup_oil.exists():
            shutil.copy(oil_path, backup_oil)
            
        with Image.open(backup_oil) as oimg:
            clean_oil = rembg.remove(oimg, session=session)
            clean_oil.save(oil_path)
            print("Saved transparent assets/oil_barrel.png")

    # 6. Ensure both dollar_bills.png and dolllar_bills.png exist
    dollar_3l = assets_dir / "dolllar_bills.png"
    dollar_2l = assets_dir / "dollar_bills.png"
    if dollar_3l.exists() and not dollar_2l.exists():
        shutil.copy(dollar_3l, dollar_2l)
        print("Created assets/dollar_bills.png alias from dolllar_bills.png")
    elif dollar_2l.exists() and not dollar_3l.exists():
        shutil.copy(dollar_2l, dollar_3l)

    print("All assets successfully processed!")

if __name__ == "__main__":
    process_all_assets()
