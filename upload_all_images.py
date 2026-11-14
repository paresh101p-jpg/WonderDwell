import cv2
import os
import sys
import json
import time
import zipfile
import numpy as np
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(r"E:\Paresh\Auto Post\WonderDwell")
IMAGES_DIR = BASE_DIR / "images"
EXTRACT_DIR = BASE_DIR / "images" / "extracted"
QUEUE_FILE = BASE_DIR / "images_urls.txt"
BACKUP_FILE = BASE_DIR / "images_urls_backup.txt"
MAPPING_FILE = BASE_DIR / "uploaded_files_map.json"

# Exact Flow star watermark polygon (896x1200)
cx, cy = 795, 1099
pts = np.array([
    [cx, cy - 31],       # top (795, 1068)
    [cx + 10, cy - 13],  # top-right (805, 1086)
    [cx + 25, cy],       # right (820, 1099)
    [cx + 10, cy + 13],  # bottom-right (805, 1112)
    [cx, cy + 31],       # bottom (795, 1130)
    [cx - 10, cy + 13],  # bottom-left (785, 1112)
    [cx - 25, cy],       # left (770, 1099)
    [cx - 10, cy - 13],  # top-left (785, 1086)
], np.int32)

mask = np.zeros((1200, 896), dtype=np.uint8)
cv2.fillPoly(mask, [pts], 255)
mask = cv2.dilate(mask, np.ones((7, 7), np.uint8), iterations=1)

def extract_zip_if_any():
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    for f in os.listdir(IMAGES_DIR):
        if f.lower().endswith(".zip"):
            zip_p = IMAGES_DIR / f
            print(f"Extracting zip file: {f}...")
            with zipfile.ZipFile(zip_p, 'r') as z:
                z.extractall(EXTRACT_DIR)
            print("Extraction complete.")

def clean_watermark(img):
    """Clean the Flow watermark without cropping."""
    if img.shape[0] == 1200 and img.shape[1] == 896:
        return cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    return img

def upload_to_catbox(image_bytes, retries=3):
    """Upload jpeg bytes to Catbox.moe with retry."""
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload"}
    files = {"fileToUpload": ("dream_home.jpg", image_bytes, "image/jpeg")}
    
    for attempt in range(retries):
        try:
            r = requests.post(url, data=data, files=files, timeout=40)
            if r.status_code == 200 and r.text.strip().startswith("http"):
                return r.text.strip()
        except Exception:
            time.sleep(1)
    return None

def process_file(file_path):
    img = cv2.imdecode(np.fromfile(str(file_path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return file_path.name, None
    
    cleaned = clean_watermark(img)
    _, buf = cv2.imencode(".jpg", cleaned, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    url = upload_to_catbox(buf.tobytes())
    return file_path.name, url

def main():
    extract_zip_if_any()
    
    # Collect all image files
    files = []
    if EXTRACT_DIR.exists():
        files.extend([EXTRACT_DIR / f for f in os.listdir(EXTRACT_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    files.extend([IMAGES_DIR / f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    files = sorted(list(set(files)))
    
    print(f"Total home images found: {len(files)}")
    if not files:
        print("No images found in images folder yet.")
        return

    uploaded_map = {}
    if MAPPING_FILE.exists():
        try:
            with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                uploaded_map = json.load(f)
        except Exception:
            uploaded_map = {}

    pending = [f for f in files if f.name not in uploaded_map]
    print(f"Already uploaded: {len(uploaded_map)} | Remaining to process: {len(pending)}")
    
    if not pending:
        print("All images are already uploaded!")
        return

    print(f"Starting upload for {len(pending)} images with 12 workers...")
    newly_uploaded = 0
    save_counter = 0

    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(process_file, f): f for f in pending}
        for fut in as_completed(futures):
            fname, url = fut.result()
            if url:
                uploaded_map[fname] = url
                newly_uploaded += 1
                save_counter += 1
                if newly_uploaded % 10 == 0 or newly_uploaded == len(pending):
                    print(f"Progress: [{newly_uploaded}/{len(pending)}] - Latest: {url}")
                
                if save_counter >= 25:
                    with open(MAPPING_FILE, "w", encoding="utf-8") as mf:
                        json.dump(uploaded_map, mf, indent=2)
                    all_urls = list(dict.fromkeys(list(uploaded_map.values())))
                    with open(QUEUE_FILE, "w", encoding="utf-8") as qf:
                        qf.write("\n".join(all_urls) + "\n")
                    with open(BACKUP_FILE, "w", encoding="utf-8") as bf:
                        bf.write("\n".join(all_urls) + "\n")
                    save_counter = 0

    with open(MAPPING_FILE, "w", encoding="utf-8") as mf:
        json.dump(uploaded_map, mf, indent=2)
    all_urls = list(dict.fromkeys(list(uploaded_map.values())))
    with open(QUEUE_FILE, "w", encoding="utf-8") as qf:
        qf.write("\n".join(all_urls) + "\n")
    with open(BACKUP_FILE, "w", encoding="utf-8") as bf:
        bf.write("\n".join(all_urls) + "\n")

    print(f"\nALL DONE! Total uploaded images in pool: {len(all_urls)}")

if __name__ == "__main__":
    main()
