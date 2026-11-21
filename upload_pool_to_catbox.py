import os
import sys
import json
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(r"E:\Paresh\Auto Post\WonderDwell")
POOL_DIR = BASE_DIR / "images"
MAPPING_FILE = BASE_DIR / "catbox_uploaded_map.json"
QUEUE_FILE = BASE_DIR / "images_urls.txt"
BACKUP_FILE = BASE_DIR / "images_urls_backup.txt"
USED_FILE = BASE_DIR / "used_urls.txt"

def upload_single_file(file_path: Path, max_retries=4) -> tuple:
    fname = file_path.name
    url = "https://catbox.moe/user/api.php"
    
    for attempt in range(max_retries):
        try:
            with open(file_path, "rb") as f:
                files = {"fileToUpload": (fname, f, "image/jpeg")}
                data = {"reqtype": "fileupload"}
                r = requests.post(url, data=data, files=files, timeout=40)
            
            res_text = r.text.strip()
            if r.status_code == 200 and res_text.startswith("http"):
                return fname, res_text
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
        
    return fname, None

def main():
    if not POOL_DIR.exists():
        print("ERROR: images_pool directory not found!")
        sys.exit(1)
        
    files = sorted(list(POOL_DIR.glob("*.jpg")))
    print(f"Total images in pool to upload to Catbox: {len(files)}")
    
    # Load existing mapping if any
    uploaded_map = {}
    if MAPPING_FILE.exists():
        try:
            with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                uploaded_map = json.load(f)
        except Exception:
            uploaded_map = {}
            
    pending = [f for f in files if f.name not in uploaded_map or not uploaded_map[f.name]]
    print(f"Already uploaded to Catbox: {len(uploaded_map)} | Pending: {len(pending)}")
    
    if pending:
        print(f"Starting Catbox upload with 10 workers for {len(pending)} images...")
        success_count = len(uploaded_map)
        save_counter = 0
        t0 = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(upload_single_file, f): f for f in pending}
            for fut in as_completed(futures):
                fname, catbox_url = fut.result()
                if catbox_url:
                    uploaded_map[fname] = catbox_url
                    success_count += 1
                    save_counter += 1
                    if success_count % 25 == 0 or success_count == len(files):
                        print(f"[{success_count}/{len(files)}] Uploaded: {fname} -> {catbox_url}")
                    
                    if save_counter >= 30:
                        with open(MAPPING_FILE, "w", encoding="utf-8") as mf:
                            json.dump(uploaded_map, mf, indent=2)
                        save_counter = 0
                        
        with open(MAPPING_FILE, "w", encoding="utf-8") as mf:
            json.dump(uploaded_map, mf, indent=2)
        print(f"Upload complete in {time.time() - t0:.1f}s! Total mapped: {len(uploaded_map)}")
    else:
        print("All images are already uploaded in mapping file.")

    # Build queue and backup files
    # The file posted last night
    first_posted_name = "Aircraft_converted_into_tiny_home_5b2330e0.jpg"
    
    all_catbox_urls = []
    used_catbox_urls = []
    queue_catbox_urls = []
    
    for f in files:
        url = uploaded_map.get(f.name)
        if url:
            all_catbox_urls.append(url)
            if f.name == first_posted_name:
                used_catbox_urls.append(url)
            else:
                queue_catbox_urls.append(url)
                
    # Save active queue
    with open(QUEUE_FILE, "w", encoding="utf-8") as qf:
        qf.write("\n".join(queue_catbox_urls) + "\n")
        
    # Save master backup
    with open(BACKUP_FILE, "w", encoding="utf-8") as bf:
        bf.write("\n".join(all_catbox_urls) + "\n")
        
    # Save used
    with open(USED_FILE, "w", encoding="utf-8") as uf:
        uf.write("\n".join(used_catbox_urls) + "\n")
        
    print("\n" + "=" * 50)
    print(f"SUCCESS: {len(queue_catbox_urls)} Catbox URLs written to images_urls.txt")
    print(f"SUCCESS: {len(all_catbox_urls)} Catbox URLs written to images_urls_backup.txt")
    print(f"SUCCESS: {len(used_catbox_urls)} Catbox URLs written to used_urls.txt")
    print("=" * 50)

if __name__ == "__main__":
    main()

