# -*- coding: utf-8 -*-
"""
绘制 PPG 波形图：AC/DC 分解 + 单周期形态学（v3 优化版）
关键改进（v3）：
  1. 纯Python实现（math替代numpy），无第三方数值库依赖
  2. AC 标注圆点数值求真实峰，钉在波形真实最高点
  3. 形态学各特征点（收缩峰/重搏切迹/舒张峰）数值求真实极值
  4. 标签对称偏移避免重叠（收缩峰朝上、重搏切迹朝下左、舒张峰朝下右）
  5. 间期/参数线段端点 x 严格 = 对应圆点 x，标签居中
依赖：Pillow
字体：文泉驿微米黑（wqy-microhei.ttc）放置在项目 fonts/ 目录，或通过环境变量 FONT_PATH 指定
输出：images/ppg_acdc.png, images/ppg_morphology.png
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
    raise FileNotFoundError(
        "未找到中文字体。请把 wqy-microhei.ttc 放到 fonts/ 目录，或设置环境变量 FONT_PATH 指向字体文件。"
    )

IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "images")
os.makedirs(IMG_DIR, exist_ok=True)

def f(sz): return ImageFont.truetype(FONT_PATH, sz)
LINE = (23, 28, 45)
GRID = (230, 235, 245); GRID_MAJOR = (200, 210, 228)
RED = (220, 60, 60); BLUE = (40, 110, 200); GREEN = (40, 150, 90)
ORANGE = (230, 130, 30); PURPLE = (130, 70, 180); GRAY = (110, 115, 125)
DKRED = (180, 70, 70); DKGRAY = (60, 60, 60)


# =====================================================================
# 图1：PPG AC/DC 分解（总信号 = DC基线 + AC脉动）
# =====================================================================
W, H = 1400, 580
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
f_title = f(24); f_small = f(16); f_lbl = f(19)
ML, MR, MT, MB = 70, 70, 70, 70
PW, PH = W - ML - MR, H - MT - MB

# 网格
for gx in range(0, PW+1, 40):
    d.line([(ML+gx, MT), (ML+gx, MT+PH)], fill=GRID, width=1)
for gy in range(0, PH+1, 40):
    d.line([(ML, MT+gy), (ML+PW, MT+gy)], fill=GRID, width=1)

# 纯Python采样：时间 0..3s，900点
N = 900
t = [i * (3.0 / (N-1)) for i in range(N)]

def ppg_ac_value(tt, hr=1.25):
    """AC脉动分量（纯Python）"""
    ph = (tt*hr) % 1.0
    if ph < 0.12:
        rise = math.sin(math.pi/2 * ph/0.12)
    else:
        rise = 0.0
    decay_env = math.exp(-3.0*(ph-0.12)) if ph >= 0.12 else 0.0
    dicrotic = 0.35*math.exp(-((ph-0.32)**2)/(2*0.05**2)) if ph >= 0.12 else 0.0
    decay = (decay_env + dicrotic)
    return rise*0.8 + decay*0.6

dc = [0.5 + 0.08*math.sin(2*math.pi*0.3*tt) for tt in t]
ac = [ppg_ac_value(tt) for tt in t]

amp_px = 130
dc_y = MT + PH*0.55
total_y = [dc_y - dc[i]*25 - ac[i]*amp_px for i in range(N)]
dc_curve_y = [dc_y - dc[i]*25 for i in range(N)]

# DC 基线
dc_pts = [(ML + i/(N-1)*PW, dc_curve_y[i]) for i in range(N)]
for i in range(N-1):
    d.line([dc_pts[i], dc_pts[i+1]], fill=BLUE, width=3)
# 总信号
total_pts = [(ML + i/(N-1)*PW, total_y[i]) for i in range(N)]
d.line(total_pts, fill=LINE, width=2)

# ---------- 数值求 AC 真实峰（在第2个周期附近找最大值）----------
# 第2个周期约在 t=0.8~1.6s
search_lo = int(0.8/3.0 * N)
search_hi = int(1.6/3.0 * N)
pk_i = search_lo
for i in range(search_lo, search_hi):
    if total_y[i] < total_y[pk_i]:   # 像素 y 越小 = 光强越大（总信号向上凸）
        pk_i = i
pk_x = ML + pk_i/(N-1)*PW
pk_y_total = total_y[pk_i]
pk_y_dc = dc_curve_y[pk_i]

# AC 圆点钉在真实峰
d.ellipse([pk_x-6, pk_y_total-6, pk_x+6, pk_y_total+6], fill=RED, outline=(255,255,255), width=2)
# 标签朝右上（避开右侧波形）
lbl_x = pk_x + 60
lbl_y = pk_y_total - 80
d.line([(pk_x, pk_y_total), (lbl_x, lbl_y+10)], fill=RED, width=2)
d.text((lbl_x, lbl_y), "AC 分量（脉动）", fill=RED, font=f_lbl)
d.text((lbl_x, lbl_y+26), "动脉血容积搏动  ~1-5%", fill=RED, font=f_small)

# 幅度标注：从 AC 峰垂直下到 DC 基线（圆点 x 不变）
amp_x = pk_x - 24
d.line([(amp_x, pk_y_total), (amp_x, pk_y_dc)], fill=DKRED, width=2)
# 箭头
d.polygon([(amp_x-5, pk_y_dc+10),(amp_x+5, pk_y_dc+10),(amp_x, pk_y_dc)], fill=DKRED)
d.line([(amp_x, pk_y_total),(amp_x-4, pk_y_total+8)], fill=DKRED, width=2)
d.line([(amp_x, pk_y_total),(amp_x+4, pk_y_total+8)], fill=DKRED, width=2)
# 幅度文字居中
amp_label = "幅度(AC)"
tw = d.textlength(amp_label, font=f_small)
d.text((amp_x - tw - 6, (pk_y_total+pk_y_dc)/2 - 8), amp_label, fill=DKRED, font=f_small)

# DC 标注（在基线中段）
dc_lbl_i = N // 2
d.text((ML+30, dc_curve_y[dc_lbl_i]-44), "DC 分量（直流/非脉动）", fill=BLUE, font=f_lbl)
d.text((ML+30, dc_curve_y[dc_lbl_i]-18), "皮肤·脂肪·骨骼·静脉血  ~95-99%", fill=BLUE, font=f_small)

d.text((ML, 22), "PPG 信号组成：总信号 = DC 基线（缓慢漂移） + AC 脉动（与心跳同步）", fill=LINE, font=f_title)
d.text((W-260, H-28), "横轴：时间(s)  纵轴：光强", fill=GRAY, font=f_small)
img.save(os.path.join(IMG_DIR, "ppg_acdc.png"))
print("PPG AC/DC image saved.")


# =====================================================================
# 图2：PPG 单周期形态学
# =====================================================================
W2, H2 = 1500, 680
img2 = Image.new("RGB", (W2, H2), "white")
d2 = ImageDraw.Draw(img2)
f_title2 = f(26); f_lbl2 = f(22); f_small2 = f(17)
ML2, MR2, MT2, MB2 = 80, 80, 75, 100
PW2, PH2 = W2 - ML2 - MR2, H2 - MT2 - MB2

for gx in range(0, PW2+1, 40):
    d2.line([(ML2+gx, MT2), (ML2+gx, MT2+PH2)], fill=GRID, width=1)
for gy in range(0, PH2+1, 40):
    d2.line([(ML2, MT2+gy), (ML2+PW2, MT2+gy)], fill=GRID, width=1)

def ppg_morph(ph):
    """单周期PPG波形（光吸收版，向上=吸收增大）"""
    if ph < 0.12:
        rise = math.sin(math.pi/2 * ph/0.12)
    else:
        rise = 0.0
    decay_env = math.exp(-3.2*(ph-0.12)) if ph >= 0.12 else 0.0
    dicrotic = 0.40*math.exp(-((ph-0.34)**2)/(2*0.045**2)) if ph >= 0.12 else 0.0
    decay = decay_env + dicrotic
    return rise*0.85 + decay*0.70

# 高密度采样
N2 = 2000
ph = [i * (1.0 / N2) for i in range(N2)]
y_norm = [ppg_morph(p) for p in ph]

xscale = PW2
base_y = MT2 + PH2*0.85
amp_px2 = PH2*0.70
pts = [(ML2 + ph[i]*xscale, base_y - y_norm[i]*amp_px2) for i in range(N2)]
d2.line(pts, fill=LINE, width=3)

def X(p): return ML2 + p*xscale
def Y(v): return base_y - v*amp_px2

# ---------- 数值求各特征点真实坐标 ----------
def find_extremum(ph_center, window, direction="max"):
    grid = [ph_center - window + i * (2*window/2000) for i in range(2001)]
    grid = [g for g in grid if 0 <= g <= 1.0]
    vals = [ppg_morph(g) for g in grid]
    if direction == "max":
        i = vals.index(max(vals))
    else:
        i = vals.index(min(vals))
    return grid[i], vals[i]

# 收缩峰：全局最大（0~0.2相位段）
sp_ph, sp_v = find_extremum(0.10, 0.08, "max")
# 重搏切迹：收缩峰之后的局部极小（0.18~0.30）
dn_ph, dn_v = find_extremum(0.24, 0.06, "min")
# 舒张峰：重搏切迹之后的局部极大（0.28~0.42）
dp_ph, dp_v = find_extremum(0.34, 0.07, "max")
# 脉搏起始点：相位0
on_ph, on_v = 0.0, 0.0

peaks = {
    "sp": (sp_ph, sp_v, RED,    "up",   "right"),  # 收缩峰朝上右
    "dn": (dn_ph, dn_v, ORANGE, "down", "left"),   # 重搏切迹朝下左
    "dp": (dp_ph, dp_v, GREEN,  "down", "right"),  # 舒张峰朝下右
    "on": (on_ph, on_v, BLUE,   "up",   "left"),   # 起始点朝上左
}

peak_px = {}
DX, DY = 18, 44
def draw_label(name, t_pk, v_pk, color, orient, hside):
    px, py = X(t_pk), Y(v_pk)
    d2.ellipse([px-6, py-6, px+6, py+6], fill=color, outline=(255,255,255), width=2)
    if orient == "up":
        ly = py - DY
    else:
        ly = py + DY
    if hside == "left":
        lx = px - DX
        first_line = name.split("\n")[0]
        tw = d2.textlength(first_line, font=f_lbl2)
        lx_text = lx - tw
    else:
        lx = px + DX
        lx_text = lx
    d2.line([(px, py), (lx, ly)], fill=color, width=2)
    # 多行文字
    lines = name.split("\n")
    for li, line in enumerate(lines):
        d2.text((lx_text, ly - f_lbl2.size + li*(f_lbl2.size+2)), line, fill=color, font=f_lbl2)
    return px

for name, (t_pk, v_pk, color, orient, hside) in peaks.items():
    peak_px[name] = draw_label(
        {"sp":"收缩期峰值\n(Systolic Peak)","dn":"重搏切迹\n(Dicrotic Notch)",
         "dp":"舒张期峰值\n(Diastolic Peak)","on":"脉搏\n起始点"}[name],
        t_pk, v_pk, color, orient, hside)

# ---------- 参数线段（端点 x 严格 = 圆点 x） ----------
def bracket(x1, x2, y, label, color, font=None):
    if x1 > x2: x1, x2 = x2, x1
    d2.line([(x1, y), (x2, y)], fill=color, width=2)
    d2.line([(x1, y-7), (x1, y+7)], fill=color, width=2)
    d2.line([(x2, y-7), (x2, y+7)], fill=color, width=2)
    ff = font or f_small2
    tw = d2.textlength(label, font=ff)
    d2.text(((x1+x2)/2 - tw/2, y + 9), label, fill=color, font=ff)

sp_x = peak_px["sp"]; dn_x = peak_px["dn"]; dp_x = peak_px["dp"]; on_x = peak_px["on"]

# 收缩上升时间：on -> sp
bracket(on_x, sp_x, base_y + 30, "收缩上升时间", PURPLE)
# Δt：sp -> dp（用于 SI）
bracket(sp_x, dp_x, base_y - amp_px2 - 15, "Δt → 大动脉僵硬度指数 SI", DKRED)
# PAT：ECG R峰(在on左侧120px) -> sp
pat_x1 = X(0.0) - 120
bracket(pat_x1, sp_x, base_y + 75, "PAT 脉搏到达时间", DKGRAY)
# ECG R峰 标注
d2.line([(pat_x1, Y(0.0)+30), (on_x, Y(0.0))], fill=DKGRAY, width=2)
d2.text((pat_x1 - 90, Y(0.0)-12), "ECG R峰", fill=DKGRAY, font=f_lbl2)

# AIx 标注（在舒张峰旁）
d2.text((dp_x + 60, peak_px_y := Y(dp_v) - 8), "AIx = 舒张峰/收缩峰", fill=GRAY, font=f_small2)

d2.text((ML2, 24), "PPG 单周期波形形态学：收缩峰 · 重搏切迹 · 舒张峰", fill=LINE, font=f_title2)
d2.text((W2-240, H2-28), "纵轴：光吸收变化  横轴：时间(一个心动周期)", fill=GRAY, font=f_small2)
img2.save(os.path.join(IMG_DIR, "ppg_morphology.png"))
print("PPG morphology image saved.")

# 打印真实峰值便于核对
print(f"  收缩峰: ph={sp_ph:.3f} v={sp_v:.3f} px_x={sp_x:.0f}")
print(f"  重搏切迹: ph={dn_ph:.3f} v={dn_v:.3f} px_x={dn_x:.0f}")
print(f"  舒张峰: ph={dp_ph:.3f} v={dp_v:.3f} px_x={dp_x:.0f}")
print(f"  起始点: px_x={on_x:.0f}")
