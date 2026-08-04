# -*- coding: utf-8 -*-
"""
绘制标准 ECG 波形图（P-QRS-T-U 全标注 + 间期）—— 优化版
关键改进：
  1. 各分量峰值用数值方法在合成波形上精确求取，标注圆点钉在真实峰值上
  2. 文字标签偏移按分量类型动态计算（P/R/T 朝上、Q/S 朝下、避开邻波）
  3. 标签与圆点用细引导线连接，消除"标签飘在别处"的错位感
依赖：numpy, Pillow
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = os.environ.get("FONT_PATH")
if not FONT_PATH:
    _candidate = os.path.join(os.path.dirname(__file__), "..", "fonts", "wqy-microhei.ttc")
    if os.path.exists(_candidate):
        FONT_PATH = _candidate
if not FONT_PATH:
    raise FileNotFoundError("未找到中文字体。请把 wqy-microhei.ttc 放到 fonts/ 目录，或设置环境变量 FONT_PATH。")

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "images", "ecg_waveform.png")

# ---------- 波形参数 ----------
W, H = 1500, 660
BG = (255, 255, 255)
LINE = (23, 28, 45)
GRID = (230, 235, 245); GRID_MAJOR = (200, 210, 228)
RED = (220, 60, 60); BLUE = (40, 110, 200); GREEN = (40, 150, 90)
ORANGE = (230, 130, 30); PURPLE = (130, 70, 180); BROWN = (160, 100, 50)
GRAY = (110, 115, 125)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
def f(sz): return ImageFont.truetype(FONT_PATH, sz)
f_title = f(26); f_lbl = f(22); f_small = f(17); f_micro = f(15)

ML, MR, MT, MB = 75, 75, 75, 85
PW, PH = W - ML - MR, H - MT - MB

total_ms = 2400
xscale = PW / total_ms
ybase = MT + PH * 0.55            # 等电位线
mV_scale = 115                    # 1mV = 115px

# ---------- 网格（小格40ms / 大格200ms；纵向 0.25mV/0.5mV） ----------
t = 0
while t <= total_ms:
    x = ML + t * xscale
    d.line([(x, MT), (x, MT + PH)], fill=GRID, width=1); t += 40
t = 0
while t <= total_ms:
    x = ML + t * xscale
    d.line([(x, MT), (x, MT + PH)], fill=GRID_MAJOR, width=1); t += 200
v = -2.0
while v <= 2.0:
    y = ybase - v * mV_scale
    d.line([(ML, y), (ML + PW, y)], fill=GRID, width=1); v += 0.25
v = -2.0
while v <= 2.0:
    y = ybase - v * mV_scale
    d.line([(ML, y), (ML + PW, y)], fill=GRID_MAJOR, width=1); v += 0.5

# ---------- 合成 ECG 波形（高密度采样，3 个周期） ----------
def ecg_cycle(t_rel):
    v = 0.0
    v += 0.15 * np.exp(-((t_rel - 90)  ** 2) / (2 * 28 ** 2))   # P
    v += -0.10 * np.exp(-((t_rel - 208) ** 2) / (2 * 6  ** 2))  # Q
    v += 1.20 * np.exp(-((t_rel - 222) ** 2) / (2 * 8  ** 2))   # R
    v += -0.30 * np.exp(-((t_rel - 236) ** 2) / (2 * 8  ** 2))  # S
    v += 0.35 * np.exp(-((t_rel - 380) ** 2) / (2 * 45 ** 2))   # T
    v += 0.08 * np.exp(-((t_rel - 500) ** 2) / (2 * 30 ** 2))   # U
    return v

cycle_len = 800
xs = np.linspace(0, total_ms, 4000)
ys = np.array([ecg_cycle(t % cycle_len) for t in xs])
pts = [(ML + x * xscale, ybase - y * mV_scale) for x, y in zip(xs, ys)]
d.line(pts, fill=LINE, width=2)

# ---------- 坐标换算 ----------
def tx(ms): return ML + ms * xscale
def ty(mv): return ybase - mv * mV_scale

# ---------- 数值求每个分量的真实峰值（在合成波形上） ----------
# 仅在第1个周期内搜索
def find_peak(t_center, window=18, direction="max"):
    """在 [t_center-window, t_center+window] 范围内数值求真实峰"""
    grid = np.linspace(t_center - window, t_center + window, 2001)
    vals = np.array([ecg_cycle(t) for t in grid])
    if direction == "max":
        i = int(np.argmax(vals))
    else:
        i = int(np.argmin(vals))
    return float(grid[i]), float(vals[i])

peaks = {
    "P": (*find_peak(90,  window=25, direction="max"), RED,    "up"),
    "Q": (*find_peak(208, window=14, direction="min"), ORANGE, "down"),
    "R": (*find_peak(222, window=12, direction="max"), BLUE,   "up"),
    "S": (*find_peak(236, window=14, direction="min"), PURPLE, "down"),
    "T": (*find_peak(380, window=40, direction="max"), GREEN,  "up"),
    "U": (*find_peak(500, window=35, direction="max"), BROWN,  "up"),
}

# ---------- 标注点 + 动态标签 ----------
# 标签距峰值像素 + 引导线
LABEL_DX = 14          # 水平偏移
LABEL_DY = 38          # 垂直偏移

def draw_label(name, t_pk, v_pk, color, orient):
    px, py = tx(t_pk), ty(v_pk)
    # 圆点钉在真实峰值
    d.ellipse([px-6, py-6, px+6, py+6], fill=color, outline=(255,255,255), width=2)
    # 标签位置：正向波朝上偏移、负向波朝下偏移
    if orient == "up":
        lx, ly = px + LABEL_DX, py - LABEL_DY
    else:
        lx, ly = px + LABEL_DX, py + LABEL_DY
    # 引导线（圆点边缘 → 标签）
    d.line([(px, py), (lx, ly)], fill=color, width=2)
    # 文字背景小框，避免压在波线上
    d.text((lx, ly - f_lbl.size), name, fill=color, font=f_lbl)

for name, (t_pk, v_pk, color, orient) in peaks.items():
    draw_label(name, t_pk, v_pk, color, orient)

# ---------- 关键文字描述（在标签旁边补中文全称，放图例区） ----------
# 在右上角放图例
legend_x, legend_y = W - 320, MT + 6
d.text((legend_x, legend_y), "波形分量", fill=LINE, font=f_lbl)
legend_items = [
    ("P", "心房去极化",   RED),
    ("QRS","心室去极化",  BLUE),
    ("T", "心室复极化",   GREEN),
    ("U", "复极化延迟",   BROWN),
]
lyy = legend_y + 30
for code, desc, col in legend_items:
    d.ellipse([legend_x-2, lyy-2, legend_x+10, lyy+10], fill=col)
    d.text((legend_x+16, lyy-2), f"{code}  {desc}", fill=LINE, font=f_small)
    lyy += 22

# ---------- 间期标注（括号 + 标签） ----------
def bracket(x1, x2, y, label, color):
    d.line([(x1, y), (x2, y)], fill=color, width=2)
    d.line([(x1, y-6), (x1, y+6)], fill=color, width=2)
    d.line([(x2, y-6), (x2, y+6)], fill=color, width=2)
    mid = (x1+x2)/2
    tw = d.textlength(label, font=f_small)
    d.text((mid - tw/2, y+8), label, fill=color, font=f_small)

# 用真实峰值点定义间期起止
p_t  = peaks["P"][0]
q_t  = peaks["Q"][0]
s_t  = peaks["S"][0]
t_t  = peaks["T"][0]
# PR 间期: P起点(~P-50ms) → QRS起点(Q)
bracket(tx(p_t-50), tx(q_t), ty(-0.85), "PR间期 120-200ms", GRAY)
# QRS 时限: Q → S
bracket(tx(q_t), tx(s_t), ty(-0.55), "QRS 60-100ms", GRAY)
# ST 段: S → T起点(~T-60ms)
bracket(tx(s_t), tx(t_t-60), ty(-0.38), "ST段", GRAY)
# QT 间期: QRS起点(Q) → T终点(~T+80ms)
bracket(tx(q_t), tx(t_t+80), ty(-1.18), "QT间期 (男<440 / 女<460 ms)", GRAY)

# 等电位线
d.text((ML + 6, ybase - 12), "等电位线 (基线)", fill=GRAY, font=f_small)

# 标题与坐标轴
d.text((ML, 24), "标准 ECG 波形：P-QRS-T-U 综合波（3 个心动周期）", fill=LINE, font=f_title)
d.text((W-230, H-28), "横轴：时间(ms)  纵轴：电压(mV)", fill=GRAY, font=f_small)

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
img.save(OUTPUT)
print(f"ECG waveform saved -> {OUTPUT}")

# 打印真实峰值，便于核对
print("标注峰值（数值求取）:")
for name,(t_pk,v_pk,_,_) in peaks.items():
    print(f"  {name}: t={t_pk:.1f}ms  v={v_pk:.3f}mV  px=({tx(t_pk):.0f},{ty(v_pk):.0f})")
