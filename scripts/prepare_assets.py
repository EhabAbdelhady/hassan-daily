"""Asset preparation script: extracts high-fidelity components from the reference image."""

from pathlib import Path
from PIL import Image

def extract_assets():
    source_img_path = Path("/Users/ehab/.gemini/antigravity/brain/4c38aed3-44a6-4497-94bd-ad564df3488c/.user_uploaded/media_1791467956768_716ef27b.jpg")
    assets_dir = Path("/Users/ehab/Desktop/Antigravity Folder/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)

    if not source_img_path.exists():
        print(f"Source image not found at {source_img_path}")
        return

    with Image.open(source_img_path) as img:
        w, h = img.size
        print(f"Reference image dimensions: {w}x{h}")

        # 1. Header Background (top Cairo skyline)
        # In the original 1080x1350 image, the header is from top 0 to approx 375
        header_box = (0, 0, w, int(h * 0.285))
        header_bg = img.crop(header_box)
        header_bg.save(assets_dir / "header_bg.jpg", quality=95)
        print("Saved assets/header_bg.jpg")

        # 2. Hassan Profile Cutout
        # In the original image, Hassan is on the left side of the header
        profile_box = (int(w * 0.01), int(h * 0.05), int(w * 0.44), int(h * 0.29))
        profile_img = img.crop(profile_box)
        profile_img.save(assets_dir / "profile.png")
        print("Saved assets/profile.png")

        # 3. Gold Bars Icon (Card 1 icon - far left)
        gold_box = (int(w * 0.06), int(h * 0.295), int(w * 0.155), int(h * 0.345))
        gold_icon = img.crop(gold_box)
        gold_icon.save(assets_dir / "gold_bars.png")
        print("Saved assets/gold_bars.png")

        # 4. Bitcoin Icon (Card 2 icon)
        btc_box = (int(w * 0.305), int(h * 0.295), int(w * 0.395), int(h * 0.345))
        btc_icon = img.crop(btc_box)
        btc_icon.save(assets_dir / "bitcoin_logo.png")
        print("Saved assets/bitcoin_logo.png")

        # 5. Dollar Bills Icon (Card 3 icon)
        usd_box = (int(w * 0.525), int(h * 0.295), int(w * 0.62), int(h * 0.345))
        usd_icon = img.crop(usd_box)
        usd_icon.save(assets_dir / "dollar_bills.png")
        print("Saved assets/dollar_bills.png")

        # 6. Oil Barrel Icon (Card 4 icon - far right)
        oil_box = (int(w * 0.775), int(h * 0.295), int(w * 0.85), int(h * 0.345))
        oil_icon = img.crop(oil_box)
        oil_icon.save(assets_dir / "oil_barrel.png")
        print("Saved assets/oil_barrel.png")

if __name__ == "__main__":
    extract_assets()
