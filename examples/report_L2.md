# Style audit against corpus baseline

- File: `examples/demo_manuscript.md`
- Baseline: `baseline.json` (16 篇 PMC 全文（用本脚本同一分句器重算）)

| Metric | This manuscript | Baseline | Target | Verdict |
|---|---:|---:|---|---|
| Sentences | 64 | 5715 |  |  |
| Mean sentence length | 11.6 | 21.9 | 20-23 | ⚠ |
| Sentences >= 35 words, % | 1.6 | 9.9 | <=12 | ok |
| Sentences <= 15 words, % | 78.1 | 31.5 | 28-33 | ⚠ |
| Connectives per 100 sentences | 14.1 | 21.2 | <=22 | ok |
| Connective types | 5 | 38 | >=25; low values usually mean a missing rhetorical slot | ⚠ |
| Hedges per 100 sentences | 12.5 | 12.2 | as close to baseline as possible |  |
| Boosters per 100 sentences | 0.0 | 0.1 |  |  |
| Hedge/booster ratio | inf | 116.33 | >1 | ok |

## Connectives, per 100 sentences

| Connective | This manuscript | Baseline |
|---|---:|---:|
| while | 0.00 | 1.40 |
| overall | 3.12 | 0.80 |
| furthermore | 0.00 | 0.70 |
| however | 0.00 | 0.70 |
| whereas | 0.00 | 0.63 |
| additionally | 0.00 | 0.59 |
| therefore | 4.69 | 0.53 |
| but | 3.12 | 0.52 |
| notably | 0.00 | 0.53 |
| first | 1.56 | 0.52 |
| although | 0.00 | 0.49 |
| moreover | 0.00 | 0.46 |
| rather | 0.00 | 0.45 |
| finally | 0.00 | 0.45 |