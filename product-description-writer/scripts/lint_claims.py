#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint_claims.py —— 宣称证据核查

从成稿中抽取所有"需要证据"的宣称，逐条对照规格来源，
找出来源里找不到依据的部分，避免无据宣称。

用法:
    python lint_claims.py copy.md --spec specs.json
    python lint_claims.py copy.md --spec specs.csv --json

输出分三档:
    [支撑]   在来源中找到依据
    [待核实] 来源无直接依据，需用户确认或改写
    [高危]   绝对化/功效类宣称，默认应删除或改写
"""

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 数字 + 单位（在去空格文本上匹配）
NUM_CLAIM = re.compile(
    r"\d+(?:\.\d+)?"
    r"(?:小时|天|分钟|秒|次|遍|年|个月|万次|转|kg|g|ml|l|mm|cm|m|℃|度|%|mah|w|v|db|d|denier)",
    re.I,
)
# 认证 / 标准
CERT = re.compile(
    r"(?:ISO\s?\d+|IP\d{2}|OEKO-?TEX|bluesign|GOTS|GRS|EFSA|EPA|FCC|ROHS|FDA|SGS|"
    r"CE|UL|3C|GB\s?\d+)",
    re.I,
)
# 对比 / 排名 / 时间承诺
COMPARE = re.compile(r"(?:比[^，。\s]{1,10}(?:更|快|轻|强|省|多|久)|优于|领先|超过|第一|唯一|最)")
PROMISE = re.compile(r"(?:终身|永久|永远|质保\s*\d+\s*年|\d+\s*年(?:包换|质保|保修)|无理由|免费换|当天发|次日达)")
ABSOLUTE = re.compile(r"(?:最好|最佳|最强|顶级|极品|唯一|国家级|世界级|全网最低|史无前例|独一无二|永不|彻底)")
MEDICAL = re.compile(
    r"(?:治疗|治愈|根治|疗效|消炎|杀菌|灭菌|防癌|抗癌|降血压|降血糖|减肥|瘦身|燃脂|排毒|祛疤|生发|壮阳|免疫力)"
)


def load_spec(path):
    p = Path(path)
    if not p.exists():
        sys.exit("找不到规格文件：%s" % p)
    raw = p.read_text(encoding="utf-8-sig")
    if p.suffix.lower() == ".json":
        data = json.loads(raw)
        if isinstance(data, dict):
            return " ".join("%s %s" % (k, v) for k, v in data.items())
        return " ".join(
            " ".join(str(x) for x in (r.values() if isinstance(r, dict) else [r]))
            for r in data
        )
    return raw


def flat_text(t):
    return re.sub(r"\s+", "", t)


BREAK_CHARS = "，。、；：（）()｜|!?！？"


def ctx(flat, start, end, pre=6):
    """取数字宣称及其前置词组，避免截出半截英文单词"""
    a = start
    cnt = 0
    while a > 0 and cnt < pre:
        ch = flat[a - 1]
        if (ch.isascii() and ch.isalpha()) or ch in BREAK_CHARS:
            break
        a -= 1
        cnt += 1
    return flat[a:end]


def normalize(s):
    return re.sub(r"[\s,，、|]", "", s).lower()


def in_spec(claim, spec_norm):
    """宣称中的关键片段是否出现在来源里"""
    core = normalize(claim)
    if len(core) >= 2 and core in spec_norm:
        return True
    # 逐段匹配：数字、认证名、关键词
    for piece in re.findall(r"\d+(?:\.\d+)?[A-Za-z\u4e00-\u9fff%]*|IP\d{2}|[A-Za-z]{3,}", claim):
        if len(piece) >= 2 and normalize(piece) in spec_norm:
            return True
    return False


def extract(raw_text):
    """在去空格文本上匹配，保证数字与单位不被空格拆开"""
    text = flat_text(raw_text)
    claims = []
    seen = set()

    def push(level, kind, c):
        c = c.strip()
        key = (kind, c)
        if c and key not in seen and 1 < len(c) <= 40:
            seen.add(key)
            claims.append({"kind": kind, "claim": c, "level": level})

    for m in ABSOLUTE.finditer(text):
        push("high", "绝对化用语", m.group(0))
    for m in MEDICAL.finditer(text):
        push("high", "功效/医疗宣称", m.group(0))
    for m in CERT.finditer(text):
        push("check", "认证/标准", m.group(0))
    for m in NUM_CLAIM.finditer(text):
        push("check", "数字宣称", ctx(text, m.start(), m.end()))
    for m in COMPARE.finditer(text):
        push("check", "对比/排名", m.group(0))
    for m in PROMISE.finditer(text):
        push("check", "服务承诺", m.group(0))
    return claims


def main():
    ap = argparse.ArgumentParser(description="宣称证据核查")
    ap.add_argument("copy", help="成稿文案文件")
    ap.add_argument("--spec", required=True, help="规格来源 .json/.csv/.txt")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--all", action="store_true", help="同时列出已有来源支撑的宣称")
    args = ap.parse_args()

    copy_path = Path(args.copy)
    if not copy_path.exists():
        sys.exit("找不到文案文件：%s" % copy_path)
    text = copy_path.read_text(encoding="utf-8")
    spec_norm = normalize(load_spec(args.spec))

    rows = []
    for c in extract(text):
        if c["level"] == "high":
            status = "高危"
        elif in_spec(c["claim"], spec_norm):
            status = "支撑"
        else:
            status = "待核实"
        rows.append({"status": status, "kind": c["kind"], "claim": c["claim"]})

    order = {"高危": 0, "待核实": 1, "支撑": 2}
    rows.sort(key=lambda r: order[r["status"]])

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    n_high = sum(1 for r in rows if r["status"] == "高危")
    n_check = sum(1 for r in rows if r["status"] == "待核实")
    print("共检出 %d 处需证据宣称：高危 %d · 待核实 %d · 有支撑 %d\n"
          % (len(rows), n_high, n_check, len(rows) - n_high - n_check))
    shown = rows if args.all else [r for r in rows if r["status"] != "支撑"]
    if not shown:
        print("（无需处理的宣称）")
    for r in shown:
        print("[%s] %-8s %s" % (r["status"], r["kind"], r["claim"]))
    if not args.all and len(rows) - n_high - n_check:
        print("\n（已省略 %d 条有来源支撑的宣称，--all 查看全部）"
              % (len(rows) - n_high - n_check))
    if n_high or n_check:
        print("\n处理顺序：高危项删除或改写；待核实项需用户提供证据，否则标注 [待核实] 交回。")
        return 1
    print("\n全部宣称均有来源支撑。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
