# -*- coding: utf-8 -*-
"""
绘制标准 ECG 波形图（P-QRS-T-U 全标注 + 间期）—— v3
关键改进（v3）：
  1. Q/S 标签对称放置：Q 朝左下、S 朝右下，避免在 R 两侧重叠
  2. 间期括号端点 x 严格 = 标注圆点 x（对齐），括号分层排列在等电位线下方
  3. 间期标签文字居中对齐括号中点
依赖：Pillow
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = os.environ.get("FONT_PATH")
if not FONT_PATH:
    _candidate = os.path.join(os.path.dirname(__file__), "..", "fonts", "wqy-microhei.ttc")
    if os.path.exists(_candidate):
        FONT_PATH = _candidate
if not FONT_PATH:
    raise FileNotFoundError("未找到中文字体。请把 wqy-microhei.ttc 放到 fonts/ 目录，或设置环境变量 FONT_PATH。")

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "images", "ecg_waveform.png")

W, H = 1500, 700
BG = (255, 255, 255)
LINE = (23, 28, 45)
GRID = (230, 235, 245); GRID_MAJOR = (200, 210, 228)
RED = (220, 60, 60); BLUE = (40, 110, 200); GREEN = (40, 150, 90)
ORANGE = (230, 130, 30); PURPLE = (130, 70, 180); BROWN = (160, 100, 50)
GRAY = (110, 115, 125)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
def f(sz): return ImageFont.truetype(FONT_PATH, sz)
f_title = f(26); f_lbl = f(22); f_small = f(17)

ML, MR, MT, MB = 75, 75, 75, 95
PW, PH = W - ML - MR, H - MT - MB

total_ms = 2400
xscale = PW / total_ms
ybase = MT + PH * 0.50          # 等电位线居中，给上下都留空间
mV_scale = 120

# 网格
t = 0
while t <= total_ms:
    x = ML + t * xscale; d.line([(x, MT), (x, MT + PH)], fill=GRID, width=1); t += 40
t = 0
while t <= total_ms:
    x = ML + t * xscale; d.line([(x, MT), (x, MT + PH)], fill=GRID_MAJOR, width=1); t += 200
v = -2.0
while v <= 2.0:
    y = ybase - v * mV_scale; d.line([(ML, y), (ML + PW, y)], fill=GRID, width=1); v += 0.25
v = -2.0
while v <= 2.0:
    y = ybase - v * mV_scale; d.line([(ML, y), (ML + PW, y)], fill=GRID_MAJOR, width=1); v += 0.5

def ecg_cycle(t_rel):
    """纯Python实现的高斯分量叠加ECG波形（替代numpy）"""
    def gauss(t, mu, sigma, amp):
        return amp * math.exp(-((t - mu) ** 2) / (2 * sigma ** 2))
    v = 0.0
    v += gauss(t_rel, 90,  28, 0.15)    # P
    v += gauss(t_rel, 208, 6,  -0.10)   # Q
    v += gauss(t_rel, 222, 8,  1.20)     # R
    v += gauss(t_rel, 236, 8,  -0.30)   # S
    v += gauss(t_rel, 380, 45, 0.35)    # T
    v += gauss(t_rel, 500, 30, 0.08)    # U
    return v

cycle_len = 800
# 纯Python生成采样点
xs = [i * (total_ms / 3999) for i in range(4000)]
ys = [ecg_cycle(t % cycle_len) for t in xs]
pts = [(ML + x * xscale, ybase - y * mV_scale) for x, y in zip(xs, ys)]
d.line(pts, fill=LINE, width=2)

def tx(ms): return ML + ms * xscale
def ty(mv): return ybase - mv * mV_scale

def find_peak(t_center, window=18, direction="max"):
    """纯Python数值求峰：在窗口内扫描最大/最小值"""
    grid = [t_center - window + i * (2 * window / 2000) for i in range(2001)]
    vals = [ecg_cycle(t) for t in grid]
    if direction == "max":
        i = vals.index(max(vals))
    else:
        i = vals.index(min(vals))
    return grid[i], vals[i]

peaks = {
    "P": (*find_peak(90,  window=25, direction="max"), RED,    "up",    "right"),
    "Q": (*find_peak(208, window=14, direction="min"), ORANGE, "down",  "left"),   # Q朝左下
    "R": (*find_peak(222, window=12, direction="max"), BLUE,   "up",    "right"),
    "S": (*find_peak(236, window=14, direction="min"), PURPLE, "down",  "right"),  # S朝右下
    "T": (*find_peak(380, window=40, direction="max"), GREEN,  "up",    "right"),
    "U": (*find_peak(500, window=35, direction="max"), BROWN,  "up",    "right"),
}

# ---------- 标注圆点 + 动态标签 ----------
DX = 16; DY = 40
def draw_label(name, t_pk, v_pk, color, orient, hside):
    px, py = tx(t_pk), ty(v_pk)
    d.ellipse([px-6, py-6, px+6, py+6], fill=color, outline=(255,255,255), width=2)
    if orient == "up":
        ly = py - DY
    else:
        ly = py + DY
    if hside == "left":
        lx = px - DX
        # 标签锚在圆点左侧，文字右对齐到引导线起点
        tw = d.textlength(name, font=f_lbl)
        lx_text = lx - tw
    else:
        lx = px + DX
        lx_text = lx
    d.line([(px, py), (lx, ly)], fill=color, width=2)
    d.text((lx_text, ly - f_lbl.size), name, fill=color, font=f_lbl)
    return px  # 返回圆点x，供间期对齐用

peak_px = {}
for name, (t_pk, v_pk, color, orient, hside) in peaks.items():
    peak_px[name] = draw_label(name, t_pk, v_pk, color, orient, hside)

# ---------- 图例 ----------
legend_x, legend_y = W - 320, MT + 6
d.text((legend_x, legend_y), "波形分量", fill=LINE, font=f_lbl)
legend_items = [("P","心房去极化",RED),("QRS","心室去极化",BLUE),("T","心室复极化",GREEN),("U","复极化延迟",BROWN)]
lyy = legend_y + 30
for code, desc, col in legend_items:
    d.ellipse([legend_x-2, lyy-2, legend_x+10, lyy+10], fill=col)
    d.text((legend_x+16, lyy-2), f"{code}  {desc}", fill=LINE, font=f_small)
    lyy += 22

# ---------- 间期括号（端点严格对齐圆点 x） ----------
# 分层 y，避免重叠；标签居中
def bracket(x1, x2, y, label, color):
    # 保证 x1 < x2
    if x1 > x2: x1, x2 = x2, x1
    d.line([(x1, y), (x2, y)], fill=color, width=2)
    d.line([(x1, y-7), (x1, y+7)], fill=color, width=2)
    d.line([(x2, y-7), (x2, y+7)], fill=color, width=2)
    tw = d.textlength(label, font=f_small)
    d.text(((x1+x2)/2 - tw/2, y + 9), label, fill=color, font=f_small)

# 间期端点 x 严格 = 对应圆点 x
p_x = peak_px["P"]; q_x = peak_px["Q"]; s_x = peak_px["S"]; t_x = peak_px["T"]
# PR间期: P起点(取P峰左侧50ms) → Q峰
pr_x1 = tx(peaks["P"][0] - 50)
pr_x2 = q_x
# QRS时限: Q峰 → S峰
qrs_x1 = q_x; qrs_x2 = s_x
# ST段: S峰 → T峰左侧60ms
st_x1 = s_x; st_x2 = tx(peaks["T"][0] - 60)
# QT间期: Q峰 → T峰右侧80ms
qt_x1 = q_x; qt_x2 = tx(peaks["T"][0] + 80)

# 分层 y（从浅到深，避开波形下方）：ST 最浅，QRS 中，PR/QT 最深
y_st  = ybase + 70
y_qrs = ybase + 110
y_pr  = ybase + 150
y_qt  = ybase + 190

bracket(pr_x1,  pr_x2,  y_pr,  "PR间期 120-200ms", GRAY)
bracket(qrs_x1, qrs_x2, y_qrs, "QRS 60-100ms",      GRAY)
bracket(st_x1,  st_x2,  y_st,  "ST段",              GRAY)
bracket(qt_x1,  qt_x2,  y_qt,  "QT间期 (男<440 / 女<460 ms)", GRAY)

# 等电位线标注
d.text((ML + 6, ybase - 22), "等电位线 (基线)", fill=GRAY, font=f_small)

# 标题与坐标轴
d.text((ML, 24), "标准 ECG 波形：P-QRS-T-U 综合波（3 个心动周期）", fill=LINE, font=f_title)
d.text((W-230, H-28), "横轴：时间(ms)  纵轴：电压(mV)", fill=GRAY, font=f_small)

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
img.save(OUTPUT)
print(f"ECG waveform saved -> {OUTPUT}")

print("标注峰值与圆点x坐标:")
for name,(t_pk,v_pk,_,_,_) in peaks.items():
    print(f"  {name}: t={t_pk:.1f}ms v={v_pk:.3f}mV px_x={peak_px[name]:.0f}")
print("间期端点:")
print(f"  PR : {pr_x1:.0f} -> {pr_x2:.0f}  (P-50ms -> Q峰)")
print(f"  QRS: {qrs_x1:.0f} -> {qrs_x2:.0f}  (Q峰 -> S峰)")
print(f"  ST : {st_x1:.0f} -> {st_x2:.0f}  (S峰 -> T-60ms)")
print(f"  QT : {qt_x1:.0f} -> {qt_x2:.0f}  (Q峰 -> T+80ms)")
