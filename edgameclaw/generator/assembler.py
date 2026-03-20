# =============================================================================
# EdGameClaw — AI Game-Based Learning Studio
# Created by Yuqi Hang (github.com/yh2072)
# https://github.com/yh2072/edgameclaw
# =============================================================================
"""Assembles generated content with static engine templates into a single HTML file."""

import json
import sys
from pathlib import Path

import jinja2

# ---------------------------------------------------------------------------
# Theme Registry — each theme defines CSS colors + pixel art palette + mood
# ---------------------------------------------------------------------------

THEMES: dict[str, dict] = {
    "pink-cute": {
        "label": "粉色可爱",
        "mood": "温馨可爱、少女心、软萌",
        "css": {
            "bg": "#1a0818",
            "containerBg": "#10060e",
            "accent": "#ff6a9a",
            "highlight": "#ffc0d0",
            "success": "#90e0a0",
            "successBg": "rgba(80,200,120,0.12)",
            "errorBg": "rgba(255,80,80,0.12)",
            "text": "#f0e0f0",
            "muted": "#c080a0",
            "buttonBg": "#5a2848",
            "buttonHover": "#7a3a60",
            "border": "#5a3050",
            "inputBorder": "#8a4a70",
            "dialogBg": "rgba(40,15,35,0.93)",
            "dialogBorder": "#e090b0",
            "glow": "rgba(255,120,180,0.15)",
            "glowSoft": "rgba(255,180,210,0.6)",
            "glowAccent": "rgba(255,106,154,0.4)",
            "dotBg": "#2a1028",
            "placeholder": "#8a5070",
            "dimText": "#b07090",
            "slotBorder": "#8a5070",
            "cardBg": "#2a1028",
            "cardHover": "#3a1838",
            "cardText": "#e0c0d0",
        },
        "pixel_palette": ["#ff6a9a", "#ffc0d0", "#e090b0", "#90e0a0", "#80b0e0", "#f0e0f0"],
    },
    "ocean-dream": {
        "label": "海洋梦境",
        "mood": "宁静深邃、海底探险、蓝色梦幻",
        "css": {
            "bg": "#0a1628",
            "containerBg": "#06101e",
            "accent": "#4ac0ff",
            "highlight": "#a0e0ff",
            "success": "#60e0a0",
            "successBg": "rgba(80,200,140,0.12)",
            "errorBg": "rgba(255,80,80,0.12)",
            "text": "#e0f0ff",
            "muted": "#6090b0",
            "buttonBg": "#1a3a5a",
            "buttonHover": "#2a5070",
            "border": "#1a3050",
            "inputBorder": "#3a6080",
            "dialogBg": "rgba(10,20,40,0.93)",
            "dialogBorder": "#4090c0",
            "glow": "rgba(74,192,255,0.15)",
            "glowSoft": "rgba(100,180,240,0.6)",
            "glowAccent": "rgba(74,192,255,0.4)",
            "dotBg": "#0e1a30",
            "placeholder": "#4070a0",
            "dimText": "#5880a8",
            "slotBorder": "#4070a0",
            "cardBg": "#0e1a30",
            "cardHover": "#162840",
            "cardText": "#b0d0e0",
        },
        "pixel_palette": ["#4ac0ff", "#a0e0ff", "#2080c0", "#60e0a0", "#ffb060", "#e0f0ff"],
    },
    "forest-sage": {
        "label": "森林智者",
        "mood": "自然清新、森林探索、绿色宁静",
        "css": {
            "bg": "#0a1810",
            "containerBg": "#06120a",
            "accent": "#50c878",
            "highlight": "#a0e8b0",
            "success": "#80e090",
            "successBg": "rgba(80,200,100,0.14)",
            "errorBg": "rgba(255,80,80,0.12)",
            "text": "#e0f8e8",
            "muted": "#708870",
            "buttonBg": "#1a3828",
            "buttonHover": "#2a5038",
            "border": "#1a3020",
            "inputBorder": "#3a6048",
            "dialogBg": "rgba(10,24,16,0.93)",
            "dialogBorder": "#50a068",
            "glow": "rgba(80,200,120,0.15)",
            "glowSoft": "rgba(120,220,150,0.6)",
            "glowAccent": "rgba(80,200,120,0.4)",
            "dotBg": "#0e2018",
            "placeholder": "#508060",
            "dimText": "#608870",
            "slotBorder": "#508060",
            "cardBg": "#0e2018",
            "cardHover": "#163028",
            "cardText": "#b0d8c0",
        },
        "pixel_palette": ["#50c878", "#a0e8b0", "#2a8048", "#e0c060", "#c08060", "#e0f8e8"],
    },
    "sunset-warm": {
        "label": "日落暖橘",
        "mood": "温暖活力、黄昏浪漫、橙金色调",
        "css": {
            "bg": "#1a1008",
            "containerBg": "#120c06",
            "accent": "#ff8c42",
            "highlight": "#ffc080",
            "success": "#a0e060",
            "successBg": "rgba(140,210,60,0.12)",
            "errorBg": "rgba(255,80,80,0.12)",
            "text": "#fff0e0",
            "muted": "#b08060",
            "buttonBg": "#5a3018",
            "buttonHover": "#7a4828",
            "border": "#5a3820",
            "inputBorder": "#8a5830",
            "dialogBg": "rgba(30,18,8,0.93)",
            "dialogBorder": "#e09050",
            "glow": "rgba(255,140,66,0.15)",
            "glowSoft": "rgba(255,180,120,0.6)",
            "glowAccent": "rgba(255,140,66,0.4)",
            "dotBg": "#201810",
            "placeholder": "#906040",
            "dimText": "#a07848",
            "slotBorder": "#906040",
            "cardBg": "#201810",
            "cardHover": "#302018",
            "cardText": "#e0c8b0",
        },
        "pixel_palette": ["#ff8c42", "#ffc080", "#e06020", "#a0e060", "#ff6080", "#fff0e0"],
    },
    "galaxy-purple": {
        "label": "银河紫",
        "mood": "神秘科幻、太空探索、紫色星辰",
        "css": {
            "bg": "#10081a",
            "containerBg": "#0a0612",
            "accent": "#a06aff",
            "highlight": "#d0a0ff",
            "success": "#80e0a0",
            "successBg": "rgba(80,200,140,0.12)",
            "errorBg": "rgba(255,80,80,0.12)",
            "text": "#f0e0ff",
            "muted": "#9070b8",
            "buttonBg": "#30185a",
            "buttonHover": "#48287a",
            "border": "#30205a",
            "inputBorder": "#60408a",
            "dialogBg": "rgba(16,8,26,0.93)",
            "dialogBorder": "#9060d0",
            "glow": "rgba(160,106,255,0.15)",
            "glowSoft": "rgba(180,140,255,0.6)",
            "glowAccent": "rgba(160,106,255,0.4)",
            "dotBg": "#18102a",
            "placeholder": "#7050a8",
            "dimText": "#7a58a0",
            "slotBorder": "#7050a8",
            "cardBg": "#18102a",
            "cardHover": "#20183a",
            "cardText": "#c8b0e0",
        },
        "pixel_palette": ["#a06aff", "#d0a0ff", "#7040c0", "#80e0a0", "#ff80a0", "#f0e0ff"],
    },
    "candy-pop": {
        "label": "糖果波普",
        "mood": "缤纷多彩、趣味童真、马卡龙色",
        "css": {
            "bg": "#180818",
            "containerBg": "#100610",
            "accent": "#ff60a0",
            "highlight": "#ffb0d0",
            "success": "#80e0c0",
            "successBg": "rgba(80,200,180,0.12)",
            "errorBg": "rgba(255,80,80,0.12)",
            "text": "#fff0f8",
            "muted": "#b880a8",
            "buttonBg": "#4a1848",
            "buttonHover": "#6a2860",
            "border": "#4a2048",
            "inputBorder": "#7a4870",
            "dialogBg": "rgba(24,8,24,0.93)",
            "dialogBorder": "#e080c0",
            "glow": "rgba(255,96,160,0.15)",
            "glowSoft": "rgba(255,160,200,0.6)",
            "glowAccent": "rgba(255,96,160,0.4)",
            "dotBg": "#200e20",
            "placeholder": "#8a5080",
            "dimText": "#a06898",
            "slotBorder": "#8a5080",
            "cardBg": "#200e20",
            "cardHover": "#2a1830",
            "cardText": "#e0c0d8",
        },
        "pixel_palette": ["#ff60a0", "#80e0c0", "#ffd060", "#a080ff", "#60c0ff", "#fff0f8"],
    },
    "retro-amber": {
        "label": "复古琥珀",
        "mood": "怀旧暖色、复古终端、琥珀绿光",
        "css": {
            "bg": "#0a0a00",
            "containerBg": "#080800",
            "accent": "#ffb000",
            "highlight": "#ffd860",
            "success": "#60e060",
            "successBg": "rgba(80,200,80,0.12)",
            "errorBg": "rgba(255,80,80,0.12)",
            "text": "#f0e8c0",
            "muted": "#a09048",
            "buttonBg": "#3a2800",
            "buttonHover": "#504000",
            "border": "#3a3000",
            "inputBorder": "#605000",
            "dialogBg": "rgba(10,10,0,0.93)",
            "dialogBorder": "#c09020",
            "glow": "rgba(255,176,0,0.15)",
            "glowSoft": "rgba(255,200,80,0.6)",
            "glowAccent": "rgba(255,176,0,0.4)",
            "dotBg": "#141000",
            "placeholder": "#807028",
            "dimText": "#887830",
            "slotBorder": "#807028",
            "cardBg": "#141000",
            "cardHover": "#1c1800",
            "cardText": "#d0c8a0",
        },
        "pixel_palette": ["#ffb000", "#ffd860", "#c08000", "#60e060", "#ff6040", "#f0e8c0"],
    },
    # ── 中国古典色 / Chinese classical ──
    "china-porcelain": {
        "label": "青花",
        "mood": "青花瓷、素雅、白底青花、东方雅韵",
        "css": {
            "bg": "#0c1620",
            "containerBg": "#081018",
            "accent": "#2e7d9a",
            "highlight": "#6eb5c8",
            "success": "#50a080",
            "successBg": "rgba(60,160,120,0.12)",
            "errorBg": "rgba(200,80,80,0.12)",
            "text": "#e8f0f4",
            "muted": "#608898",
            "buttonBg": "#1a3a48",
            "buttonHover": "#285060",
            "border": "#1a3040",
            "inputBorder": "#3a6070",
            "dialogBg": "rgba(12,22,32,0.93)",
            "dialogBorder": "#3a8098",
            "glow": "rgba(46,125,154,0.15)",
            "glowSoft": "rgba(100,180,200,0.5)",
            "glowAccent": "rgba(46,125,154,0.4)",
            "dotBg": "#101c28",
            "placeholder": "#507080",
            "dimText": "#587088",
            "slotBorder": "#407088",
            "cardBg": "#101c28",
            "cardHover": "#182838",
            "cardText": "#b8d0dc",
        },
        "pixel_palette": ["#2e7d9a", "#6eb5c8", "#1a5068", "#80c0a0", "#e0c070", "#e8f0f4"],
    },
    "china-cinnabar": {
        "label": "朱砂",
        "mood": "朱砂红、印章、喜庆、传统中国红",
        "css": {
            "bg": "#1a0808",
            "containerBg": "#120606",
            "accent": "#c43838",
            "highlight": "#e87878",
            "success": "#60a060",
            "successBg": "rgba(80,160,80,0.12)",
            "errorBg": "rgba(200,60,60,0.14)",
            "text": "#f8e8e8",
            "muted": "#a06868",
            "buttonBg": "#501818",
            "buttonHover": "#702828",
            "border": "#502020",
            "inputBorder": "#804040",
            "dialogBg": "rgba(26,8,8,0.93)",
            "dialogBorder": "#c05050",
            "glow": "rgba(196,56,56,0.15)",
            "glowSoft": "rgba(220,100,100,0.5)",
            "glowAccent": "rgba(196,56,56,0.4)",
            "dotBg": "#200c0c",
            "placeholder": "#885050",
            "dimText": "#906060",
            "slotBorder": "#885050",
            "cardBg": "#200c0c",
            "cardHover": "#301414",
            "cardText": "#d8c0c0",
        },
        "pixel_palette": ["#c43838", "#e87878", "#882020", "#d0a050", "#408040", "#f8e8e8"],
    },
    "china-ink": {
        "label": "墨色",
        "mood": "水墨、留白、文人画、墨分五色",
        "css": {
            "bg": "#0e0e0e",
            "containerBg": "#0a0a0a",
            "accent": "#404040",
            "highlight": "#787878",
            "success": "#508050",
            "successBg": "rgba(60,120,60,0.12)",
            "errorBg": "rgba(160,60,60,0.12)",
            "text": "#e0e0dc",
            "muted": "#808078",
            "buttonBg": "#282828",
            "buttonHover": "#383838",
            "border": "#282828",
            "inputBorder": "#484840",
            "dialogBg": "rgba(18,18,18,0.95)",
            "dialogBorder": "#505048",
            "glow": "rgba(80,80,80,0.2)",
            "glowSoft": "rgba(120,120,120,0.4)",
            "glowAccent": "rgba(100,100,100,0.35)",
            "dotBg": "#141414",
            "placeholder": "#606058",
            "dimText": "#686860",
            "slotBorder": "#505048",
            "cardBg": "#141414",
            "cardHover": "#1c1c1c",
            "cardText": "#b8b8b0",
        },
        "pixel_palette": ["#404040", "#787878", "#202020", "#508050", "#a08050", "#e0e0dc"],
    },
    "dunhuang": {
        "label": "敦煌",
        "mood": "敦煌壁画、土黄、赭石、飞天",
        "css": {
            "bg": "#1c1410",
            "containerBg": "#14100c",
            "accent": "#c07838",
            "highlight": "#e0a868",
            "success": "#70a050",
            "successBg": "rgba(80,140,60,0.12)",
            "errorBg": "rgba(180,70,50,0.12)",
            "text": "#f0e8e0",
            "muted": "#a08870",
            "buttonBg": "#503820",
            "buttonHover": "#704828",
            "border": "#403020",
            "inputBorder": "#705840",
            "dialogBg": "rgba(28,20,16,0.93)",
            "dialogBorder": "#b08048",
            "glow": "rgba(192,120,56,0.15)",
            "glowSoft": "rgba(220,160,100,0.5)",
            "glowAccent": "rgba(192,120,56,0.4)",
            "dotBg": "#201810",
            "placeholder": "#806850",
            "dimText": "#887860",
            "slotBorder": "#806850",
            "cardBg": "#201810",
            "cardHover": "#282018",
            "cardText": "#d8c8b8",
        },
        "pixel_palette": ["#c07838", "#e0a868", "#905828", "#708848", "#b06050", "#f0e8e0"],
    },
    "forbidden-red": {
        "label": "故宫红",
        "mood": "故宫红墙、帝王、庄重、中国红",
        "css": {
            "bg": "#180808",
            "containerBg": "#100606",
            "accent": "#b83030",
            "highlight": "#e06868",
            "success": "#508850",
            "successBg": "rgba(60,120,60,0.12)",
            "errorBg": "rgba(180,50,50,0.14)",
            "text": "#f5e6e6",
            "muted": "#986060",
            "buttonBg": "#581818",
            "buttonHover": "#782828",
            "border": "#481818",
            "inputBorder": "#784040",
            "dialogBg": "rgba(24,8,8,0.93)",
            "dialogBorder": "#a83838",
            "glow": "rgba(184,48,48,0.15)",
            "glowSoft": "rgba(220,90,90,0.5)",
            "glowAccent": "rgba(184,48,48,0.4)",
            "dotBg": "#200c0c",
            "placeholder": "#805050",
            "dimText": "#886868",
            "slotBorder": "#805050",
            "cardBg": "#200c0c",
            "cardHover": "#301010",
            "cardText": "#d0b8b8",
        },
        "pixel_palette": ["#b83030", "#e06868", "#802020", "#c8a040", "#408050", "#f5e6e6"],
    },
    "china-landscape": {
        "label": "青绿",
        "mood": "青绿山水、千里江山、国画山水",
        "css": {
            "bg": "#0a1418",
            "containerBg": "#060e12",
            "accent": "#308868",
            "highlight": "#70b898",
            "success": "#60a878",
            "successBg": "rgba(60,140,90,0.12)",
            "errorBg": "rgba(180,70,70,0.12)",
            "text": "#e0f0e8",
            "muted": "#608878",
            "buttonBg": "#183830",
            "buttonHover": "#285048",
            "border": "#183028",
            "inputBorder": "#386858",
            "dialogBg": "rgba(10,20,24,0.93)",
            "dialogBorder": "#408870",
            "glow": "rgba(48,136,104,0.15)",
            "glowSoft": "rgba(100,180,140,0.5)",
            "glowAccent": "rgba(48,136,104,0.4)",
            "dotBg": "#0c1814",
            "placeholder": "#507868",
            "dimText": "#587870",
            "slotBorder": "#507868",
            "cardBg": "#0c1814",
            "cardHover": "#122420",
            "cardText": "#b0d0c0",
        },
        "pixel_palette": ["#308868", "#70b898", "#206050", "#c0b060", "#6088a0", "#e0f0e8"],
    },
    "china-rouge": {
        "label": "胭脂",
        "mood": "胭脂、古典妆、柔粉、含蓄",
        "css": {
            "bg": "#1a1014",
            "containerBg": "#120c10",
            "accent": "#b05870",
            "highlight": "#d890a0",
            "success": "#70a878",
            "successBg": "rgba(80,160,100,0.12)",
            "errorBg": "rgba(180,70,80,0.12)",
            "text": "#f0e8ec",
            "muted": "#907878",
            "buttonBg": "#482838",
            "buttonHover": "#603848",
            "border": "#402830",
            "inputBorder": "#684858",
            "dialogBg": "rgba(26,16,20,0.93)",
            "dialogBorder": "#a06878",
            "glow": "rgba(176,88,112,0.15)",
            "glowSoft": "rgba(210,140,160,0.5)",
            "glowAccent": "rgba(176,88,112,0.4)",
            "dotBg": "#201418",
            "placeholder": "#786068",
            "dimText": "#806870",
            "slotBorder": "#786068",
            "cardBg": "#201418",
            "cardHover": "#281c20",
            "cardText": "#d0c0c4",
        },
        "pixel_palette": ["#b05870", "#d890a0", "#784050", "#90c088", "#c0a070", "#f0e8ec"],
    },
    # ── 欧洲古典 / European classical ──
    "renaissance": {
        "label": "文艺复兴",
        "mood": "文艺复兴、暖金、赭石、古典油画",
        "css": {
            "bg": "#181410",
            "containerBg": "#12100c",
            "accent": "#c09048",
            "highlight": "#e0c078",
            "success": "#608858",
            "successBg": "rgba(70,130,70,0.12)",
            "errorBg": "rgba(160,60,50,0.12)",
            "text": "#f0e8e0",
            "muted": "#a08870",
            "buttonBg": "#504028",
            "buttonHover": "#706038",
            "border": "#403828",
            "inputBorder": "#786850",
            "dialogBg": "rgba(24,20,16,0.93)",
            "dialogBorder": "#b08850",
            "glow": "rgba(192,144,72,0.15)",
            "glowSoft": "rgba(220,180,120,0.5)",
            "glowAccent": "rgba(192,144,72,0.4)",
            "dotBg": "#1c1810",
            "placeholder": "#807058",
            "dimText": "#887868",
            "slotBorder": "#807058",
            "cardBg": "#1c1810",
            "cardHover": "#242018",
            "cardText": "#d8ccb8",
        },
        "pixel_palette": ["#c09048", "#e0c078", "#806030", "#708848", "#a06050", "#f0e8e0"],
    },
    "baroque": {
        "label": "巴洛克",
        "mood": "巴洛克、金碧辉煌、深紫、奢华",
        "css": {
            "bg": "#14101a",
            "containerBg": "#0e0c14",
            "accent": "#c8a040",
            "highlight": "#e8d078",
            "success": "#609868",
            "successBg": "rgba(70,140,90,0.12)",
            "errorBg": "rgba(160,60,80,0.12)",
            "text": "#f0ece8",
            "muted": "#908878",
            "buttonBg": "#403020",
            "buttonHover": "#585038",
            "border": "#383028",
            "inputBorder": "#605850",
            "dialogBg": "rgba(20,16,26,0.93)",
            "dialogBorder": "#a88848",
            "glow": "rgba(200,160,64,0.18)",
            "glowSoft": "rgba(230,200,120,0.5)",
            "glowAccent": "rgba(200,160,64,0.4)",
            "dotBg": "#181418",
            "placeholder": "#787068",
            "dimText": "#807870",
            "slotBorder": "#787068",
            "cardBg": "#181418",
            "cardHover": "#201c24",
            "cardText": "#d0c8c0",
        },
        "pixel_palette": ["#c8a040", "#e8d078", "#786028", "#7088a0", "#a07088", "#f0ece8"],
    },
    "nordic": {
        "label": "北欧",
        "mood": "北欧、冷调、简约、森林与雪",
        "css": {
            "bg": "#0e1418",
            "containerBg": "#0a1014",
            "accent": "#5088a0",
            "highlight": "#88b8c8",
            "success": "#60a078",
            "successBg": "rgba(70,140,100,0.12)",
            "errorBg": "rgba(160,80,80,0.12)",
            "text": "#e8f0f4",
            "muted": "#708890",
            "buttonBg": "#283840",
            "buttonHover": "#385058",
            "border": "#283038",
            "inputBorder": "#486070",
            "dialogBg": "rgba(14,20,24,0.93)",
            "dialogBorder": "#508098",
            "glow": "rgba(80,136,160,0.15)",
            "glowSoft": "rgba(120,180,200,0.5)",
            "glowAccent": "rgba(80,136,160,0.4)",
            "dotBg": "#101418",
            "placeholder": "#587080",
            "dimText": "#607888",
            "slotBorder": "#587080",
            "cardBg": "#101418",
            "cardHover": "#181c24",
            "cardText": "#b8c8d0",
        },
        "pixel_palette": ["#5088a0", "#88b8c8", "#386078", "#70a878", "#d0a878", "#e8f0f4"],
    },
    "victorian": {
        "label": "维多利亚",
        "mood": "维多利亚、酒红、奶油色、复古英伦",
        "css": {
            "bg": "#181014",
            "containerBg": "#120c0e",
            "accent": "#784858",
            "highlight": "#a07080",
            "success": "#508860",
            "successBg": "rgba(60,120,70,0.12)",
            "errorBg": "rgba(140,60,60,0.12)",
            "text": "#f0e8e8",
            "muted": "#907878",
            "buttonBg": "#402830",
            "buttonHover": "#583840",
            "border": "#382828",
            "inputBorder": "#605050",
            "dialogBg": "rgba(24,16,20,0.93)",
            "dialogBorder": "#886068",
            "glow": "rgba(120,72,88,0.15)",
            "glowSoft": "rgba(160,120,140,0.5)",
            "glowAccent": "rgba(120,72,88,0.4)",
            "dotBg": "#1c1418",
            "placeholder": "#786868",
            "dimText": "#806868",
            "slotBorder": "#786868",
            "cardBg": "#1c1418",
            "cardHover": "#242018",
            "cardText": "#d0c4c4",
        },
        "pixel_palette": ["#784858", "#a07080", "#503040", "#608858", "#c0a068", "#f0e8e8"],
    },
    "mediterranean": {
        "label": "地中海",
        "mood": "地中海、陶土、海蓝、橄榄绿",
        "css": {
            "bg": "#14181a",
            "containerBg": "#0e1214",
            "accent": "#4088a0",
            "highlight": "#78b0c0",
            "success": "#70a060",
            "successBg": "rgba(80,140,70,0.12)",
            "errorBg": "rgba(180,70,60,0.12)",
            "text": "#e8f0ec",
            "muted": "#708078",
            "buttonBg": "#384838",
            "buttonHover": "#506050",
            "border": "#283830",
            "inputBorder": "#506858",
            "dialogBg": "rgba(20,24,26,0.93)",
            "dialogBorder": "#609080",
            "glow": "rgba(64,136,160,0.15)",
            "glowSoft": "rgba(120,180,192,0.5)",
            "glowAccent": "rgba(64,136,160,0.4)",
            "dotBg": "#101418",
            "placeholder": "#587068",
            "dimText": "#607870",
            "slotBorder": "#587068",
            "cardBg": "#101418",
            "cardHover": "#181c20",
            "cardText": "#b8c4c0",
        },
        "pixel_palette": ["#4088a0", "#78b0c0", "#c07848", "#70a060", "#e0c070", "#e8f0ec"],
    },
    # ── 故事/氛围 / Story & mood ──
    "fairy-tale": {
        "label": "童话",
        "mood": "童话、梦幻、柔和马卡龙、魔法",
        "css": {
            "bg": "#1a1418",
            "containerBg": "#141018",
            "accent": "#d070b0",
            "highlight": "#e8a8d0",
            "success": "#80c890",
            "successBg": "rgba(100,200,140,0.12)",
            "errorBg": "rgba(200,80,120,0.12)",
            "text": "#f8f0f4",
            "muted": "#a08898",
            "buttonBg": "#483848",
            "buttonHover": "#605058",
            "border": "#403848",
            "inputBorder": "#706068",
            "dialogBg": "rgba(26,20,24,0.93)",
            "dialogBorder": "#c078a8",
            "glow": "rgba(208,112,176,0.18)",
            "glowSoft": "rgba(230,170,210,0.5)",
            "glowAccent": "rgba(208,112,176,0.4)",
            "dotBg": "#20181c",
            "placeholder": "#807078",
            "dimText": "#887880",
            "slotBorder": "#807078",
            "cardBg": "#20181c",
            "cardHover": "#282024",
            "cardText": "#e0d4dc",
        },
        "pixel_palette": ["#d070b0", "#e8a8d0", "#80c890", "#f0d878", "#78b8e0", "#f8f0f4"],
    },
    "detective": {
        "label": "侦探",
        "mood": "侦探、 noir、昏黄灯光、悬疑",
        "css": {
            "bg": "#0c0c0a",
            "containerBg": "#080806",
            "accent": "#c8a028",
            "highlight": "#e0c858",
            "success": "#508050",
            "successBg": "rgba(60,120,60,0.12)",
            "errorBg": "rgba(160,60,50,0.12)",
            "text": "#e8e4d8",
            "muted": "#888068",
            "buttonBg": "#282418",
            "buttonHover": "#383428",
            "border": "#282418",
            "inputBorder": "#484430",
            "dialogBg": "rgba(12,12,10,0.95)",
            "dialogBorder": "#a88838",
            "glow": "rgba(200,160,40,0.12)",
            "glowSoft": "rgba(220,200,100,0.4)",
            "glowAccent": "rgba(200,160,40,0.35)",
            "dotBg": "#141410",
            "placeholder": "#686050",
            "dimText": "#706858",
            "slotBorder": "#686050",
            "cardBg": "#141410",
            "cardHover": "#1c1c18",
            "cardText": "#c0b8a8",
        },
        "pixel_palette": ["#c8a028", "#e0c858", "#404040", "#508050", "#a06050", "#e8e4d8"],
    },
    "sci-fi": {
        "label": "科幻",
        "mood": "科幻、霓虹、深空、科技感",
        "css": {
            "bg": "#080a14",
            "containerBg": "#060814",
            "accent": "#40c0e0",
            "highlight": "#80e0f8",
            "success": "#60e080",
            "successBg": "rgba(80,220,120,0.12)",
            "errorBg": "rgba(255,80,120,0.12)",
            "text": "#e0f0f8",
            "muted": "#6080a0",
            "buttonBg": "#182038",
            "buttonHover": "#283050",
            "border": "#182038",
            "inputBorder": "#304060",
            "dialogBg": "rgba(8,10,20,0.93)",
            "dialogBorder": "#4080c0",
            "glow": "rgba(64,192,224,0.2)",
            "glowSoft": "rgba(128,224,248,0.5)",
            "glowAccent": "rgba(64,192,224,0.45)",
            "dotBg": "#0c0e18",
            "placeholder": "#406080",
            "dimText": "#507090",
            "slotBorder": "#406080",
            "cardBg": "#0c0e18",
            "cardHover": "#121828",
            "cardText": "#b0c8e0",
        },
        "pixel_palette": ["#40c0e0", "#80e0f8", "#8060ff", "#60e080", "#ff6080", "#e0f0f8"],
    },
    "academy": {
        "label": "书院",
        "mood": "书院、书香、竹墨、文人",
        "css": {
            "bg": "#121410",
            "containerBg": "#0e100c",
            "accent": "#506848",
            "highlight": "#809878",
            "success": "#608858",
            "successBg": "rgba(70,130,70,0.12)",
            "errorBg": "rgba(140,60,60,0.12)",
            "text": "#e0e4dc",
            "muted": "#707868",
            "buttonBg": "#283028",
            "buttonHover": "#384038",
            "border": "#282c28",
            "inputBorder": "#485048",
            "dialogBg": "rgba(18,20,16,0.93)",
            "dialogBorder": "#607858",
            "glow": "rgba(80,104,72,0.12)",
            "glowSoft": "rgba(120,150,110,0.4)",
            "glowAccent": "rgba(80,104,72,0.35)",
            "dotBg": "#161814",
            "placeholder": "#606858",
            "dimText": "#686c60",
            "slotBorder": "#606858",
            "cardBg": "#161814",
            "cardHover": "#1e201c",
            "cardText": "#b8bcb0",
        },
        "pixel_palette": ["#506848", "#809878", "#384830", "#a08850", "#6088a0", "#e0e4dc"],
    },
    "myth": {
        "label": "神话",
        "mood": "神话、金色、深蓝、神秘",
        "css": {
            "bg": "#0c0e18",
            "containerBg": "#080a14",
            "accent": "#d0a830",
            "highlight": "#f0d060",
            "success": "#60a878",
            "successBg": "rgba(80,160,110,0.12)",
            "errorBg": "rgba(180,70,80,0.12)",
            "text": "#f0ece0",
            "muted": "#808078",
            "buttonBg": "#282418",
            "buttonHover": "#383428",
            "border": "#202428",
            "inputBorder": "#404850",
            "dialogBg": "rgba(12,14,24,0.93)",
            "dialogBorder": "#a88840",
            "glow": "rgba(208,168,48,0.18)",
            "glowSoft": "rgba(240,210,96,0.5)",
            "glowAccent": "rgba(208,168,48,0.4)",
            "dotBg": "#101218",
            "placeholder": "#606870",
            "dimText": "#686c78",
            "slotBorder": "#606870",
            "cardBg": "#101218",
            "cardHover": "#181c28",
            "cardText": "#c8c4b8",
        },
        "pixel_palette": ["#d0a830", "#f0d060", "#305088", "#60a878", "#c07878", "#f0ece0"],
    },
}

DEFAULT_THEME = "pink-cute"

AUDIO_PROFILES: dict[str, dict[str, str]] = {
    "retro": {
        "title": "Music Loops/Retro/Retro Mystic.ogg",
        "dialog": "Music Loops/Retro/Retro Comedy.ogg",
        "minigame": "Music Loops/Retro/Retro Beat.ogg",
        "victory": "Music Loops/Loops/Alpha Dance.ogg",
        "explore": "Music Loops/Retro/Retro Reggae.ogg",
    },
    "calm": {
        "title": "Music Loops/Loops/Night at the Beach.ogg",
        "dialog": "Music Loops/Loops/Flowing Rocks.ogg",
        "minigame": "Music Loops/Loops/German Virtue.ogg",
        "victory": "Music Loops/Loops/Cheerful Annoyance.ogg",
        "explore": "Music Loops/Loops/Sad Town.ogg",
    },
    "energetic": {
        "title": "Music Loops/Loops/Alpha Dance.ogg",
        "dialog": "Music Loops/Retro/Retro Beat.ogg",
        "minigame": "Music Loops/Loops/Time Driving.ogg",
        "victory": "Music Loops/Loops/Cheerful Annoyance.ogg",
        "explore": "Music Loops/Loops/Drumming Sticks.ogg",
    },
}

THEME_TO_AUDIO: dict[str, str] = {
    "pink-cute": "energetic",
    "ocean-dream": "calm",
    "forest-sage": "calm",
    "sunset-warm": "calm",
    "galaxy-purple": "calm",
    "candy-pop": "energetic",
    "retro-amber": "retro",
    "china-porcelain": "calm",
    "china-cinnabar": "calm",
    "china-ink": "calm",
    "dunhuang": "calm",
    "forbidden-red": "calm",
    "china-landscape": "calm",
    "china-rouge": "energetic",
    "renaissance": "calm",
    "baroque": "retro",
    "nordic": "calm",
    "victorian": "retro",
    "mediterranean": "calm",
    "fairy-tale": "energetic",
    "detective": "retro",
    "sci-fi": "calm",
    "academy": "calm",
    "myth": "retro",
}

DEFAULT_AUDIO_PROFILE = "retro"


# -- Created by Yuqi Hang (github.com/yh2072) --
def get_audio_profile(theme_name: str, mood_hint: str | None = None) -> dict[str, str]:
    """Return a BGM profile dict for a given theme.

    If mood_hint is provided (from AI), use that directly if it matches a profile.
    Otherwise fall back to the theme-to-audio mapping.
    """
    if mood_hint and mood_hint in AUDIO_PROFILES:
        return AUDIO_PROFILES[mood_hint]
    profile_key = THEME_TO_AUDIO.get(theme_name, DEFAULT_AUDIO_PROFILE)
    return AUDIO_PROFILES[profile_key]


def get_theme(name: str) -> dict:
    """Return theme dict by name. Falls back to pink-cute."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def get_theme_css(name: str) -> dict:
    """Return CSS color dict for a theme."""
    return get_theme(name)["css"]


def get_theme_spec(name: str) -> str:
    """Return a prompt-friendly text description of a theme for LLM consumption."""
    t = get_theme(name)
    css = t["css"]
    palette = ", ".join(t["pixel_palette"])
    return f"""
Theme: "{name}" ({t['label']})
风格氛围: {t['mood']}
- Background: {css['bg']}
- Container background: {css['containerBg']}
- Accent color: {css['accent']}
- Highlight: {css['highlight']}
- Success: {css['success']}
- Success background: {css['successBg']}
- Error background: {css['errorBg']}
- Text: {css['text']}
- Muted text: {css['muted']} (readable medium-brightness; use for secondary/secondary info)
- Button: {css['buttonBg']} / hover {css['buttonHover']}
- Border: {css['border']}
- Card background: {css['cardBg']}
- Dialog: {css['dialogBg']} with border {css['dialogBorder']}
- Pixel art palette: {palette}
⚠️ Color contrast rule: ALL text must be readable. Use 'highlight' or 'text' for primary text, 'muted' for secondary text. NEVER use dark colors (#333–#888) as text on dark card/bg backgrounds.
"""


def list_themes() -> list[dict]:
    """Return summary of all available themes for display."""
    return [
        {"id": k, "label": v["label"], "mood": v["mood"]}
        for k, v in THEMES.items()
    ]


def get_rendered_style_block(template_dir: str, theme: dict, ui: dict) -> str:
    """Render only the <style>...</style> block from template.html with theme and ui.
    Used by the player data package so the player can inject CSS without the full template.
    """
    engine = Path(template_dir)
    template_html = _read_file(engine / "template.html")
    start = template_html.find("<style>")
    end = template_html.find("</style>") + len("</style>")
    if start == -1 or end < start:
        return ""
    style_section = template_html[start:end]
    env = jinja2.Environment(undefined=jinja2.StrictUndefined, autoescape=False)
    tmpl = env.from_string(style_section)
    return tmpl.render(theme=theme, ui=ui)

# All mechanics are sim_*; template mechanics (MECHANIC_TO_FILE) no longer used.
# MECHANIC_TO_FILE = {
#     "matching": "matching.js",
#     "sorting": "sorting.js",
#     "exploration": "exploration.js",
# }


def _detect_mechanics(script: list) -> set[str]:
    """Scan the script array for minigame commands and collect mechanic types."""
    mechanics = set()
    for cmd in script:
        if isinstance(cmd, dict) and cmd.get("type") == "minigame":
            game = cmd.get("game", "")
            if game:
                mechanics.add(game)
    return mechanics


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _validate_js_string(js: str, label: str) -> str:
    """Validate and auto-repair a standalone JS snippet.

    Wraps the JS in a minimal HTML shell, runs _validate_assembled_js, then
    extracts the (possibly repaired) JS back out.  Used to fix minigames_js
    *before* it is stored in out_content / game.pkg.json — because the full
    HTML validation pass happens afterwards and its repairs are not reflected
    in out_content.
    """
    if not js or not js.strip():
        return js
    import re as _re
    fake_html = f"<script>\n{js}\n</script>"
    repaired_html = _validate_assembled_js(fake_html, label)
    m = _re.search(r'<script[^>]*>([\s\S]*?)</script>', repaired_html)
    return m.group(1).strip() if m else js


def _validate_assembled_js(html: str, output_path: str) -> str:
    """Extract all <script> content, run node --check, and attempt auto-repair.

    Returns the (possibly repaired) HTML.  Repairs are applied directly to *html*
    by mapping combined-JS line numbers back to the original ``<script>`` blocks.
    Up to 5 rounds of fix-then-revalidate are attempted.
    """
    import subprocess, tempfile, os, re as _re

    def _node_check(js_text: str) -> tuple[int, str]:
        """Return (returncode, stderr) from ``node --check``."""
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.js', delete=False, encoding='utf-8'
            ) as f:
                f.write(js_text)
                tmp = f.name
            r = subprocess.run(
                ['node', '--check', tmp], capture_output=True, text=True, timeout=15
            )
            os.unlink(tmp)
            return r.returncode, r.stderr.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return 0, ''

    for round_idx in range(5):
        scripts = _re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
        if not scripts:
            return html
        combined = '\n;\n'.join(s for s in scripts if s.strip())
        if not combined.strip():
            return html

        rc, err = _node_check(combined)
        if rc == 0:
            return html

        line_match = _re.search(r':(\d+)', err)
        err_line = int(line_match.group(1)) if line_match else 0
        lines = combined.split('\n')
        if err_line < 1 or err_line > len(lines):
            break

        bad = lines[err_line - 1].strip()
        fixed = False

        # Fix 1: extra standalone }); between registerMinigame blocks
        if _re.fullmatch(r'[}\);\s]+', bad):
            prev = lines[err_line - 2].strip() if err_line >= 2 else ''
            if prev in ('});', '})', '}'):
                # Map combined-JS line back to HTML and remove it
                html = _remove_combined_line_from_html(html, scripts, lines, err_line - 1)
                fixed = True

        # Fix 2: truncated hex color string
        if not fixed and _re.search(r"['\"]#[0-9a-fA-F]{0,5}\s*$", bad):
            full = _re.sub(
                r"(['\"])#([0-9a-fA-F]{0,5})\s*$",
                lambda m: f"{m.group(1)}#{m.group(2) + 'f' * (6 - len(m.group(2)))}{m.group(1)});",
                bad,
            )
            html = _replace_combined_line_in_html(html, scripts, lines, err_line - 1, full)
            fixed = True

        # Fix 3: incomplete gpx/grect line (truncated before the opening paren)
        # Error is often reported on the NEXT line; the real problem is a line with just "gpx" or "grect"
        if not fixed and ('Unexpected number' in err or 'Invalid or unexpected token' in err):
            prev_idx = err_line - 2  # 0-based index of line before the reported line
            if prev_idx >= 0:
                prev_line = lines[prev_idx].strip()
                if _re.fullmatch(r'(gpx|grect)\s*$', prev_line):
                    html = _remove_combined_line_from_html(html, scripts, lines, prev_idx)
                    fixed = True

        # Fix 3b: unquoted emoji/special char as object key (e.g. `❓: function` → `'❓': function`)
        if not fixed and 'Invalid or unexpected token' in err:
            for idx in range(len(lines)):
                line = lines[idx]
                m = _re.match(r"^(\s*)([^\w'\"\s][^:]*?)\s*:\s*function\s*\(", line)
                if m:
                    indent, key = m.group(1), m.group(2).strip()
                    if not (key.startswith("'") or key.startswith('"')):
                        fixed_line = f"{indent}'{key}': function(" + line[m.end():]
                        html = _replace_combined_line_in_html(html, scripts, lines, idx, fixed_line)
                        fixed = True
                        break  # fix one per round, revalidate will catch more

        # Fix 4: unterminated string literal — remove the bad line
        if not fixed and ('Unterminated string' in err or 'Invalid or unexpected token' in err):
            html = _remove_combined_line_from_html(html, scripts, lines, err_line - 1)
            fixed = True

        if fixed:
            tag = f"[SYNTAX-FIX] assembled round {round_idx + 1}: "
            print(f"  {tag}repaired line {err_line}: {bad[:80]}", file=sys.stderr)
            continue

        # Could not fix — log warning
        context = f' → {bad[:80]}' if bad else ''
        print(
            f"\n  ╔══ WARN: assembled HTML has JS syntax error (unfixable) ══╗\n"
            f"  ║  File: {output_path}\n"
            f"  ║  Error line {err_line}{context}\n"
            f"  ║  {err[:120]}\n"
            f"  ╚══════════════════════════════════════════════════════════╝\n",
            file=sys.stderr,
        )
        break

    return html


def _find_script_and_offset(scripts: list[str], lines: list[str], combined_line_idx: int):
    """Map a 0-based line index in the combined JS back to (script_index, line_within_script)."""
    offset = 0
    for si, script in enumerate(scripts):
        if not script.strip():
            continue
        script_lines = script.split('\n')
        # +1 for the `;\n` separator between scripts (except the first)
        block_len = len(script_lines) + (1 if si > 0 else 0)
        if combined_line_idx < offset + len(script_lines) + (1 if si > 0 else 0):
            local_idx = combined_line_idx - offset - (1 if si > 0 else 0)
            return si, max(0, local_idx), script
        offset += block_len
    return None, None, None


def _remove_combined_line_from_html(html: str, scripts, lines, combined_line_idx: int) -> str:
    """Remove a single line (by combined-JS index) from the corresponding <script> in html."""
    si, local_idx, script = _find_script_and_offset(scripts, lines, combined_line_idx)
    if script is None:
        return html
    script_lines = script.split('\n')
    if 0 <= local_idx < len(script_lines):
        target_line = script_lines[local_idx]
        script_lines.pop(local_idx)
        new_script = '\n'.join(script_lines)
        return html.replace(script, new_script, 1)
    return html


def _replace_combined_line_in_html(html: str, scripts, lines, combined_line_idx: int, replacement: str) -> str:
    """Replace a single line (by combined-JS index) in the corresponding <script>."""
    si, local_idx, script = _find_script_and_offset(scripts, lines, combined_line_idx)
    if script is None:
        return html
    script_lines = script.split('\n')
    if 0 <= local_idx < len(script_lines):
        old_line = script_lines[local_idx]
        script_lines[local_idx] = replacement
        new_script = '\n'.join(script_lines)
        return html.replace(script, new_script, 1)
    return html


# -- Created by Yuqi Hang (github.com/yh2072) --
def assemble(
    template_dir: str,
    content: dict,
    output_path: str,
    *,
    out_content: dict | None = None,
) -> None:
    """Merge static templates with generated content into a single HTML file.

    Args:
        template_dir: Path to the engine/ directory.
        content: Dict with keys: config, pixel_art_js, script, minigame_data, theme.
        output_path: Where to write the final index.html.
        out_content: If provided, will be updated with the final config (after remap) and minigames_js
                     so the caller can write a data package without duplicating logic.
    """
    engine = Path(template_dir)
    config = dict(content["config"])  # copy so we can mutate for remap
    pixel_art_js = content["pixel_art_js"]
    script = content["script"]
    theme_name = content.get("theme", "pink-cute")

    # 1. Read template.html
    template_html = _read_file(engine / "template.html")

    # 2. Read engine.js
    engine_js = _read_file(engine / "engine.js")

    # 3. Read needed minigame JS files
    mechanics = _detect_mechanics(script)
    simulation_codes: dict[str, str] = content.get("simulation_codes", {})

    # Build ordered fallback map: if script sim names don't match code keys,
    # pair them by order so custom code is still used.
    _sim_code_remap: dict[str, str] = {}
    script_sims = sorted(m for m in mechanics if m.startswith("sim_"))
    code_sims = sorted(simulation_codes.keys())
    if script_sims and code_sims and script_sims != code_sims and len(script_sims) == len(code_sims):
        _sim_code_remap = dict(zip(script_sims, code_sims))
        print(
            f"  [assembler] sim key mismatch — remapping: "
            + ", ".join(f"{k}→{v}" for k, v in _sim_code_remap.items()),
            file=sys.stderr,
        )

    minigames_parts = []
    for mechanic in sorted(mechanics):
        if mechanic.startswith("sim_") and mechanic in simulation_codes:
            minigames_parts.append(simulation_codes[mechanic])
            continue
        if mechanic.startswith("sim_") and mechanic in _sim_code_remap:
            mapped_key = _sim_code_remap[mechanic]
            if mapped_key in simulation_codes:
                code = simulation_codes[mapped_key].replace(
                    f"registerMinigame('{mapped_key}'",
                    f"registerMinigame('{mechanic}'",
                )
                minigames_parts.append(code)
                continue
        if mechanic.startswith("sim_"):
            fallback_path = engine / "minigames" / "simulation.js"
            if fallback_path.exists():
                fallback_js = _read_file(fallback_path)
                patched = fallback_js.replace(
                    "registerMinigame('simulation'",
                    f"registerMinigame('{mechanic}'",
                )
                minigames_parts.append(patched)
            continue
        # Template mechanics no longer used (custom_simulation only).
        # filename = MECHANIC_TO_FILE.get(mechanic)
        # if not filename: continue
        # mg_path = engine / "minigames" / filename
        # if mg_path.exists(): minigames_parts.append(_read_file(mg_path))

    minigames_js = "\n".join(minigames_parts)

    # 3a. Validate and repair minigames_js *before* storing in out_content.
    #     The full HTML validation pass (_validate_assembled_js below) repairs
    #     the assembled index.html but its fixes are NOT reflected in out_content,
    #     so game.pkg.json would get broken JS → player.html injects it as a
    #     dynamic <script> which fails silently → registerMinigame never called
    #     → "小游戏类型尚未实现".  Validating here ensures both index.html and
    #     game.pkg.json receive the same corrected code.
    if minigames_js.strip():
        minigames_js = _validate_js_string(minigames_js, output_path + "[minigames]")

    # 3b. If sim codes were remapped, also patch config.minigames keys
    #     and endScreen.mechanics so GAME data matches the script references.
    if _sim_code_remap:
        _data_remap = _sim_code_remap  # script_name → code_name
        _inv_remap = {v: k for k, v in _data_remap.items()}  # code_name → script_name
        mg = config.get("minigames", {})
        for code_key, script_key in _inv_remap.items():
            if code_key in mg and script_key not in mg:
                mg[script_key] = mg.pop(code_key)
        es = config.get("endScreen", {})
        for m in es.get("mechanics", []):
            old_mech = m.get("mechanic", "")
            if old_mech in _inv_remap:
                m["mechanic"] = _inv_remap[old_mech]

    if out_content is not None:
        out_content.update({
            "config": config,
            "script": script,
            "pixel_art_js": pixel_art_js,
            "minigames_js": minigames_js,
            "theme": theme_name,
            "cover_js": content.get("cover_js", ""),
        })

    # 4. Build theme dict
    theme = get_theme_css(theme_name)

    # 5. Render the template
    game_config_js = (
        f"const GAME = {json.dumps(config, ensure_ascii=False, indent=2)};"
    )
    script_data_js = (
        f"const SCRIPT = {json.dumps(script, ensure_ascii=False, indent=2)};"
    )

    cover_js = content.get("cover_js", "")
    init_js = _build_init_js()

    env = jinja2.Environment(
        undefined=jinja2.StrictUndefined,
        autoescape=False,
    )
    tmpl = env.from_string(template_html)

    from .i18n import get_ui_strings, UI_STRINGS, LOCALE_NAMES
    ui = config.get("ui") or get_ui_strings(config.get("locale", "zh"))
    ui_locales = {code: get_ui_strings(code) for code in UI_STRINGS.keys()}
    ui_locales_json = json.dumps(ui_locales, ensure_ascii=False)

    # Inline cover_js after pixel art so drawCover is available
    combined_pixel_js = pixel_art_js
    if cover_js:
        combined_pixel_js += "\n;\n" + cover_js

    html = tmpl.render(
        theme=theme,
        ui=ui,
        ui_locales_json=ui_locales_json,
        locale_names=LOCALE_NAMES,
        title=config.get("title", "EdGame"),
        title_display=config.get("title", "EdGame"),
        subtitle=config.get("subtitle", ""),
        description=config.get("description", ""),
        total_chapters=config.get("totalChapters", 6),
        game_config=game_config_js,
        engine_js=engine_js,
        pixel_art_js=combined_pixel_js,
        minigames_js=minigames_js,
        script_data=script_data_js,
        init_js=init_js,
    )

    # 6. Final JS syntax check + auto-repair on the assembled HTML
    html = _validate_assembled_js(html, output_path)

    # 7. Write output
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def _build_init_js() -> str:
    """Build the initialization JavaScript that draws the title cover/logo, loads locale, and boots the game."""
    return """\
// Restore window.rect / window.px to engine signatures after pixel-art injection
(function() {
  var _mc = document.getElementById('main');
  var _mctx = _mc ? _mc.getContext('2d') : null;
  if (_mctx) {
    window.rect = function(x,y,w,h,c){_mctx.fillStyle=c;_mctx.fillRect(x,y,w,h);};
    window.px = function(x,y,c){_mctx.fillStyle=c;_mctx.fillRect(x,y,1,1);};
  }
})();

// Draw title cover art (or fall back to small logo)
(function() {
  var coverCanvas = document.getElementById('title-cover');
  var logoCanvas = document.getElementById('title-logo');
  if (coverCanvas && typeof drawCover === 'function') {
    try {
      var g = coverCanvas.getContext('2d');
      drawCover(g, coverCanvas.width, coverCanvas.height);
      coverCanvas.style.display = '';
      if (logoCanvas) logoCanvas.style.display = 'none';
    } catch(e) {
      coverCanvas.style.display = 'none';
      if (logoCanvas) logoCanvas.style.display = '';
    }
  } else {
    if (coverCanvas) coverCanvas.style.display = 'none';
  }
  if (logoCanvas && logoCanvas.style.display !== 'none' && typeof drawTitleLogo === 'function') {
    var g2 = logoCanvas.getContext('2d');
    drawTitleLogo(g2, logoCanvas.width, logoCanvas.height);
  }
})();

// Play title BGM on first interaction
document.addEventListener('click', function initAudio() {
  Audio.ensureContext();
  document.removeEventListener('click', initAudio);
}, { once: true });

// Apply UI strings to DOM (so language switch works without reload)
window.applyGameUi = function(ui) {
  if (!ui) return;
  var totalCh = (typeof GAME !== 'undefined' && GAME.totalChapters) ? GAME.totalChapters : 6;
  var el = document.getElementById('back-to-course');
  if (el && ui.backToCourse) el.textContent = '\\u2190 ' + ui.backToCourse;
  el = document.getElementById('share-btn');
  if (el && ui.shareGame) el.textContent = '\\u2398 ' + ui.shareGame;
  el = document.getElementById('dialog-next');
  if (el && ui.clickToContinue) el.textContent = ui.clickToContinue;
  el = document.getElementById('name-label');
  if (el && ui.nameLabel) el.textContent = ui.nameLabel;
  el = document.getElementById('player-name-input');
  if (el && ui.namePlaceholder) el.placeholder = ui.namePlaceholder;
  el = document.getElementById('start-btn');
  if (el && ui.startGame) el.textContent = ui.startGame;
  el = document.getElementById('start-hint');
  if (el) el.textContent = (ui.startHint || '') + ' \\u00B7 ' + totalCh + ' ' + (ui.chapters || '');
  el = document.getElementById('share-copied-msg');
  if (el && ui.shareCopied) el.setAttribute('data-msg', ui.shareCopied);
  var modal = document.getElementById('share-modal');
  if (modal) {
    var h3 = modal.querySelector('h3');
    if (h3 && ui.shareGame) h3.textContent = ui.shareGame;
    modal.querySelectorAll('.share-opt').forEach(function(o) {
      var a = o.getAttribute('data-action');
      var t = a === 'copy' ? ui.shareCopyLink : a === 'wechat' ? ui.shareWeChat : a === 'xiaohongshu' ? ui.shareXiaohongshu : a === 'linkedin' ? ui.shareLinkedIn : a === 'twitter' ? ui.shareTwitter : a === 'facebook' ? ui.shareFacebook : a === 'instagram' ? ui.shareInstagram : ui.shareGame;
      if (t) { o.textContent = (a === 'copy' ? '\\u2398 ' : a === 'linkedin' ? 'in ' : a === 'facebook' ? 'f ' : '') + t; o.setAttribute('title', t); }
    });
  }
  document.documentElement.lang = ui.lang || (typeof GAME !== 'undefined' ? GAME.locale : 'zh');
};

// Switch game UI language using embedded UI_LOCALES (no fetch)
window.setGameLocale = function(lang) {
  if (!window.UI_LOCALES || !UI_LOCALES[lang]) return;
  Object.assign(GAME.ui, UI_LOCALES[lang]);
  GAME.locale = lang;
  window.applyGameUi(GAME.ui);
  document.querySelectorAll('.lang-opt').forEach(function(b) { b.classList.toggle('active', b.getAttribute('data-lang') === lang); });
  try { localStorage.setItem('edgame_lang', lang); } catch(e) {}
};

// Async locale loader — prefers embedded UI_LOCALES, then locales/{lang}.json
window._localeReady = (function() {
  var params = new URLSearchParams(location.search);
  var lang = params.get('lang') || (typeof localStorage !== 'undefined' ? localStorage.getItem('edgame_lang') : null);

  // Prefer embedded UI locales (no fetch)
  if (lang && window.UI_LOCALES && UI_LOCALES[lang] && GAME.locale !== lang) {
    Object.assign(GAME.ui, UI_LOCALES[lang]);
    GAME.locale = lang;
    window.applyGameUi(GAME.ui);
    document.querySelectorAll('.lang-opt').forEach(function(b) { b.classList.toggle('active', b.getAttribute('data-lang') === lang); });
    try { localStorage.setItem('edgame_lang', lang); } catch(e) {}
    return Promise.resolve();
  }

  if (!lang || lang === GAME.locale) return Promise.resolve();

  var basePath = location.pathname.replace(/\\/[^\\/]*$/, '');
  var url = basePath + '/locales/' + lang + '.json';

  return fetch(url).then(function(r) {
    if (!r.ok) return;
    return r.json();
  }).then(function(loc) {
    if (!loc) return;

    if (loc.meta) {
      if (loc.meta.title) GAME.title = loc.meta.title;
      if (loc.meta.subtitle) GAME.subtitle = loc.meta.subtitle;
      if (loc.meta.description) GAME.description = loc.meta.description;
      if (loc.meta.defaultPlayerName) GAME.defaultPlayerName = loc.meta.defaultPlayerName;
    }
    if (loc.characters && GAME.characters) {
      Object.keys(loc.characters).forEach(function(cid) {
        if (GAME.characters[cid]) GAME.characters[cid].name = loc.characters[cid];
      });
    }
    if (loc.dialogs && typeof SCRIPT !== 'undefined') {
      loc.dialogs.forEach(function(d) {
        var idx = d[0], name = d[1], text = d[2];
        if (SCRIPT[idx] && SCRIPT[idx].type === 'dialog') {
          SCRIPT[idx].name = name;
          SCRIPT[idx].text = text;
        }
      });
    }
    if (loc.minigames && GAME.minigames) {
      Object.keys(loc.minigames).forEach(function(key) {
        if (GAME.minigames[key]) GAME.minigames[key] = loc.minigames[key];
      });
    }
    if (loc.endScreen && GAME.endScreen && loc.endScreen.mechanics) GAME.endScreen.mechanics = loc.endScreen.mechanics;
    if (loc.ui) Object.assign(GAME.ui, loc.ui);
    GAME.locale = loc.locale || lang;

    var el;
    el = document.getElementById('title-text');
    if (el && loc.meta && loc.meta.title) el.textContent = loc.meta.title;
    el = document.getElementById('subtitle-text');
    if (el && loc.meta && loc.meta.subtitle) el.textContent = loc.meta.subtitle;
    el = document.getElementById('desc-text');
    if (el && loc.meta && loc.meta.description) el.textContent = loc.meta.description;
    if (window.applyGameUi && loc.ui) window.applyGameUi(loc.ui);
    else {
      el = document.getElementById('name-label');
      if (el && loc.ui && loc.ui.nameLabel) el.textContent = loc.ui.nameLabel;
      el = document.getElementById('player-name-input');
      if (el && loc.ui && loc.ui.namePlaceholder) el.placeholder = loc.ui.namePlaceholder;
      el = document.getElementById('start-btn');
      if (el && loc.ui && loc.ui.startGame) el.textContent = loc.ui.startGame;
      el = document.getElementById('start-hint');
      if (el && loc.ui) el.textContent = (loc.ui.startHint || '') + ' \\u00B7 ' + (GAME.totalChapters || '') + ' ' + (loc.ui.chapters || '');
      el = document.getElementById('dialog-next');
      if (el && loc.ui && loc.ui.clickToContinue) el.textContent = loc.ui.clickToContinue;
    }
    document.documentElement.lang = loc.ui && loc.ui.lang ? loc.ui.lang : lang;
    document.querySelectorAll('.lang-opt').forEach(function(b) { b.classList.toggle('active', b.getAttribute('data-lang') === lang); });
    try { localStorage.setItem('edgame_lang', lang); } catch(e) {}
  }).catch(function() {});
})();

// Wire language switcher buttons and set active state
(function() {
  function wire() {
    document.querySelectorAll('.lang-opt').forEach(function(btn) {
      var l = btn.getAttribute('data-lang');
      btn.addEventListener('click', function() { if (window.setGameLocale) setGameLocale(l); });
      if (typeof GAME !== 'undefined' && GAME.locale === l) btn.classList.add('active');
    });
  }
  if (typeof GAME !== 'undefined') wire();
  else document.addEventListener('DOMContentLoaded', wire);
})();
"""
