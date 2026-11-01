# 语义一致性审计（确定性规则层）

- 文件：`examples/demo_manuscript.md`
- 词数：762｜句数：64
- 命中：**6** 条｜高 2｜中 4｜低 0

> 本层只报**可判定**的不一致。真正的语义对错（机制说不通、证据不支持结论）见 `references/protocol.md` 的 LLM 复核流程。

## 高风险（2 条）

### 同名指标数值冲突 — `number_conflict`
- name: ion of random sets that matched the score
- unit: %
- values: ['4.2', '6.1']
- count: 2

### 有图注但正文未引用 — `fig_legend_not_cited`
- fig: 2

## 中风险（4 条）

### 图号引用顺序错乱 — `fig_out_of_order`
- order: [3, 1]

### 缩写首次出现未定义 — `abbr_undefined`
- abbr: PFS
- pos: 3387
- ctx: random sets that matched the score was 6.1%.  The PFS analysis gave a 

### 近重复句 — `near_duplicate`
- ratio: 0.85
- a: The score was associated with overall survival in both.
- b: The score was associated with survival in both cohorts.

### 同一句式反复起句 — `repeated_opener`
- head: the score was
- count: 4
