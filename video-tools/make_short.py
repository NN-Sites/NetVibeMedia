# -*- coding: utf-8 -*-
"""NetVibeMedia – YouTube Short #1 (1080x1920, 30fps) – motion graphics rendered with Pillow, piped to ffmpeg."""
import math, os, subprocess, sys, wave, random, asyncio, argparse, shutil, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ap = argparse.ArgumentParser(description="NetVibeMedia – generate a YouTube Short with a Hebrew AI voice-over (edge-tts), perfectly synced.")
ap.add_argument("--out", default=os.path.join(HERE, "NetVibeMedia_Short_01.mp4"), help="final mp4 path")
ap.add_argument("--icon", default=os.path.join(ROOT, "brand", "logo-icon-512.png"), help="logo icon png")
ap.add_argument("--voice", default="he-IL-AvriNeural", choices=["he-IL-AvriNeural", "he-IL-HilaNeural"], help="Hebrew neural voice")
ap.add_argument("--rate", default="+14%", help="speech rate, e.g. +8%% (faster) or -5%%")
ap.add_argument("--music", type=float, default=0.55, help="background beat volume (0 = voice only)")
ap.add_argument("--engine", default="edge", choices=["edge", "files"], help="edge = edge-tts; files = use your own clips from --voice-dir (any TTS or a real recording)")
ap.add_argument("--voice-dir", default=os.path.join(HERE, "voice_custom"), help="folder with <scene>_<n>.wav/mp3 clips when --engine files (e.g. hook_0.wav)")
ap.add_argument("--pitch", default="+0Hz", help="edge-tts pitch, e.g. -4Hz (deeper) / +3Hz")
ap.add_argument("--no-fx", action="store_true", help="disable the voice polish chain (EQ + compression + light room)")
ap.add_argument("--no-voice", action="store_true", help="skip TTS (uses fixed timings)")
ARGS = ap.parse_args() if __name__ == "__main__" else ap.parse_args([])
OUT, ICON = ARGS.out, ARGS.icon
W, H, FPS = 1080, 1920, 30
LEAD, GAP, TAIL = 0.10, 0.10, 0.35   # seconds: voice starts LEAD after a scene begins, GAP between phrases, TAIL hold after voice

# One entry per scene: (name, minimum seconds, [voice-over phrases]).  Each phrase becomes its own audio clip,
# so the animation can be keyed to the exact moment each phrase starts. No prices in the voice-over.
SCRIPT = [
    ("hook",  1.4, ["בעל עסק?", "זה בשבילך!"]),
    ("web",   1.6, ["צריך אתר?", "או דף נחיתה שמביא לקוחות!"]),
    ("video", 1.6, ["עריכת סרטונים קצבית,", "וסרטוני פרסומת שעוצרים את הגלילה."]),
    ("brand", 1.5, ["לוגו וכרטיס ביקור,", "מעוצבים בדיוק למותג שלך."]),
    ("proof", 1.9, ["עשרות עסקים כבר בפנים.", "הצטרפו אליהם!"]),
    ("cta",   3.0, ["מוכנים להתחיל?", "כנסו לאתר, ונתחיל!"]),
]
SCENES, STARTS, CUES, PHRASE_FILES = [], [], {}, {}
DUR, N = 0.0, 0

def plan(phrase_durs):
    """Derive scene lengths + animation cues from the real voice-over durations (this is the sync)."""
    global SCENES, STARTS, CUES, DUR, N
    SCENES, STARTS, CUES = [], [], {}
    t0 = 0.0
    for (name, min_d, phrases) in SCRIPT:
        durs = phrase_durs[name]
        cue, cur = [], LEAD
        for d in durs:
            cue.append(cur); cur += d + GAP
        voice_end = cur - GAP
        scene_d = max(min_d, voice_end + TAIL)
        SCENES.append((name, scene_d)); STARTS.append(t0); CUES[name] = cue
        t0 += scene_d
    DUR = t0
    N = int(round(DUR * FPS))

INK = (11, 16, 32); WHITE = (255, 255, 255)
A = (79, 70, 229); B = (147, 51, 234); C = (219, 39, 119)
LIGHT = (247, 248, 255)

GV = os.path.join(HERE, "fonts", "GveretLevin-Regular.ttf")
AS = os.path.join(HERE, "fonts", "Assistant.ttf")
FONT_URLS = {
    GV: "https://github.com/google/fonts/raw/main/ofl/gveretlevin/GveretLevin-Regular.ttf",
    AS: "https://github.com/google/fonts/raw/main/ofl/assistant/Assistant%5Bwght%5D.ttf",
}
def ensure_fonts():
    os.makedirs(os.path.join(HERE, "fonts"), exist_ok=True)
    for p, u in FONT_URLS.items():
        if not os.path.exists(p):
            print("downloading font", os.path.basename(p))
            urllib.request.urlretrieve(u, p)
_fc = {}
def font(kind, size, wght=800):
    k = (kind, size, wght)
    if k not in _fc:
        if kind == "gv":
            _fc[k] = ImageFont.truetype(GV, size)
        else:
            f = ImageFont.truetype(AS, size)
            try: f.set_variation_by_axes([wght])
            except Exception: pass
            _fc[k] = f
    return _fc[k]

def isheb(t): return any(0x590 <= ord(c) <= 0x5ff for c in t)

def grad_img(w, h, stops=(A, B, C), diag=True):
    xs = np.linspace(0, 1, w)[None, :]
    ys = np.linspace(0, 1, h)[:, None]
    t = (xs * 0.7 + ys * 0.3) if diag else xs + ys * 0
    t = np.clip(t, 0, 1)
    out = np.zeros((h, w, 3), np.float32)
    seg = np.where(t < 0.55, 0, 1)
    u = np.where(t < 0.55, t / 0.55, (t - 0.55) / 0.45)[..., None]
    c0 = np.where(seg[..., None] == 0, np.array(stops[0]), np.array(stops[1]))
    c1 = np.where(seg[..., None] == 0, np.array(stops[1]), np.array(stops[2]))
    out = c0 + (c1 - c0) * u
    return Image.fromarray(out.astype(np.uint8), "RGB")

# ---------- text layers (RTL aware, cached) ----------
_tc = {}
def text_layer(text, kind, size, fill=WHITE, wght=800, gradient=False, stroke=0, stroke_fill=INK):
    key = (text, kind, size, fill if not gradient else "g", wght, stroke)
    if key in _tc: return _tc[key]
    f = font(kind, size, wght)
    toks = text.split(" ")
    vis = [t[::-1] if isheb(t) else t for t in toks]
    sp = f.getlength(" ")
    widths = [f.getlength(v) for v in vis]
    total = sum(widths) + sp * (len(toks) - 1)
    pad = int(size * 0.35) + stroke
    lw, lh = int(total + pad * 2), int(size * 1.7)
    mask = Image.new("L", (lw, lh), 0)
    d = ImageDraw.Draw(mask)
    cur = lw - pad
    base = int(size * 1.2)
    rtl = isheb(text)
    if rtl:
        for v, w_ in zip(vis, widths):
            d.text((cur - w_, base), v, font=f, fill=255, anchor="ls"); cur -= w_ + sp
    else:
        x = pad
        d.text((x, base), text, font=f, fill=255, anchor="ls")
    layer = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    if stroke:
        sm = mask.filter(ImageFilter.MaxFilter(stroke * 2 + 1))
        layer.paste(Image.new("RGBA", (lw, lh), stroke_fill + (255,)), (0, 0), sm)
    if gradient:
        g = grad_img(lw, lh).convert("RGBA")
        layer.paste(g, (0, 0), mask)
    else:
        layer.paste(Image.new("RGBA", (lw, lh), tuple(fill) + (255,)), (0, 0), mask)
    _tc[key] = layer
    return layer

def put(canvas, layer, cx, cy, scale=1.0, rot=0.0, alpha=1.0, maxw=900):
    if alpha <= 0.01 or scale <= 0.01: return
    if layer.width > maxw: scale *= maxw / layer.width
    im = layer
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    canvas.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(t): t = clamp(t); return 1 - (1 - t) ** 3
def ob(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def seg(t, a, b): return clamp((t - a) / (b - a))

# ---------- backgrounds ----------
def blobs(img, items):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for (x, y, r, col, al) in items:
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (al,))
    ov = ov.filter(ImageFilter.GaussianBlur(120))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

BG_GRAD = grad_img(W, H)
BG_LIGHT = blobs(Image.new("RGB", (W, H), LIGHT), [(150, 250, 420, A, 70), (950, 700, 380, C, 55), (200, 1700, 460, (6, 182, 212), 50), (900, 1850, 420, B, 55)])
d_ = ImageDraw.Draw(BG_LIGHT)
for gx in range(0, W, 60): d_.line([(gx, 0), (gx, H)], fill=(232, 235, 250), width=1)
for gy in range(0, H, 60): d_.line([(0, gy), (W, gy)], fill=(232, 235, 250), width=1)
BG_DARK = blobs(Image.new("RGB", (W, H), INK), [(200, 300, 520, B, 120), (950, 1500, 520, C, 100), (100, 1700, 420, A, 110)])

def bg(name, t=0.0):
    base = {"grad": BG_GRAD, "light": BG_LIGHT, "dark": BG_DARK}[name]
    return base.copy()

def rrect(canvas, box, r, fill=None, outline=None, width=0):
    ImageDraw.Draw(canvas).rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def shadowed_card(canvas, box, r, fill=WHITE, blur=40, off=26, col=(79, 70, 229), al=70):
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((box[0], box[1] + off, box[2], box[3] + off), radius=r, fill=col + (al,))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(sh, (0, 0), sh)
    rrect(canvas, box, r, fill=fill)

ICON_IMG = Image.open(ICON).convert("RGBA")
def icon_layer(size):
    return ICON_IMG.resize((size, size), Image.LANCZOS)

def pill(canvas, cx, cy, text, kind="as", size=58, fg=WHITE, bgc=INK, padx=48, pady=22, wght=800, grad=False, scale=1.0, alpha=1.0, rot=0):
    tl = text_layer(text, kind, size, fill=fg, wght=wght)
    tw = int(tl.width - size * 0.5) + padx * 2
    th = int(size * 1.0) + pady * 2
    lay = Image.new("RGBA", (tw + 8, th + 8), (0, 0, 0, 0))
    if grad:
        g = grad_img(tw, th).convert("RGBA")
        m = Image.new("L", (tw, th), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, tw - 1, th - 1), radius=th // 2, fill=255)
        lay.paste(g, (4, 4), m)
    else:
        ImageDraw.Draw(lay).rounded_rectangle((4, 4, tw + 3, th + 3), radius=th // 2, fill=bgc + (255,))
    lay.paste(tl, ((lay.width - tl.width) // 2, (lay.height - tl.height) // 2 - int(size * 0.1)), tl)
    put(canvas, lay, cx, cy, scale, rot, alpha)

def sparkle(canvas, cx, cy, r, col=WHITE, rot=0):
    lay = Image.new("RGBA", (int(r * 2 + 4), int(r * 2 + 4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); c = r + 2
    pts = [(c, c - r), (c + r * .22, c - r * .22), (c + r, c), (c + r * .22, c + r * .22), (c, c + r), (c - r * .22, c + r * .22), (c - r, c), (c - r * .22, c - r * .22)]
    d.polygon(pts, fill=col + (255,))
    put(canvas, lay, cx, cy, 1, rot)

def heart(canvas, cx, cy, s, col=C, alpha=1.0):
    lay = Image.new("RGBA", (int(s * 2.4), int(s * 2.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); o = s * 1.2
    r = s * 0.5
    d.ellipse((o - s * .95, o - s * .9, o - s * .95 + 2 * r * 1.0 + 0, o - s * .9 + 2 * r), fill=col + (255,))
    d.ellipse((o - 0.05 * s, o - s * .9, o - 0.05 * s + 2 * r, o - s * .9 + 2 * r), fill=col + (255,))
    d.polygon([(o - s * .93, o - s * .3), (o + s * .93, o - s * .3), (o, o + s * .95)], fill=col + (255,))
    put(canvas, lay, cx, cy, 1, 0, alpha)

def check_circle(canvas, cx, cy, r, scale=1.0, col=None):
    lay = Image.new("RGBA", (r * 2 + 8, r * 2 + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    g = grad_img(r * 2, r * 2).convert("RGBA")
    m = Image.new("L", (r * 2, r * 2), 0); ImageDraw.Draw(m).ellipse((0, 0, r * 2 - 1, r * 2 - 1), fill=255)
    lay.paste(g, (4, 4), m)
    c = r + 4
    d.line([(c - r * .42, c + r * .02), (c - r * .1, c + r * .34), (c + r * .45, c - r * .3)], fill=WHITE + (255,), width=max(4, int(r * .18)), joint="curve")
    put(canvas, lay, cx, cy, scale)

def cursor(canvas, x, y, scale=1.0):
    lay = Image.new("RGBA", (90, 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.polygon([(8, 6), (8, 80), (28, 62), (42, 96), (56, 90), (42, 58), (68, 58)], fill=INK + (255,), outline=WHITE + (255,))
    put(canvas, lay, x + 30, y + 42, scale)

# ---------- scenes ----------
def s_hook(t, d):
    q = CUES["hook"][1]
    cv = bg("grad")
    dr = ImageDraw.Draw(cv)
    # rotating sparkles
    for i, (x, y, r, sp) in enumerate([(160, 330, 46, 120), (930, 520, 34, -150), (140, 1500, 38, 90), (950, 1430, 52, -110), (880, 260, 26, 160)]):
        a = ob(seg(t, 0.05 + i * .05, .45))
        sparkle(cv, x, y, r * a, (255, 255, 255), t * sp)
    s = ob(seg(t, 0.0, 0.38))
    shake = (math.sin(t * 60) * 6 * (1 - seg(t, .38, .7))) if t > .38 else 0
    pulse = 1 + 0.025 * math.sin(t * 12) * seg(t, .5, 1)
    put(cv, text_layer("בעל עסק?", "gv", 270, WHITE, stroke=0), W / 2 + shake, 800, s * pulse, -4 * (1 - eo(seg(t, 0, .4))))
    # underline swoosh
    w_ = int(700 * eo(seg(t, .35, .6)))
    if w_ > 0:
        dr.rounded_rectangle((W / 2 - w_ / 2, 955, W / 2 + w_ / 2, 975), radius=10, fill=(255, 255, 255))
    pill(cv, W / 2, 1180, "זה בשבילך", "as", 74, INK, WHITE, scale=ob(seg(t, q, q + .3)), alpha=eo(seg(t, q, q + .15)), rot=3)
    return cv

def browser(canvas, cx, cy, w, h, t):
    x0, y0 = int(cx - w // 2), int(cy - h // 2)
    shadowed_card(canvas, (x0, y0, x0 + w, y0 + h), 44)
    dr = ImageDraw.Draw(canvas)
    dr.rounded_rectangle((x0, y0, x0 + w, y0 + 90), radius=44, fill=(241, 243, 251))
    dr.rectangle((x0, y0 + 50, x0 + w, y0 + 90), fill=(241, 243, 251))
    for i, col in enumerate([(251, 113, 133), (251, 191, 36), (52, 211, 153)]):
        dr.ellipse((x0 + 36 + i * 38, y0 + 32, x0 + 58 + i * 38, y0 + 54), fill=col)
    dr.rounded_rectangle((x0 + 190, y0 + 24, x0 + w - 40, y0 + 66), radius=21, fill=WHITE)
    # hero skeleton fills in
    p1 = eo(seg(t, .15, .55)); p2 = eo(seg(t, .3, .7)); p3 = eo(seg(t, .45, .85))
    g = grad_img(int((w - 120) * 0.8), 56)
    m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, g.size[0] - 1, 55), radius=28, fill=255)
    canvas.paste(g, (x0 + 60, y0 + 150), m.point(lambda v: int(v * 1)) if p1 > .99 else Image.fromarray((np.array(m) * (np.arange(g.size[0])[None, :] < g.size[0] * p1)).astype(np.uint8)))
    for k, (yy, frac, pp) in enumerate([(240, 0.9, p2), (290, 0.6, p3)]):
        ww = int((w - 120) * frac * pp)
        if ww > 4: dr.rounded_rectangle((x0 + 60, y0 + yy, x0 + 60 + ww, y0 + yy + 26), radius=13, fill=(222, 226, 244))
    # CTA button
    bp = ob(seg(t, .6, .9))
    bw, bh = 330 * bp, 96 * bp
    if bp > .02:
        gg = grad_img(int(bw) + 1, int(bh) + 1)
        mm = Image.new("L", gg.size, 0); ImageDraw.Draw(mm).rounded_rectangle((0, 0, gg.size[0] - 1, gg.size[1] - 1), radius=int(bh / 2), fill=255)
        canvas.paste(gg, (x0 + w - 60 - int(bw), y0 + 380), mm)
    # cards row
    for i in range(3):
        cp = ob(seg(t, .7 + i * .08, 1.0 + i * .08))
        ch = int(200 * cp)
        if ch > 4:
            col = [(238, 240, 255), (252, 231, 243), (238, 240, 255)][i]
            dr.rounded_rectangle((x0 + 60 + i * ((w - 120 - 40) // 3 + 20), y0 + 560 + (200 - ch), x0 + 60 + i * ((w - 120 - 40) // 3 + 20) + (w - 120 - 40) // 3, y0 + 760), radius=26, fill=col)
    return (x0, y0, bw, bh)

def s_web(t, d):
    q = CUES["web"][1]
    cv = bg("light")
    put(cv, text_layer("אתרים ודפי נחיתה", "gv", 150, gradient=True), W / 2, 330, ob(seg(t, 0, .35)), 0, eo(seg(t, 0, .2)))
    put(cv, text_layer("שמביאים לקוחות", "as", 80, INK, 800), W / 2, 470, 1, 0, eo(seg(t, .15, .4)) , ) if False else None
    sl = text_layer("שמביאים לקוחות", "as", 84, INK, 800)
    put(cv, sl, W / 2, 480 + 40 * (1 - eo(seg(t, q, q + .3))), 1, 0, eo(seg(t, q, q + .25)))
    yb = 1290 + 900 * (1 - eo(seg(t, .0, .5)))
    x0, y0, bw, bh = browser(cv, W / 2, int(yb), 960, 1000, t)
    # cursor to button
    tx, ty = x0 + 960 - 60 - 160, y0 + 380 + 48
    ck = q + .55
    cp = eo(seg(t, q + .1, q + .45))
    cx_, cy_ = tx + 360 * (1 - cp), ty + 420 * (1 - cp)
    if t > q + .05: cursor(cv, cx_, cy_, 1.0 - 0.15 * (1 if ck - .02 < t < ck + .08 else 0))
    # click ripple
    if ck < t < ck + .35:
        r = int(40 + 160 * seg(t, ck, ck + .35)); a = 1 - seg(t, ck, ck + .35)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse((tx - r, ty - r, tx + r, ty + r), outline=B + (int(255 * a),), width=8)
        cv.paste(ov, (0, 0), ov)
    # notification
    if t > ck + .05:
        pill(cv, 740, 800, "פנייה חדשה!", "as", 60, WHITE, bgc=INK, scale=ob(seg(t, ck + .05, ck + .3)), rot=-4)
        check_circle(cv, 520, 800, 42, ob(seg(t, ck + .1, ck + .35)))
    return cv

def s_video(t, d):
    q = CUES["video"][1]
    cv = bg("dark")
    put(cv, text_layer("סרטוני פרסומת", "gv", 160, WHITE), W / 2, 280, ob(seg(t, 0, .35)), 0, eo(seg(t, 0, .2)))
    pill(cv, W / 2, 440, "עריכה קצבית שעוצרת גלילה", "as", 58, WHITE, grad=True, scale=ob(seg(t, q, q + .3)), alpha=eo(seg(t, q, q + .2)))
    # phone
    px, py, pw, ph = W / 2, 1150 + 700 * (1 - eo(seg(t, 0, .5))), 560, 1020
    x0, y0 = int(px - pw / 2), int(py - ph / 2)
    shadowed_card(cv, (x0, y0, x0 + pw, y0 + ph), 78, fill=(20, 24, 44), blur=50, off=30, col=(147, 51, 234), al=110)
    scr = (x0 + 22, y0 + 22, x0 + pw - 22, y0 + ph - 22)
    g = grad_img(scr[2] - scr[0], scr[3] - scr[1])
    m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, g.size[0] - 1, g.size[1] - 1), radius=58, fill=255)
    cv.paste(g, (scr[0], scr[1]), m)
    dr = ImageDraw.Draw(cv)
    # play button pulsing
    pr = 110 * (1 + 0.08 * math.sin(t * 14))
    cxp, cyp = x0 + pw / 2, y0 + ph / 2 - 40
    dr.ellipse((cxp - pr, cyp - pr, cxp + pr, cyp + pr), fill=(255, 255, 255))
    dr.polygon([(cxp - 34, cyp - 56), (cxp - 34, cyp + 56), (cxp + 62, cyp)], fill=B)
    # progress bar
    pb = x0 + 60; pe = x0 + pw - 60; yy = y0 + ph - 110
    dr.rounded_rectangle((pb, yy, pe, yy + 14), radius=7, fill=(255, 255, 255, 90) if False else (200, 170, 235))
    dr.rounded_rectangle((pb, yy, pb + (pe - pb) * clamp(t / d), yy + 14), radius=7, fill=WHITE)
    # equalizer
    for i in range(7):
        h_ = 30 + 70 * abs(math.sin(t * 9 + i * .9))
        dr.rounded_rectangle((x0 + 90 + i * 34, y0 + ph - 190 - h_, x0 + 112 + i * 34, y0 + ph - 190), radius=8, fill=(255, 255, 255))
    # floating hearts
    for i in range(6):
        tt = (t * 0.9 + i * .17) % 1.0
        if t > .45:
            heart(cv, x0 + pw + 40 - 60 * math.sin(tt * 6 + i), y0 + ph - 150 - tt * 700, 26 + (i % 3) * 8, C if i % 2 else (255, 130, 190), 1 - tt)
    # side sparkle
    sparkle(cv, 140, 900, 36 * ob(seg(t, .3, .6)), (255, 255, 255), t * 120)
    sparkle(cv, 960, 700, 28 * ob(seg(t, .4, .7)), (200, 160, 255), -t * 140)
    return cv

def s_brand(t, d):
    q = CUES["brand"][1]
    cv = bg("light")
    put(cv, text_layer("לוגו וכרטיס ביקור", "gv", 150, gradient=True), W / 2, 300, ob(seg(t, 0, .35)), 0, eo(seg(t, 0, .2)))
    sl = text_layer("מעוצבים בדיוק למותג שלך", "as", 70, INK, 800)
    put(cv, sl, W / 2, 440, 1, 0, eo(seg(t, q, q + .28)))
    # logo tile
    ls = ob(seg(t, .1, .55))
    put(cv, icon_layer(380), W / 2, 850, ls, (1 - eo(seg(t, .1, .6))) * -180)
    # business card
    cp = eo(seg(t, q - .05, q + .4))
    cx = W / 2 + (1 - cp) * 1100
    cw, ch = 800, 470
    card = Image.new("RGBA", (cw + 120, ch + 120), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((60, 80, 60 + cw, 80 + ch), radius=40, fill=(79, 70, 229, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(26)); card.alpha_composite(sh)
    g = grad_img(cw, ch); mk = Image.new("L", (cw, ch), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, cw - 1, ch - 1), radius=40, fill=255)
    card.paste(g, (60, 60), mk)
    cd = ImageDraw.Draw(card)
    ic = icon_layer(120); card.alpha_composite(ic, (60 + cw - 160, 60 + 40))
    cd.rounded_rectangle((60 + 60, 60 + 280, 60 + 60 + 360, 60 + 280 + 22), radius=11, fill=(255, 255, 255, 235))
    cd.rounded_rectangle((60 + 60, 60 + 330, 60 + 60 + 250, 60 + 330 + 18), radius=9, fill=(255, 255, 255, 170))
    cd.rounded_rectangle((60 + 60, 60 + 370, 60 + 60 + 300, 60 + 370 + 18), radius=9, fill=(255, 255, 255, 170))
    put(cv, card, cx, 1330 + 8 * math.sin(t * 6), 1, -7 * cp + 2 * math.sin(t * 5) * (1 if t > .9 else 0))
    for (x, y, r, sp, a0) in [(150, 700, 34, 130, .5), (940, 1000, 40, -120, .62), (200, 1650, 28, 150, .7)]:
        sparkle(cv, x, y, r * ob(seg(t, a0, a0 + .3)), (147, 51, 234), t * sp)
    return cv

def s_proof(t, d):
    q = CUES["proof"][1]
    cv = bg("dark")
    put(cv, text_layer("עשרות", "gv", 330, gradient=True), W / 2, 330, ob(seg(t, 0, .35)), -3 * (1 - eo(seg(t, 0, .4))), eo(seg(t, 0, .15)))
    put(cv, text_layer("עסקים כבר בפנים", "gv", 150, WHITE), W / 2, 560, ob(seg(t, .2, .55)), 0, eo(seg(t, .2, .4)))
    # grid of badges
    cols, rows = 4, 4
    gap = 40; size = 150
    gx0 = (W - (cols * size + (cols - 1) * gap)) / 2 + size / 2
    gy0 = 880
    k = 0
    for r in range(rows):
        for c in range(cols):
            st = .35 + k * .055
            sc = ob(seg(t, st, st + .28))
            cxx = gx0 + c * (size + gap); cyy = gy0 + r * (size + gap)
            if sc > 0.02:
                ov = Image.new("RGBA", (size + 20, size + 20), (0, 0, 0, 0))
                ImageDraw.Draw(ov).rounded_rectangle((10, 10, size + 10, size + 10), radius=40, fill=(30, 36, 66, 255), outline=(90, 80, 160, 255), width=4)
                put(cv, ov, cxx, cyy, sc)
                check_circle(cv, int(cxx), int(cyy), 46, sc * (1 + 0.04 * math.sin(t * 10 + k)))
            k += 1
    pill(cv, W / 2, 1600, "הצטרפו אליהם", "as", 76, WHITE, grad=True, scale=ob(seg(t, q, q + .3)), alpha=eo(seg(t, q, q + .2)), rot=-2)
    return cv

def s_cta(t, d):
    q = CUES["cta"][1]
    cv = bg("grad")
    for i, (x, y, r, sp) in enumerate([(150, 260, 40, 110), (940, 380, 30, -140), (120, 1550, 36, 100), (960, 1620, 46, -90)]):
        sparkle(cv, x, y, r * ob(seg(t, .05 + i * .06, .45)), (255, 255, 255), t * sp)
    put(cv, text_layer("מוכנים להתחיל?", "gv", 200, WHITE), W / 2, 380, ob(seg(t, 0, .35)), 0, eo(seg(t, 0, .2)))
    # logo + name
    lp = ob(seg(t, .25, .65))
    put(cv, icon_layer(300), W / 2, 790, lp, (1 - eo(seg(t, .25, .65))) * 120)
    put(cv, text_layer("NetVibeMedia", "as", 118, WHITE, 800), W / 2, 1030, 1, 0, eo(seg(t, .5, .8)))
    # button
    bp = ob(seg(t, q, q + .35)); pul = 1 + 0.04 * math.sin(t * 10) * seg(t, q + .3, q + .5)
    pill(cv, W / 2, 1290, "כנסו לאתר", "gv", 130, INK, WHITE, padx=110, pady=40, scale=bp * pul, alpha=eo(seg(t, q, q + .2)))
    # arrow bounce
    ab = 14 * math.sin(t * 9)
    dr = ImageDraw.Draw(cv)
    if t > q + .35:
        ax, ay = W / 2, 1480 + ab
        a = eo(seg(t, q + .35, q + .55))
        col = (255, 255, 255)
        dr.polygon([(ax - 44, ay), (ax + 44, ay), (ax, ay + 56)], fill=col)
        dr.rounded_rectangle((ax - 14, ay - 70, ax + 14, ay + 4), radius=8, fill=col)
    put(cv, text_layer("nn-sites.github.io/NetVibeMedia", "as", 56, WHITE, 700), W / 2, 1700, 1, 0, eo(seg(t, q + .5, q + .85)))
    return cv

FN = {"hook": s_hook, "web": s_web, "video": s_video, "brand": s_brand, "proof": s_proof, "cta": s_cta}

def wipe(cv, t_global):
    for b in STARTS[1:]:
        dt = t_global - b
        if -0.13 < dt < 0.13:
            p = (dt + 0.13) / 0.26
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            x = -W * 1.2 + p * (W * 2.4)
            g = grad_img(int(W * 1.2), H, diag=True).convert("RGBA")
            # skewed panel
            sk = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sk.paste(g, (int(x), 0))
            cv.paste(sk, (0, 0), sk)
    return cv

PREVIEW = set()
def render_video(path):
    os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
    PREVIEW.update(int(N * f) for f in (0.03, 0.12, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.95))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    sample = {}
    for i in range(N):
        tg = i / FPS
        si = max(j for j, s in enumerate(STARTS) if tg >= s - 1e-9)
        name, d = SCENES[si]
        cv = FN[name](tg - STARTS[si], d)
        cv = wipe(cv.convert("RGB"), tg)
        pr.stdin.write(cv.tobytes())
        if i in PREVIEW:
            cv.save(os.path.join(HERE, "preview", f"frame_{i:03d}.png"))
        if i % 30 == 0: print("frame", i, "/", N, flush=True)
    pr.stdin.close(); pr.wait()

# ---------- audio ----------
def audio(path, voice=None):
    sr = 44100
    n = int(DUR * sr)
    L = np.zeros(n, np.float32)
    rng = np.random.default_rng(7)
    bpm = 128; beat = 60 / bpm
    def add(sig, t0, gain=1.0):
        i0 = int(t0 * sr)
        if i0 >= n: return
        j = min(n, i0 + len(sig))
        L[i0:j] += sig[: j - i0] * gain
    def kick():
        tt = np.arange(int(.28 * sr)) / sr
        f = 120 * np.exp(-tt * 18) + 42
        return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 9)
    def hat():
        tt = np.arange(int(.05 * sr)) / sr
        x = rng.standard_normal(len(tt)); x = np.diff(x, prepend=0)
        return x * np.exp(-tt * 70) * .5
    def clap():
        tt = np.arange(int(.18 * sr)) / sr
        x = rng.standard_normal(len(tt))
        env = np.exp(-tt * 28) * (1 + .8 * (np.sin(tt * 300) > 0))
        return x * env * .35
    def bass(freq, dur=.22):
        tt = np.arange(int(dur * sr)) / sr
        return (np.sin(2 * np.pi * freq * tt) + .35 * np.sin(4 * np.pi * freq * tt)) * np.exp(-tt * 6) * .5
    def whoosh(dur=.4):
        tt = np.arange(int(dur * sr)) / sr
        x = rng.standard_normal(len(tt))
        k = np.exp(-((tt - dur / 2) ** 2) / (2 * (dur / 5) ** 2))
        # crude low->high sweep via moving average shrinking
        y = np.convolve(x, np.ones(30) / 30, "same") * (1 - tt / dur) + np.diff(x, prepend=0) * (tt / dur)
        return y * k * .5
    def pop(freq=520):
        tt = np.arange(int(.12 * sr)) / sr
        return np.sin(2 * np.pi * (freq + 900 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 28) * .6
    nb = int(DUR / beat) + 1
    notes = [55.0, 55.0, 82.41, 55.0, 65.41, 65.41, 98.0, 73.42]
    for b in range(nb):
        t0 = b * beat
        add(kick(), t0, .95)
        if b % 2 == 1: add(clap(), t0, .7)
        add(hat(), t0 + beat / 2, .5)
        add(hat(), t0 + beat / 4, .22); add(hat(), t0 + beat * .75, .22)
        add(bass(notes[b % len(notes)]), t0 + beat / 2, .55)
    # pops on scene entrances and sfx on wipes
    for s in STARTS:
        add(pop(480), s + 0.02, .8)
        add(pop(700), s + 0.35, .5)
    for s in STARTS[1:]:
        add(whoosh(), s - 0.2, .9)
    # soft arpeggio on CTA
    for i, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
        tt = np.arange(int(.35 * sr)) / sr
        add(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 7) * .35, STARTS[-1] + .3 + i * .12, .6)
    # fade out
    fo = int(.35 * sr); L[-fo:] *= np.linspace(1, 0, fo)
    L = np.tanh(L * 1.1)
    L = L / (np.max(np.abs(L)) + 1e-6) * .85 * ARGS.music
    if voice is not None:
        # sidechain-style ducking: the beat dips while the narrator speaks
        env = np.convolve(np.abs(voice), np.ones(2205) / 2205, "same")
        env = np.clip(env * 7, 0, 1)
        L = L * (1 - .6 * env) + voice
        L = L / max(1.0, np.max(np.abs(L)) / .92)
    pcm = (L * 32767).astype(np.int16)
    st = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes())


# ---------- voice-over (edge-tts) ----------
def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode().strip()
    return float(out)

async def _tts(text, path):
    import edge_tts
    await edge_tts.Communicate(text, ARGS.voice, rate=ARGS.rate, pitch=ARGS.pitch).save(path)

def make_voice_clips():
    vdir = os.path.join(HERE, "voice"); os.makedirs(vdir, exist_ok=True)
    durs = {}
    for name, _, phrases in SCRIPT:
        durs[name] = []
        PHRASE_FILES[name] = []
        for k, text in enumerate(phrases):
            p = os.path.join(vdir, f"{name}_{k}.mp3")
            if ARGS.engine == "files" and not ARGS.no_voice:
                found = [os.path.join(ARGS.voice_dir, f"{name}_{k}{e}") for e in (".wav", ".mp3", ".m4a", ".flac")]
                found = [f for f in found if os.path.exists(f)]
                if not found: sys.exit(f"missing clip for {name}_{k}: put {name}_{k}.wav in {ARGS.voice_dir}")
                durs[name].append(len(decode_mono(found[0])) / 44100); PHRASE_FILES[name].append(found[0]); continue
            if ARGS.no_voice:
                durs[name].append(0.9 + 0.05 * len(text.split()))
                continue
            asyncio.run(_tts(text, p))
            durs[name].append(len(decode_mono(p)) / 44100)   # spoken length only (silence trimmed)
            PHRASE_FILES[name].append(p)
    return durs

def decode_mono(path, sr=44100):
    fx = [] if ARGS.no_fx else ["-af", "highpass=f=85,equalizer=f=220:t=q:w=1:g=1.5,equalizer=f=3400:t=q:w=1.2:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=6:release=90:makeup=3,aecho=0.85:0.5:28:0.10"]
    raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", path] + fx + ["-f", "f32le", "-ac", "1", "-ar", str(sr), "-"])
    x = np.frombuffer(raw, np.float32).copy()
    # trim leading/trailing silence so the cue time == the first spoken syllable
    nz = np.where(np.abs(x) > 0.01)[0]
    if len(nz): x = x[max(0, nz[0] - int(.02 * sr)): nz[-1] + int(.04 * sr)]
    pk = np.max(np.abs(x)) + 1e-6
    return x / pk * .9

def build_voice(sr=44100):
    v = np.zeros(int(DUR * sr) + sr, np.float32)
    for si, (name, _, phrases) in enumerate(SCRIPT):
        for k, p in enumerate(PHRASE_FILES.get(name, [])):
            x = decode_mono(p)
            i0 = int((STARTS[si] + CUES[name][k]) * sr)
            v[i0:i0 + len(x)] += x[: len(v) - i0]
    return v[: int(DUR * sr)]

def report(durs):
    print(f"voice={ARGS.voice} rate={ARGS.rate}")
    for si, (name, d) in enumerate(SCENES):
        cs = ", ".join(f"{STARTS[si] + c:5.2f}s" for c in CUES[name])
        print(f"  scene {name:6s} start {STARTS[si]:5.2f}s len {d:4.2f}s | phrase starts: {cs} | phrase lens: {', '.join('%.2f' % x for x in durs[name])}")
    print(f"  total {DUR:.2f}s = {N} frames @ {FPS}fps")

if __name__ == "__main__":
    ensure_fonts()
    durs = make_voice_clips()
    plan(durs)
    report(durs)
    tmpv = os.path.join(HERE, "_video_noaudio.mp4"); wav = os.path.join(HERE, "_mix.wav")
    voice = None if ARGS.no_voice else build_voice()
    audio(wav, voice)
    render_video(tmpv)
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", tmpv, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                           "-t", f"{DUR:.3f}", "-movflags", "+faststart", OUT])
    for f in (tmpv, wav):
        try: os.remove(f)
        except OSError: pass
    print("done ->", OUT, f"({probe(OUT):.2f}s)")
