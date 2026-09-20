---
name: Product Description Writer
description: Writes the single on-site PDP master copy - a benefit-led, scannable product detail page in the brand's voice - from a raw spec sheet or feature list. 商品详情页/PDP 主文案、产品描述、卖点提炼、详情页改写。Use when you have a spec list, feature bullets, or a bare template description for one product and need conversion copy for its on-site product detail page. Do NOT use for Amazon or marketplace listings - use amazon-listing-optimizer instead; do NOT use to spin one master into many size/color variants - use variant-copy-scaler instead.
---

# Product Description Writer

把产品规格翻译成**独立站商品详情页（PDP）主文案**：以利益驱动、可跳读、符合品牌调性，让人在手机上八秒内做出决定。

> 扩展版：在原版 SKILL.md 基础上增加了 `references/` `scripts/` `assets/` 三个模块，
> 按需取用，不要一次性全部读入。

---

## 资源索引

| 需要时 | 去哪里 |
|---|---|
| 把参数翻译成利益 | `references/benefit-translation.md` |
| 处理买家疑虑 | `references/objection-library.md` |
| 判断品牌语气 | `references/voice-calibration.md` |
| 担心违规用词 | `references/compliance-redlines.md` |
| 拿不准结构 / 想看范例 | `references/pdp-anatomy.md` |
| 规格太多不知取舍 | `references/spec-triage-and-category.md` |
| 输出骨架模板 | `assets/pdp-template.md` |
| 收集输入 | `assets/intake-brief.md` |
| 写 Details 块 | `assets/details-block-template.md` |
| 找句式参考 | `assets/swipe-file.md` |

**脚本**（Python 3，无第三方依赖）：

```bash
# 规格表 → PDP 骨架（省去搭结构的时间）
python scripts/spec_to_outline.py specs.csv --product 保温杯 -o outline.md

# 成稿体检：句长、要点加粗、空话、绝对化用语、Details 缺失、裸 CTA
python scripts/check_copy.py copy.md

# 宣称证据核查：找出来源里撑不住的数字、认证、承诺
python scripts/lint_claims.py copy.md --spec specs.csv
```

---

## Workflow

1. **收集输入。** 拿规格清单、目标客户、品牌调性。调性未知就按 `references/voice-calibration.md` 从品类反推，**最多问一个校准问题**。规格太薄时按 `assets/intake-brief.md` 的补问清单要一个关键细节 —— 不要自己脑补填充。
   - 规格较多时，先跑 `spec_to_outline.py` 生成骨架，别从空白页开始。

2. **找到唯一的购买理由。** 说出核心转变或要完成的任务，而不是品类名（"切熟透的番茄不压烂它"，不是"刀"）。这是 Hook。八种起手式见 `assets/swipe-file.md`。

3. **逐条把规格翻译成利益。** 特征 + 机制 + 利益（"316 不锈钢，意味着海边浴室的盐雾也锈不透它"）。保留规格以建立可信度，加上利益以建立欲望。翻译不出买家利益的规格直接丢弃。详见 `references/benefit-translation.md`。

4. **找出并回应异议。** 说出买家没讲出口的疑虑 —— 尺码、合身、耐用、退货、"这适合我吗" —— 每条给一句让人安心的话，织进要点或 "Good to know"。真的偏小就要明说。见 `references/objection-library.md`。

5. **按 F 型扫描组装。** Hook 开头 → 2-3 句引言 → 3-5 条利益要点（利益词前置、前 2-4 字加粗）→ 复述利益的 CTA → 底部放 Details 块装所有数字、尺寸、材质、保养。结构细节与范例见 `references/pdp-anatomy.md`。

6. **校准语气。** 句长、用词、温度都要贴合品牌（高端护肤冷静克制，零食品牌活泼调皮）。五档光谱见 `references/voice-calibration.md`。

7. **交付前自检。** 跑 `check_copy.py`，A/M 类问题（绝对化、功效宣称）必须清零；跑 `lint_claims.py` 确认每个宣称都有来源支撑。见 `references/compliance-redlines.md`。

---

## Quality bar

- 第一行能独立成立 —— 很多买家只会读这一行。
- 每条利益都能追溯到来源里的某个规格；留下来的每个规格都值得占那个位置。
- 中文单句 ≤25 字，英文 ≤20 词；要点把利益放最前面。
- 找参数的人能在 Details 块里找到每一个数字，又不干扰主文案的说服节奏。
- 买家在加购前会有的每个疑虑，都被诚实回答了。
- 没有任何一行是"所有同行都能原样说"的。

---

## Deliverable

输出完整 PDP 主文案，一个可直接粘贴的整块：Hook 行 → 2-3 句引言 → 3-5 条利益要点（利益前置、开头加粗）→ 异议处理或 "Good to know" → 复述利益的 CTA → Details/Specs 块（来源里每一个数字、尺寸、材质、保养方式）。

**文末必须附两段说明**（这是交付的一部分，不是可选项）：

```
丢弃的规格及理由：
- [规格]：[为什么它不进主文案]

无法从输入支撑、未写入的宣称：
- [宣称]：[缺少什么依据]
```

---

## Do NOT

- 不得编造性能数字、认证、材质或健康/安全/收益类宣称。只用来源提供的信息；被要求写来源撑不住的效果时，拒绝并给出合规替代方案。
- 不得以"优质品质"或任何泛泛的品类名开头。
- 不得伪造稀缺感、倒计时或低库存紧迫感。只在真实情况下使用（限量批次、季节性、真实低库存）。
- 不得保留翻译不出买家利益的特性。
- 不得以光秃秃的"立即购买"结尾 —— CTA 要复述利益。
- 不得跳过异议处理，尤其是真实的硬伤（偏小、需组装、有气味）。
