# PPG 与 ECG 技术原理可视化

本项目用 Python（numpy + Pillow）从零绘制 PPG / ECG 波形图，并配套技术原理文档。所有波形图为矢量级清晰标注，可用于教学、产品文档、技术汇报。

## 项目结构

```
PPG-ECG/
├── README.md                       本说明
├── scripts/
│   ├── draw_ecg.py                 绘制标准 ECG 波形（P-QRS-T-U + 间期标注）
│   └── draw_ppg.py                 绘制 PPG 波形（AC/DC 分解 + 单周期形态学）
├── images/                         生成的波形图（PNG）
│   ├── ecg_waveform.png
│   ├── ppg_acdc.png
│   └── ppg_morphology.png
└── fonts/
    └── wqy-microhei.ttc            中文字体（文泉驿微米黑，开源）
```

## 环境依赖

```bash
pip install numpy pillow
```

> 不依赖 matplotlib —— 纯 numpy + Pillow 绘制，规避了无图形界面环境的依赖问题。

## 快速开始

```bash
cd scripts
python3 draw_ecg.py      # 生成 images/ecg_waveform.png
python3 draw_ppg.py      # 生成 images/ppg_acdc.png + images/ppg_morphology.png
```

字体默认从 `fonts/wqy-microhei.ttc` 加载；也可用环境变量指定：

```bash
FONT_PATH=/path/to/your/font.ttf python3 draw_ecg.py
```

## 波形图说明

### 1. ECG 波形（ecg_waveform.png）

3 个心动周期的 P-QRS-T-U 综合波，关键标注：

| 波形 | 含义 | 临床意义 |
|------|------|----------|
| **P** | 心房去极化 | P 增宽→左房肥大；P 高尖→右房肥大；P 消失→房颤 |
| **QRS** | 心室去极化 | 时限 60-100ms；>120ms 为束支阻滞/室性起源 |
| **T** | 心室快速复极化 | 高尖→高钾血症；低平/倒置→心肌缺血 |
| **U** | 复极化延迟 | 明显 U 波→低钾血症 |

间期标注：PR 间期（120-200ms）、QRS 时限（60-100ms）、QT 间期（男<440ms/女<460ms，Bazett 校正）、ST 段（等电位线，抬高/压低有临床意义）。

### 2. PPG AC/DC 分解（ppg_acdc.png）

展示 PPG 信号的本质组成：

- **DC 分量（~95-99%）**：缓慢漂移，反映皮肤/脂肪/骨骼/静脉血的恒定光吸收，受呼吸调制
- **AC 分量（~1-5%）**：与心跳同步的脉动，反映动脉血容积的搏动性变化

基于 Beer-Lambert 定律：`I = I₀ · e^(-ε(λ)·C·L)`

### 3. PPG 单周期形态学（ppg_morphology.png）

标注 PPG 脉冲波形的关键特征点与衍生参数：

- **收缩期峰值**：心脏射血后动脉压力最大点
- **重搏切迹**：主动脉瓣关闭引起的反射波
- **舒张期峰值**：反射波产生的二次小峰
- **收缩上升时间**：反映动脉僵硬度
- **Δt → SI**：大动脉僵硬度指数 = 身高 / Δt
- **AIx**：增强指数 = 舒张峰/收缩峰，血管年龄生物标志
- **PAT**：脉搏到达时间（ECG R 峰 → PPG 收缩峰起点），无袖带血压估算核心参数

## 技术原理文档

完整的 PPG 与 ECG 技术原理（含业务落地全景、LaTeX 公式、产品化映射）已发布为飞书云文档：

<a href="https://anker-in.feishu.cn/docx/EIKYdcfwNoIXsDxwhRaczydSnDg" target="_blank">PPG与ECG技术原理与业务落地全景（飞书文档）</a>

## 字体版权

`wqy-microhei.ttc` 来自 [文泉驿微米黑](http://wenq.org/)，GPL 许可，可自由使用与分发。

## 许可

MIT
