# WonderDwell - Dream Homes & Architecture Auto Poster 🏡

Automated daily dream home content poster for **Facebook Page** (`WonderDwell`) & **Instagram** (`@wonder_dwell`).

## ✨ Features
- 📸 Posts 1 dream home/architecture image daily at **4:00 PM IST** (10:30 UTC)
- 🤖 Gemini Vision AI analyzes each image, reads the home name, and writes a unique luxury architecture caption
- 📝 Caption includes: Home name, architectural style, materials, living experience, hashtags
- 🔄 Smart image queue system (auto-refills from backup pool)
- 📱 Simultaneous Facebook + Instagram dual-posting

## 📁 File Structure
```
WonderDwell/
├── auto_poster.py          # Main posting script
├── fb_config.json          # Page & IG account IDs
├── images_urls.txt         # Active image queue (Catbox URLs)
├── images_urls_backup.txt  # Backup pool (refills queue when empty)
├── used_urls.txt           # Posted images log
├── upload_all_images.py    # Batch watermark cleaner & Catbox uploader
└── .github/workflows/
    └── daily_post.yml      # GitHub Actions daily schedule
```

