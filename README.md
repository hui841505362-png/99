# Product Description Writer

把干巴巴的产品规格表，改写成**独立站商品详情页（PDP）主文案** —— 以利益驱动、可跳读、符合品牌调性，让人在手机上八秒内做出决定。

> 本 skill 基于 [SkillMedev/skills](https://github.com/SkillMedev/skills/tree/main/skills/product-description-writer) 的 `product-description-writer` 扩展。
> 原版只有一个 `SKILL.md`（已留存为 `SKILL.original.md`），此处补齐了 `references/` `scripts/` `assets/` 三个模块，并把主文件重写为中文版。

---

## 30 秒上手

**场景 A：直接让 AI 写。** 把规格表丢给 AI 就行，skill 会自动生效：

```
用 product-description-writer 写一份详情页文案：
500ml 保温杯，316 不锈钢内胆，双层真空，保温 6 小时，
净重 280g，口径 5.4cm，密封圈可拆，一键弹盖，礼盒装。
卖给通勤上班族，语气温暖一点。
```

**场景 B：自己控制流程。** 用脚本先搭骨架、写完再体检：

```bash
# 1. 规格表 → PDP 骨架
python scripts/spec_to_outline.py specs.csv --product 保温杯 -o outline.md

# 2. 填充骨架，写成稿 copy.md

# 3. 成稿体检
python scripts/check_copy.py copy.md

# 4. 宣称证据核查
python scripts/lint_claims.py copy.md --spec specs.csv
```

脚本只用 Python 3 标准库，无需安装任何依赖。

---

## 目录结构

```
product-description-writer/
├── SKILL.md              # 主文件，AI 读这个（中文扩展版）
├── SKILL.original.md     # 原版英文，仅作溯源留存
├── README.md             # 本文件
├── references/           # 知识库：写的时候按需查
│   ├── benefit-translation.md         卖点转译手册
│   ├── objection-library.md           异议处理库
│   ├── voice-calibration.md           品牌声音校准
│   ├── compliance-redlines.md         合规红线
│   ├── pdp-anatomy.md                 页面结构与范例
│   └── spec-triage-and-category.md    规格筛选与品类打法
├── scripts/              # 可执行工具
│   ├── spec_to_outline.py            规格表 → PDP 骨架
│   ├── check_copy.py                 成稿体检（评分）
│   └── lint_claims.py                宣称证据核查
└── assets/               # 模板素材
    ├── pdp-template.md               输出骨架
    ├── intake-brief.md               输入收集表
    ├── details-block-template.md     Details 字段清单
    └── swipe-file.md                 句式库
```

---

## 三个模块分别管什么

### references/ —— 写的时候查

不是让你通读，是卡壳时翻对应的那一份。

| 文件 | 什么时候查 |
|---|---|
| `benefit-translation.md` | 参数不知道怎么翻译成人话；写完不确定算不算"利益" |
| `objection-library.md` | 不知道买家会担心什么；不知道怎么回应硬伤 |
| `voice-calibration.md` | 拿不准品牌该用什么语气；想看同一卖点的不同档位写法 |
| `compliance-redlines.md` | 担心违规用词；被要求"写得夸张点" |
| `pdp-anatomy.md` | 不确定区块顺序和字数；想看完整改造范例 |
| `spec-triage-and-category.md` | 规格太多不知取舍；规格太少不知问什么 |

### scripts/ —— 能真跑

**`spec_to_outline.py`** 把规格表转成待填骨架，省掉搭结构的时间。主文案只留 3-5 个要点位，其余规格全部下沉到 Details 表格，且**同类规格自动去重**（内胆材质和外壳材质不会同时占位）。

```bash
python scripts/spec_to_outline.py specs.csv --product 保温杯 --top 4 -o outline.md
```

输入支持 CSV（前两列：属性,值）和 JSON（对象或对象数组）。

**`check_copy.py`** 成稿体检，八项检查输出 0-100 分：

| 代号 | 检查项 | 级别 |
|---|---|---|
| H | Hook 能否独立成立、长度是否合理 | warn |
| S | 句子长度（中文 ≤25 字 / 英文 ≤20 词） | warn / error |
| B | 要点是否加粗前置、条数是否 3-5 | warn / info |
| F | 空话占位词（优质、匠心、品质保证…） | warn |
| A | 绝对化用语（最好、第一、顶级、唯一…） | **error** |
| M | 医疗功效宣称（治疗、减肥、提高免疫力…） | **error** |
| D | 是否有 Details 规格块 | **error** |
| C | 是否出现裸号召（"立即购买"）、CTA 位置是否正确 | error / warn |

```bash
python scripts/check_copy.py copy.md            # 人类可读输出
python scripts/check_copy.py copy.md --lang en  # 强制英文规则
python scripts/check_copy.py copy.md --json     # 供程序消费
```

实测：同一份素材，差稿 10 分，好稿 100 分。A/M 两类是合规红线，必须清零才能交付。

**`lint_claims.py`** 拿成稿对照规格来源，揪出撑不住的宣称。抽数字、认证、对比、排名、服务承诺五类，逐条比对：

```bash
python scripts/lint_claims.py copy.md --spec specs.csv
python scripts/lint_claims.py copy.md --spec specs.json --all   # 连同有支撑的一并列出
```

输出分三档：**高危**（绝对化/功效，默认应删改）、**待核实**（来源里找不到依据，需用户确认或标注）、**支撑**（默认折叠不显示）。存在高危或待核实时退出码为 1，可直接接进 CI。

### assets/ —— 模板和素材

| 文件 | 用途 |
|---|---|
| `pdp-template.md` | 输出骨架，复制填充即可，含各区块常见错误 |
| `intake-brief.md` | 开写前收集什么；规格太薄时按品类该问哪一个问题 |
| `details-block-template.md` | 六大品类的 Details 必填字段；最容易漏写的五项 |
| `swipe-file.md` | Hook 八种起手式、要点五种连接、CTA 分档、禁用词替换表 |

---

## 完整走一遍（保温杯实例）

**1. 准备规格表** `specs.csv`

```csv
属性,值
容量,500ml
内胆材质,316不锈钢
净重,280g
口径,5.4cm
保温,6小时
保冷,12小时
```

**2. 生成骨架**

```bash
python scripts/spec_to_outline.py specs.csv --product 保温杯 -o outline.md
```

**3. 按骨架填写**，成稿 `copy.md`

**4. 体检 + 核查**

```bash
python scripts/check_copy.py copy.md
python scripts/lint_claims.py copy.md --spec specs.csv
```

判分标准与完整改造范例见 `references/pdp-anatomy.md` 第五节。

---

## 定制指南

**改词表** —— 空话、绝对化用语、功效词都在 `scripts/check_copy.py` 顶部的 `FILLER_ZH/EN`、`ABSOLUTE_ZH/EN`、`MEDICAL_ZH/EN`。公司有自己的禁用词清单，直接往里加。

**加品类** —— `references/spec-triage-and-category.md` 的品类打法，和 `assets/details-block-template.md` 的必填字段，两处一起加。

**调优先级** —— `scripts/spec_to_outline.py` 的 `PRIORITY` 决定哪些规格进主文案，`CATEGORY` 决定哪些算同类（避免要点重复）。

**改判分尺度** —— `check_copy.py` 里 `penalty = {"error": 12, "warn": 5, "info": 1}`。

改完记得把 D 盘的改动同步到 `C:\Users\41499\.workbuddy\skills\product-description-writer\`，两处保持一致。

---

## 边界：什么情况别用它

| 场景 | 该用什么 |
|---|---|
| 亚马逊 / 平台 Listing | `amazon-listing-optimizer`（本仓库有，未安装） |
| 把主文案批量扩成尺码/颜色变体 | `variant-copy-scaler`（本仓库有，未安装） |
| 广告投放素材、短视频脚本 | 不适用 |

---

## 安装位置

| 路径 | 作用 |
|---|---|
| `D:\workbuddy\skills\product-description-writer\` | 主副本，在这里改 |
| `C:\Users\41499\.workbuddy\skills\product-description-writer\` | 生效副本，WorkBuddy 实际扫描这里 |

两处内容一致。新增或改动 skill 后，通常需要重启会话才会出现在可用列表里。
