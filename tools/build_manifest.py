# -*- coding: utf-8 -*-
"""Scan the media folders and write assets/manifest.json.
Run automatically by GitHub Actions on every push that touches a media folder."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = {'.mp4', '.webm', '.mov', '.m4v'}
IMG = {'.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif', '.avif'}
FOLDERS = {'videos': ('commercial-videos', VIDEO), 'sites': ('websites-landing', IMG),
           'cards': ('business-cards', IMG), 'brand': ('logo-design', IMG), 'logos': ('client-logos', IMG)}
def files(folder, exts):
    p = os.path.join(ROOT, folder)
    if not os.path.isdir(p): return []
    return sorted(f for f in os.listdir(p) if os.path.splitext(f)[1].lower() in exts and not f.startswith('.'))
man = {k: files(*v) for k, v in FOLDERS.items()}
# poster = an image in the videos folder with the same name as the video
imgs = {os.path.splitext(f)[0]: f for f in files('commercial-videos', IMG)}
man['videoPosters'] = {v: imgs[os.path.splitext(v)[0]] for v in man['videos'] if os.path.splitext(v)[0] in imgs}
out = os.path.join(ROOT, 'assets', 'manifest.json')
with open(out, 'w', encoding='utf-8') as fh:
    json.dump(man, fh, ensure_ascii=False, indent=2)
print({k: (len(v)) for k, v in man.items()})
