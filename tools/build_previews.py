# -*- coding: utf-8 -*-
"""Create a small silent loop + a still image for every video in commercial-videos/.
These feed the moving gallery on videos.html. Requires ffmpeg; existing previews are kept.
To redo a preview, delete its files in commercial-videos/previews/ and run again."""
import os, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'commercial-videos')
OUT = os.path.join(SRC, 'previews')
VIDEO = {'.mp4', '.webm', '.mov', '.m4v'}
SECONDS = 6
# every tile is 9:16; wider videos are shown whole over a blurred copy of themselves
FRAME = ('split[a][b];'
         '[a]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=12:2,eq=brightness=-0.12[bg];'
         '[b]scale=270:480:force_original_aspect_ratio=decrease:force_divisible_by=2[fg];'
         '[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1')


def duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip() or 0)


def run(args, dest):
    tmp = dest + '.tmp' + os.path.splitext(dest)[1]
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + args + [tmp], check=True)
    os.replace(tmp, dest)


def build():
    if not (shutil.which('ffmpeg') and shutil.which('ffprobe')):
        print('ffmpeg not found - skipping previews')
        return
    os.makedirs(OUT, exist_ok=True)
    for name in sorted(os.listdir(SRC)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in VIDEO or name.startswith('.'):
            continue
        src = os.path.join(SRC, name)
        clip, still = os.path.join(OUT, name + '.mp4'), os.path.join(OUT, name + '.jpg')
        try:
            if os.path.exists(clip) and os.path.exists(still):
                continue
            # start a bit into the video, past fade-ins and title cards
            start = max(0, min(duration(src) * 0.2, duration(src) - SECONDS))
            run(['-ss', '%.2f' % start, '-t', str(SECONDS), '-i', src, '-an', '-vf', FRAME + ',fps=20',
                 '-c:v', 'libx264', '-preset', 'slow', '-crf', '30', '-profile:v', 'main',
                 '-pix_fmt', 'yuv420p', '-movflags', '+faststart'], clip)
            run(['-ss', str(SECONDS / 2), '-i', clip, '-frames:v', '1', '-q:v', '5'], still)
            print('preview:', name)
        except (subprocess.CalledProcessError, ValueError) as e:
            print('preview failed for', name, e)


if __name__ == '__main__':
    build()
