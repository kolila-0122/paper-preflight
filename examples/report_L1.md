# Semantic consistency audit (deterministic layer)

- File: `examples/demo_manuscript.md`
- 762 words | 64 sentences
- Findings: **6** | high 2 | medium 4 | low 0

> This layer reports only **decidable** inconsistencies. For whether a claim is scientifically wrong, see the review protocol in `references/protocol.md`.

## High risk (2)

### Same metric reported with different values — `number_conflict`
- name: random sets that matched the score
- unit: %
- values: ['4.2', '6.1']
- count: 2

### Legend present but figure never cited — `fig_legend_not_cited`
- fig: 2

## Medium risk (4)

### Figures not cited in order — `fig_out_of_order`
- order: [3, 1]

### Abbreviation used before definition — `abbr_undefined`
- abbr: PFS
- pos: 3387
- ctx: random sets that matched the score was 6.1%.  The PFS analysis gave a 

### Near-duplicate sentences — `near_duplicate`
- ratio: 0.85
- a: The score was associated with overall survival in both.
- b: The score was associated with survival in both cohorts.

### Same sentence opener repeated — `repeated_opener`
- head: the score was
- count: 4
