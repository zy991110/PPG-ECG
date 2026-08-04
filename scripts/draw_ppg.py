# -*- coding: utf-8 -*-
"""
绘制 PPG 波形图：AC/DC 分解 + 单周期形态学
依赖：numpy, Pillow
字体：文泉驿微米黑（wqy-microhei.ttc）放置在项目 fonts/ 目录，或通过环境变量 FONT_PATH 指定
输出：images/ppg_acdc.png, images/ppg_morphology.png
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
    raise FileNotFoundError(
        "未找到中文字体。请把 wqy-microhei.ttc 放到 fonts/ 目录，或设置环境变量 FONT_PATH 指向字体文件。"
    )

IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "images")
os.makedirs(IMG_DIR, exist_ok=True)

def f(sz): return ImageFont.truetype(FONT_PATH, sz)
LINE = (23, 28, 45)
GRID = (230, 235, 245)
RED = (220, 60, 60); BLUE = (40, 110, 200); GREEN = (40, 150, 90)
ORANGE = (230, 130, 30); PURPLE = (130, 70, 180); GRAY = (110, 115, 125)

# =====================================================================
# 图1：PPG AC/DC 分解（总信号 = DC基线 + AC脉动）
# =====================================================================
W, H = 1400, 560
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
f_title = f(24); f_small = f(16)
ML, MR, MT, MB = 70, 70, 70, 70
PW, PH = W - ML - MR, H - MT - MB

for gx in range(0, PW+1, 40):
    d.line([(ML+gx, MT), (ML+gx, MT+PH)], fill=GRID, width=1)
for gy in range(0, PH+1, 40):
    d.line([(ML, MT+gy), (ML+PW, MT+gy)], fill=GRID, width=1)

t = np.linspace(0, 3.0, 900)
dc = 0.5 + 0.08*np.sin(2*np.pi*0.3*t)
hr = 1.25

def ppg_pulse(tt):
    ph = (tt*hr) % 1.0
    rise = np.where(ph < 0.12, np.sin(np.pi/2 * ph/0.12), 0)
    decay_env = np.exp(-3.0*(ph-0.12))
    dicrotic = 0.35*np.exp(-((ph-0.32)**2)/(2*0.05**2))
    decay = (decay_env + dicrotic) * (ph >= 0.12)
    return (rise*0.8 + decay*0.6)

ac = ppg_pulse(t)
amp_px = 130
dc_y = MT + PH*0.55
total_y = dc_y - dc*25 - ac*amp_px
dc_curve_y = dc_y - dc*25

dc_pts = [(ML + i/(len(t)-1)*PW, dc_curve_y[i]) for i in range(len(t))]
for i in range(len(dc_pts)-1):
    d.line([dc_pts[i], dc_pts[i+1]], fill=BLUE, width=3)
total_pts = [(ML + i/(len(t)-1)*PW, total_y[i]) for i in range(len(t))]
d.line(total_pts, fill=LINE, width=2)

d.text((ML+30, dc_curve_y[len(t)//2]-30), "DC 分量（直流/非脉动）\n皮肤·脂肪·骨骼·静脉血  ~95-99%", fill=BLUE, font=f_small)
pk_i = int(0.06/3.0*len(t)) + int(0.5/3.0*len(t))
pk_x = ML + pk_i/(len(t)-1)*PW
d.ellipse([pk_x-5, total_y[pk_i]-5, pk_x+5, total_y[pk_i]+5], fill=RED)
d.line([(pk_x, total_y[pk_i]), (pk_x+120, total_y[pk_i]-60)], fill=RED, width=2)
d.text((pk_x+125, total_y[pk_i]-78), "AC 分量（脉动）\n动脉血容积搏动  ~1-5%", fill=RED, font=f_small)
d.line([(pk_x-20, total_y[pk_i]), (pk_x-20, dc_curve_y[pk_i])], fill=(200,80,80), width=2)
d.polygon([(pk_x-25, dc_curve_y[pk_i]+8),(pk_x-15, dc_curve_y[pk_i]+8),(pk_x-20, dc_curve_y[pk_i])], fill=(200,80,80))
d.text((pk_x-90, (total_y[pk_i]+dc_curve_y[pk_i])/2 - 8), "幅度", fill=(200,80,80), font=f_small)

d.text((ML, 22), "PPG 信号组成：总信号 = DC 基线（缓慢漂移） + AC 脉动（与心跳同步）", fill=LINE, font=f_title)
d.text((W-260, H-28), "横轴：时间(s)  纵轴：光强", fill=GRAY, font=f_small)
img.save(os.path.join(IMG_DIR, "ppg_acdc.png"))
print("PPG AC/DC image saved.")

# =====================================================================
# 图2：PPG 单周期形态学
# =====================================================================
W2, H2 = 1400, 620
img2 = Image.new("RGB", (W2, H2), "white")
d2 = ImageDraw.Draw(img2)
f_title2 = f(26); f_lbl2 = f(22); f_small2 = f(17)
ML2, MR2, MT2, MB2 = 80, 80, 70, 90
PW2, PH2 = W2 - ML2 - MR2, H2 - MT2 - MB2

for gx in range(0, PW2+1, 40):
    d2.line([(ML2+gx, MT2), (ML2+gx, MT2+PH2)], fill=GRID, width=1)
for gy in range(0, PH2+1, 40):
    d2.line([(ML2, MT2+gy), (ML2+PW2, MT2+gy)], fill=GRID, width=1)

ph = np.linspace(0, 1.0, 600, endpoint=False)
rise = np.where(ph < 0.12, np.sin(np.pi/2 * ph/0.12), 0.0)
decay_env = np.exp(-3.2*(ph-0.12))
dicrotic = 0.40*np.exp(-((ph-0.34)**2)/(2*0.045**2))
decay = (decay_env + dicrotic) * (ph >= 0.12)
y_norm = rise*0.85 + decay*0.70

xscale = PW2
base_y = MT2 + PH2*0.85
amp_px2 = PH2*0.70
pts = [(ML2 + ph[i]*xscale, base_y - y_norm[i]*amp_px2) for i in range(len(ph))]
d2.line(pts, fill=LINE, width=3)

def X(p): return ML2 + p*xscale
def Y(v): return base_y - v*amp_px2

sp = (X(0.12), Y(0.85))
dn = (X(0.255), Y(0.50))
dp = (X(0.34), Y(0.58))
on = (X(0.0), Y(0.0))

for pt, col, name, dy in [
    (sp, RED, "收缩期峰值\n(Systolic Peak)", -70),
    (dn, ORANGE, "重搏切迹\n(Dicrotic Notch)", 30),
    (dp, GREEN, "舒张期峰值\n(Diastolic Peak)", 30),
    (on, BLUE, "脉搏起始点", 25),
]:
    d2.ellipse([pt[0]-6, pt[1]-6, pt[0]+6, pt[1]+6], fill=col)
    d2.line([(pt[0], pt[1]), (pt[0]+60, pt[1]+dy)], fill=col, width=2)
    d2.text((pt[0]+66, pt[1]+dy-18), name, fill=col, font=f_lbl2)

d2.line([(on[0], base_y+25), (sp[0], base_y+25)], fill=PURPLE, width=2)
d2.line([(on[0], base_y+19), (on[0], base_y+31)], fill=PURPLE, width=2)
d2.line([(sp[0], base_y+19), (sp[0], base_y+31)], fill=PURPLE, width=2)
d2.text(((on[0]+sp[0])/2-60, base_y+36), "收缩上升时间", fill=PURPLE, font=f_small2)

d2.line([(sp[0], base_y-amp_px2-15), (dp[0], base_y-amp_px2-15)], fill=(180,70,70), width=2)
d2.text(((sp[0]+dp[0])/2-90, base_y-amp_px2-40), "Δt → 大动脉僵硬度指数 SI", fill=(180,70,70), font=f_small2)
d2.text((dp[0]+90, dp[1]-10), "AIx = 舒张峰/收缩峰", fill=GRAY, font=f_small2)

d2.line([(X(0.0)-120, Y(0.0)+30), (on[0], on[1])], fill=(60,60,60), width=2)
d2.text((X(0.0)-200, Y(0.0)-10), "ECG R峰", fill=(60,60,60), font=f_lbl2)
pat_y = base_y + 70
d2.line([(X(0.0)-120, pat_y), (sp[0], pat_y)], fill=(60,60,60), width=2)
d2.text(((X(0.0)-120+sp[0])/2-100, pat_y+8), "PAT 脉搏到达时间", fill=(60,60,60), font=f_small2)

d2.text((ML2, 22), "PPG 单周期波形形态学：收缩峰 · 重搏切迹 · 舒张峰", fill=LINE, font=f_title2)
d2.text((W2-240, H2-28), "纵轴：光吸收变化  横轴：时间(一个心动周期)", fill=GRAY, font=f_small2)
img2.save(os.path.join(IMG_DIR, "ppg_morphology.png"))
print("PPG morphology image saved.")
