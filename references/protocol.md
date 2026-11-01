# L3 语义复核协议

L1/L2 是脚本，L3 是**流程**。这一层的任务不是"找错别字"，而是回答三个问题：
这句话的证据在哪？它说得比证据多吗？它和别处矛盾吗？

---

## §1 换领域时重算基线（必做）

`assets/baseline.json` 来自生物信息学 16 篇全文。换领域后，旧的句长/连接词基线不再适用。

```python
# 取新领域的 PMC 全文（OA 子集），用同一分句器重算
import sys; sys.path.insert(0, "scripts")
from style_audit import sentences, CONNECTIVES, HEDGES, BOOSTERS
# 对每篇正文抽 <body> 段落 → sentences() → 汇总 → 写入 baseline.json 的 full_text
```

**要点**：基线必须与体检脚本使用**同一个分句器**。用别人的统计数字（如"平均 21 词/句"）而不重算，等于拿两把尺子量。

---

## §2 证据-结论对齐表（核心步骤）

逐条抽取"结论句"，填表。**一行一个断言，不合并**。

| # | 原句 | 断言类型 | 证据位置 | 证据强度 | 结论是否越级 |
|---|---|---|---|---|---|
| 1 | … | 因果/相关/描述/推断 | Fig. X / 表 Y / 引用[n] | 直接/间接/无 | 是/否 |

**判定规则**：

| 断言类型 | 最低证据 | 越级信号 |
|---|---|---|
| 因果（causes / drives / leads to） | 干预实验或 MR | 只有相关性数据 |
| 相关（associates with） | 同一数据集内的统计量 | 跨数据集外推 |
| 推断（suggests / may） | 需显式写限定 | 缺限定语 |
| 描述（we observed） | 数据本身 | 用了 evaluate/validate 等评价词 |

**必须报的三种越级**：
1. 相关数据说成因果（`X drives Y` 而只有关联）
2. 单队列说成普遍（`in colorectal cancer` 而只有 n=177 的队列）
3. 未校正说成校正后（正文写"独立于 Z"，但模型里没有 Z）

---

## §3 跨节一致性扫描

按顺序比对四处，任何两处说法冲突都要写进报告：

1. **摘要 vs 正文**：数字、样本量、结论强度
2. **Results vs Methods**：正文提到的分析，Methods 里有没有；反之亦然
3. **Discussion vs Results**：Discussion 是否引入了 Results 没有的结果
4. **局限段 vs 全文**：局限段说"未验证/不能推断"，正文却在用"验证了/说明"

最后一条最容易漏。判定词：`not validated` / `cannot exclude` / `preliminary` / `exploratory` 与正文的 `validated` / `demonstrates` / `establishes` 直接对撞。

---

## §4 术语一致性

同一对象只能有一个名字。检查这三组：

| 组 | 常见混用 |
|---|---|
| 评分对象 | signature / score / index / model / classifier / panel |
| 效应量 | HR / hazard ratio / risk ratio / OR |
| 数据来源 | cohort / dataset / series / set |

做法：取每个术语的首次定义句，确认后文是否一直沿用；改名必须显式（`hereafter the score`）。

---

## §5 报告格式

每条问题按四列写，便于作者取舍：

```
原句 → 问题类型 → 证据（图/表/引用） → 建议改法
```

**禁止**写"建议润色""表达不够准确"这类无法执行的评语。要么指出具体矛盾，要么不写。

---

## §6 与脚本的分工

| 问题 | 谁抓 |
|---|---|
| 图号乱序、缩写未定义、数值冲突 | L1 脚本 |
| 句长/连接词偏离基线 | L2 脚本 |
| 论断越级、跨节矛盾、术语混用 | **L3 人工** |
| 反复起句、小写开头、逐字重复 | **通读**（脚本给线索，人来定性） |

L3 不产出"评分"。语义审计的产出是**一张可逐条回应的清单**，不是分数。
