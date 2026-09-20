#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spec_to_outline.py —— 规格表转 PDP 骨架

把原始规格清单（CSV / JSON）转成待填写的 PDP 骨架：
主文案预留 3-5 个利益要点位，全部规格自动下沉到 Details 块。

用法:
    python spec_to_outline.py specs.csv
    python spec_to_outline.py specs.json --product 保温杯
    python spec_to_outline.py specs.csv --top 4 -o outline.md

CSV 格式（首行为表头，取前两列: 属性, 值）:
    属性,值
    容量,500ml
    材质,316不锈钢
"""

import argparse
import csv
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 主文案优先级的关键词：命中者更可能适合做利益要点
PRIORITY = ["续航", "电池", "快充", "保温", "保冷", "防水", "耐磨", "承重",
            "容量", "容积", "净重", "克重", "轻量", "材质", "面料", "成分",
            "版型", "尺码", "尺寸", "兼容", "适配", "免工具", "可拆", "机洗",
            "静音", "透气", "认证", "保修", "质保", "弹开", "一键"]

# 同类规格只保留一项，避免要点重复（如内胆材质 / 外壳材质）
CATEGORY = [
    ("材质", ["材质", "面料", "成分", "材料"]),
    ("重量", ["重"]),
    ("尺寸", ["尺寸", "口径", "高度", "长度", "宽度", "厚度", "直径"]),
    ("温控", ["保温", "保冷", "温度"]),
    ("电力", ["续航", "电池", "充电"]),
    ("容量", ["容量", "容积"]),
    ("外观", ["颜色", "配色", "色"]),
]


def category_of(key):
    for name, words in CATEGORY:
        if any(w in key for w in words):
            return name
    return None


def load(path):
    p = Path(path)
    if not p.exists():
        sys.exit("找不到文件：%s" % p)
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return list(data.items())
        items = []
        for row in data:
            if isinstance(row, dict):
                ks = list(row.keys())
                items.append((str(row.get(ks[0], "")), str(row.get(ks[1], "")) if len(ks) > 1 else ""))
        return items
    with p.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.reader(f) if r and any(c.strip() for c in r)]
    if not rows:
        return []
    if len(rows[0]) >= 2 and rows[0][0].strip().lower() in ("属性", "属性名", "key", "name", "spec"):
        rows = rows[1:]
    return [(r[0].strip(), r[1].strip() if len(r) > 1 else "") for r in rows]


def score(k, v):
    s = 0
    text = k + v
    for w in PRIORITY:
        if w in text:
            s += 2
    if any(ch.isdigit() for ch in v):
        s += 1
    return s


def build(items, product, top):
    if not items:
        sys.exit("规格表为空，无法生成骨架。")

    ranked = sorted(items, key=lambda kv: -score(kv[0], kv[1]))

    # 同类去重，保证要点之间信息不重复
    leads, used_cat = [], set()
    for k, v in ranked:
        cat = category_of(k)
        if cat and cat in used_cat:
            continue
        if cat:
            used_cat.add(cat)
        leads.append((k, v))
        if len(leads) >= top:
            break

    L = []
    L.append("# %s PDP 骨架（待填写）\n" % product)
    L.append("> 由 spec_to_outline.py 生成。括号内为填写提示，交付前请删除本行与所有提示。\n")

    L.append("## ① Hook\n")
    L.append("（12-25 字。说出它完成的动作或被消除的麻烦，不要用品牌名/品类名/空泛形容词开头）\n")

    L.append("## ② 引言\n")
    L.append("（2-3 句，单句 <=25 字。承接 Hook，给出核心购买理由。）\n")

    L.append("## ③ 利益要点（%d 条）\n" % len(leads))
    for k, v in leads:
        L.append("- **（利益词前置 4-8 字）**（%s：%s —— 转写成买家得到的什么？）" % (k, v))
    L.append("")
    L.append("> 转译公式：特征 + 机制 + 利益。参考 references/benefit-translation.md\n")

    L.append("## ④ 异议处理 / Good to know\n")
    L.append("- （最多 3 条。选本品类最容易被问的：尺码？耐用？安装？退货？）")
    L.append("- （真实硬伤必须明说，例如偏小、需组装）")
    L.append("> 参考 references/objection-library.md\n")

    L.append("## ⑤ CTA\n")
    L.append("**（复述利益的号召，10-20 字，不要写裸的「立即购买」）**\n")

    L.append("## ⑥ Details\n")
    L.append("| 属性 | 值 |")
    L.append("| --- | --- |")
    for k, v in items:
        L.append("| %s | %s |" % (k.replace("|", "/"), v.replace("|", "/")))
    L.append("")
    L.append("## 交付备注（必填）\n")
    L.append("- 丢弃的规格及理由：")
    L.append("- 无法从输入支撑、未写入的宣称：")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="规格表转 PDP 骨架")
    ap.add_argument("spec", help="规格文件 .csv 或 .json")
    ap.add_argument("--product", default="本产品", help="产品名，用于标题")
    ap.add_argument("--top", type=int, default=4, help="主文案要点数量，默认 4（建议 3-5）")
    ap.add_argument("-o", "--out", help="输出文件，默认打印到屏幕")
    args = ap.parse_args()

    items = load(args.spec)
    out = build(items, args.product, args.top)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print("已生成：%s（共 %d 项规格）" % (args.out, len(items)))
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
