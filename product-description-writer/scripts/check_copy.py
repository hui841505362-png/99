#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_copy.py —— PDP 文案体检

按 product-description-writer 的质量标准检查成稿，输出问题清单与评分。

用法:
    python check_copy.py copy.md
    python check_copy.py copy.md --lang en
    python check_copy.py copy.md --json

检查项:
    H  Hook 是否独立成立且长度合理
    S  句子长度（中文 <=25 字 / 英文 <=20 词）
    B  要点是否加粗前置
    F  空话 / 占位词
    A  绝对化用语（合规风险）
    M  医疗功效宣称（高危）
    D  Details 规格块是否存在
    C  CTA 是否复述利益
"""

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- 词表

FILLER_ZH = [
    "高品质", "优质", "卓越", "匠心", "极致", "物超所值", "性价比高",
    "质量保证", "品质保证", "放心购买", "理想选择", "最佳选择", "不二之选",
    "精心设计", "做工精良", "正品保障", "正规渠道", "高档",
    "轻松上手", "安装简便", "操作简单",
]
FILLER_EN = [
    "premium quality", "high quality", "top quality", "excellent quality",
    "best choice", "perfect choice", "great value",
]

ABSOLUTE_ZH = [
    "最好", "最佳", "最强", "最便宜", "第一", "顶级", "极品", "唯一",
    "国家级", "世界级", "全网最低", "史无前例", "独一无二", "绝无仅有",
    "遥遥领先", "永远", "永不", "彻底解决", "百分之百",
]
ABSOLUTE_EN = [
    "best", "no.1", "#1", "number one", "top-rated", "world-class",
    "unbeatable", "never", "forever", "100% effective", "guaranteed",
]

MEDICAL_ZH = [
    "治疗", "治愈", "根治", "疗效", "消炎", "杀菌", "灭菌", "防癌", "抗癌",
    "降血压", "降血糖", "降血脂", "减肥", "瘦身", "燃脂", "排毒", "祛疤",
    "生发", "壮阳", "提高免疫力", "增强免疫", "包治", "药效",
]
MEDICAL_EN = [
    "cure", "treat disease", "anti-cancer", "heals", "therapeutic",
    "weight loss", "burn fat", "detox", "boost immunity",
]

BARE_CTA_ZH = ["立即购买", "马上购买", "点击购买", "加入购物车", "现在下单"]
BARE_CTA_EN = ["buy now", "add to cart", "purchase now", "order now"]

DETAILS_HEAD = re.compile(
    r"^\s*#{0,6}\s*(details|specs|specifications|规格|参数|详情|商品参数)\s*[:：]?\s*$",
    re.I,
)

# ---------------------------------------------------------------- 工具


def detect_lang(text):
    han = len(re.findall(r"[\u4e00-\u9fff]", text))
    letters = len(re.findall(r"[A-Za-z]", text))
    if han == 0:
        return "en"
    return "zh" if han / max(han + letters, 1) > 0.3 else "en"


def split_sentences(text, lang):
    text = re.sub(r"[ \t]+", " ", text)
    if lang == "zh":
        parts = re.split(r"[。！？!?；;\n]+", text)
    else:
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def sentence_len(s, lang):
    body = re.sub(r"[#*\->|`\s]", "", s)
    if lang == "zh":
        return len(re.findall(r"[\u4e00-\u9fff]", body)) or len(body)
    return len(re.findall(r"[A-Za-z']+", body))


def strip_md(line):
    """去掉标题符号与空白，保留 ** 强调标记"""
    return re.sub(r"^[\s>#]+", "", line).strip()


def bullet_body(line):
    """去掉列表符号，保留 ** 强调标记"""
    return re.sub(r"^\s*(?:[-*+]|\d+[.)])\s*", "", line).strip()


SPEC_LINE = re.compile(
    r"\d+\s*(?:ml|l|g|kg|cm|mm|m|℃|度|h|小时|天|次|w|v|mah|d|%)", re.I)


def is_spec_line(line):
    """规格行：表格行、含 ｜ 分隔、或含数字+单位"""
    s = line.strip()
    return s.startswith("|") or "｜" in s or bool(SPEC_LINE.search(s))


def is_bullet(line):
    return bool(re.match(r"^\s*[-*+]\s+", line)) or bool(re.match(r"^\s*\d+[.)]\s+", line))


# ---------------------------------------------------------------- 检查


def check(text, lang=None):
    lang = lang or detect_lang(text)
    issues = []
    lines = text.splitlines()

    def add(code, level, msg):
        issues.append({"code": code, "level": level, "msg": msg})

    # --- H: Hook
    first = next((strip_md(l) for l in lines if strip_md(l)), "")
    if first:
        n = sentence_len(first, lang)
        unit = "字" if lang == "zh" else "words"
        lo, hi = (8, 25) if lang == "zh" else (3, 12)
        if n < lo:
            add("H", "warn", "Hook 过短（%d %s），信息量不足：%s" % (n, unit, first[:40]))
        elif n > hi:
            add("H", "warn", "Hook 过长（%d %s），一行读不完：%s" % (n, unit, first[:40]))
        openers = ["高端", "优质", "品质"] if lang == "zh" else ["premium", "quality"]
        for w in openers:
            if first.lower().startswith(w.lower()):
                add("H", "error", "Hook 以空泛形容词开头（%s），应改为具体利益" % w)
    else:
        add("H", "error", "未找到 Hook（正文为空）")

    # --- S: 句子长度（要点行有自己的规范，交给 B 检查）
    max_len = 25 if lang == "zh" else 20
    hard = 35 if lang == "zh" else 30
    for s in split_sentences(text, lang):
        if is_bullet(s):
            continue
        n = sentence_len(s, lang)
        if n > hard:
            add("S", "error", "句子过长（%d）：%s..." % (n, s[:50]))
        elif n > max_len:
            add("S", "warn", "句子偏长（%d）：%s..." % (n, s[:50]))

    # --- B: 要点加粗前置
    bullets = [(i + 1, l) for i, l in enumerate(lines) if is_bullet(l)]
    if not bullets:
        add("B", "warn", "未检测到要点列表，缺少可跳读的利益点")
    else:
        for no, l in bullets:
            body = bullet_body(l)
            if not body.startswith("**"):
                add("B", "warn", "第 %d 行要点未加粗前置：%s" % (no, body[:40]))
            else:
                m = re.match(r"^\*\*(.+?)\*\*", body)
                if m and sentence_len(m.group(1), lang) > 12:
                    add("B", "info", "第 %d 行加粗部分过长，建议只加粗前 4-8 字" % no)
        if len(bullets) > 5:
            add("B", "warn", "要点 %d 条，超过建议的 3-5 条" % len(bullets))
        elif len(bullets) < 3:
            add("B", "warn", "要点仅 %d 条，少于建议的 3-5 条" % len(bullets))

    # --- F / A / M: 词表命中
    low = text.lower()

    def scan(words, code, level, label):
        hit = [w for w in words if w.lower() in low]
        if hit:
            add(code, level, "命中%s：%s" % (label, ", ".join(hit)))

    scan(FILLER_ZH if lang == "zh" else FILLER_EN, "F", "warn", "空话/占位词")
    scan(ABSOLUTE_ZH if lang == "zh" else ABSOLUTE_EN, "A", "error", "绝对化用语（合规风险）")
    scan(MEDICAL_ZH if lang == "zh" else MEDICAL_EN, "M", "error", "医疗功效宣称（高危）")

    # --- D: Details 块
    if not any(DETAILS_HEAD.match(l) for l in lines):
        add("D", "error", "缺少 Details/Specs 规格块，参数党无法找到全部数字")

    # --- C: CTA（只抓明确违规：裸号召 / 位置在 Details 之后）
    bare = BARE_CTA_ZH if lang == "zh" else BARE_CTA_EN
    nonword = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff]")
    for no, l in enumerate(lines, 1):
        clean = nonword.sub("", strip_md(l))
        if clean and any(clean == nonword.sub("", b) for b in bare):
            add("C", "error", "第 %d 行是裸号召（%s），CTA 应复述利益" % (no, clean))

    det_idx = next((i for i, l in enumerate(lines) if DETAILS_HEAD.match(l)), None)
    if det_idx is not None:
        after = [strip_md(l) for l in lines[det_idx + 1:]
                 if strip_md(l) and not is_spec_line(l)]
        if after:
            add("C", "warn", "Details 之后仍有正文，CTA 与利益应在 Details 之前：%s" % after[0][:30])

    # --- 评分
    penalty = {"error": 12, "warn": 5, "info": 1}
    score = max(0, 100 - sum(penalty[i["level"]] for i in issues))
    return {
        "lang": lang,
        "score": score,
        "counts": {
            "error": sum(1 for i in issues if i["level"] == "error"),
            "warn": sum(1 for i in issues if i["level"] == "warn"),
            "info": sum(1 for i in issues if i["level"] == "info"),
        },
        "issues": issues,
    }


# ---------------------------------------------------------------- 输出

ICON = {"error": "[X]", "warn": "[!]", "info": "[i]"}
NAME = {"H": "Hook", "S": "句长", "B": "要点", "F": "空话",
        "A": "绝对化", "M": "功效宣称", "D": "Details", "C": "CTA"}


def main():
    ap = argparse.ArgumentParser(description="PDP 文案体检")
    ap.add_argument("file", help="待检查的文案文件（.md/.txt）")
    ap.add_argument("--lang", choices=["zh", "en"], help="强制指定语言，默认自动检测")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print("找不到文件：%s" % path, file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    r = check(text, args.lang)

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    print("语言：%s   评分：%d/100" % (r["lang"], r["score"]))
    print("错误 %d · 警告 %d · 提示 %d\n" % (
        r["counts"]["error"], r["counts"]["warn"], r["counts"]["info"]))
    if not r["issues"]:
        print("未发现问题。")
        return 0
    for i in r["issues"]:
        print("%s [%s·%s] %s" % (ICON[i["level"]], i["code"], NAME.get(i["code"], ""), i["msg"]))
    print("\n建议：先修 [X]，再处理 [!]。A/M 类属合规风险，必须清零。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
