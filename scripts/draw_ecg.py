# -*- coding: utf-8 -*-
"""
绘制标准 ECG 波形图（P-QRS-T-U 全标注 + 间期）
依赖：numpy, Pillow
字体：文泉驿微米黑（wqy-microhei.ttc）放置在项目 fonts/ 目录，或通过环境变量 FONT_PATH 指定
输出：images/ecg_waveform.png
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 字体路径：优先环境变量，其次项目内 fonts 目录
FONT_PATH = os.environ.get("FONT_PATH")
if not FONT_PATH:
    _candidate = os.path.join(os.path.dirname(__file__), "..", "fonts", "wqy-microhei.ttc")
    if os.path.exists(_candidate):
        FONT_PATH = _candidate
if not FONT_PATH:
    raise FileNotFoundError(
        "未找到中文字体。请把 wqy-microhei.ttc 放到 fonts/ 目录，或设置环境变量 FONT_PATH 指向字体文件。"
    )

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "images", "ecg_waveform.png")

W, H = 1400, 620
BG = (255, 255, 255)
LINE = (23, 28, 45)
GRID = (230, 235, 245)
GRID_MAJOR = (200, 210, 228)
RED = (220, 60, 60)
BLUE = (40, 110, 200)
GREEN = (40, 150, 90)
ORANGE = (230, 130, 30)
PURPLE = (130, 70, 180)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def f(sz): return ImageFont.truetype(FONT_PATH, sz)
f_title = f(26); f_lbl = f(20); f_small = f(16)

ML, MR, MT, MB = 70, 70, 70, 80
PW, PH = W - ML - MR, H - MT - MB

total_ms = 2400
xscale = PW / total_ms
ybase = MT + PH * 0.55
mV_scale = 110

# 网格
t = 0
while t <= total_ms:
    x = ML + t * xscale
    d.line([(x, MT), (x, MT + PH)], fill=GRID, width=1)
    t += 40
t = 0
while t <= total_ms:
    x = ML + t * xscale
    d.line([(x, MT), (x, MT + PH)], fill=GRID_MAJOR, width=1)
    t += 200
v = -2.0
while v <= 2.0:
    y = ybase - v * mV_scale
    d.line([(ML, y), (ML + PW, y)], fill=GRID, width=1)
    v += 0.25
v = -2.0
while v <= 2.0:
    y = ybase - v * mV_scale
    d.line([(ML, y), (ML + PW, y)], fill=GRID_MAJOR, width=1)
    v += 0.5

def ecg_cycle(t_rel):
    v = 0.0
    v += 0.15 * np.exp(-((t_rel - 90) ** 2) / (2 * 28 ** 2))      # P
    v += -0.10 * np.exp(-((t_rel - 208) ** 2) / (2 * 6 ** 2))     # Q
    v += 1.20 * np.exp(-((t_rel - 222) ** 2) / (2 * 8 ** 2))     # R
    v += -0.30 * np.exp(-((t_rel - 236) ** 2) / (2 * 8 ** 2))    # S
    v += 0.35 * np.exp(-((t_rel - 380) ** 2) / (2 * 45 ** 2))    # T
    v += 0.08 * np.exp(-((t_rel - 500) ** 2) / (2 * 30 ** 2))    # U
    return v

cycle_len = 800
xs = np.linspace(0, total_ms, int(total_ms / 2))
ys = np.array([ecg_cycle(t % cycle_len) for t in xs])
pts = [(ML + x * xscale, ybase - y * mV_scale) for x, y in zip(xs, ys)]
d.line(pts, fill=LINE, width=2)

def tx(ms): return ML + ms * xscale
def ty(mv): return ybase - mv * mV_scale
def point(ms, mv): return (tx(ms), ty(mv))

p_peak = point(90, 0.15)
d.ellipse([p_peak[0]-5, p_peak[1]-5, p_peak[0]+5, p_peak[1]+5], fill=RED)
d.text((p_peak[0]-8, p_peak[1]-32), "P", fill=RED, font=f_lbl)

q = point(208, -0.10)
d.ellipse([q[0]-5, q[1]-5, q[0]+5, q[1]+5], fill=ORANGE)
d.text((q[0]-26, q[1]-6), "Q", fill=ORANGE, font=f_lbl)
r = point(222, 1.20)
d.ellipse([r[0]-5, r[1]-5, r[0]+5, r[1]+5], fill=BLUE)
d.text((r[0]-8, r[1]-32), "R", fill=BLUE, font=f_lbl)
s = point(236, -0.30)
d.ellipse([s[0]-5, s[1]-5, s[0]+5, s[1]+5], fill=PURPLE)
d.text((s[0]+10, s[1]-6), "S", fill=PURPLE, font=f_lbl)
t_pk = point(380, 0.35)
d.ellipse([t_pk[0]-5, t_pk[1]-5, t_pk[0]+5, t_pk[1]+5], fill=GREEN)
d.text((t_pk[0]-8, t_pk[1]-32), "T", fill=GREEN, font=f_lbl)
u_pk = point(500, 0.08)
d.ellipse([u_pk[0]-5, u_pk[1]-5, u_pk[0]+5, u_pk[1]+5], fill=(180,120,60))
d.text((u_pk[0]-8, u_pk[1]+8), "U", fill=(180,120,60), font=f_lbl)

def bracket(x1, x2, y, label, color):
    d.line([(x1, y), (x2, y)], fill=color, width=2)
    d.line([(x1, y-6), (x1, y+6)], fill=color, width=2)
    d.line([(x2, y-6), (x2, y+6)], fill=color, width=2)
    mid = (x1+x2)/2
    d.text((mid-30, y+8), label, fill=color, font=f_small)

bracket(tx(40), tx(205), ty(-0.85), "PR间期 120-200ms", (100,100,110))
bracket(tx(205), tx(245), ty(-0.55), "QRS 60-100ms", (100,100,110))
bracket(tx(205), tx(470), ty(-1.15), "QT间期 (<440男/<460女ms)", (100,100,110))
bracket(tx(245), tx(320), ty(-0.40), "ST段", (100,100,110))

d.text((ML + 6, ybase - 12), "等电位线 (基线)", fill=(120,120,130), font=f_small)
d.text((ML, 22), "标准 ECG 波形：P-QRS-T-U 综合波（3 个心动周期）", fill=LINE, font=f_title)
d.text((W-180, H-30), "横轴：时间(ms)  纵轴：电压(mV)", fill=(120,120,130), font=f_small)

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
img.save(OUTPUT)
print(f"ECG waveform saved -> {OUTPUT}")
