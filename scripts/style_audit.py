# -*- coding: utf-8 -*-
"""style_audit.py — 文体指标体检（对照语料基线）

用法：
    python style_audit.py --file manuscript.md --out report.md [--baseline assets/baseline.json]

输出四类指标：句长节奏、连接词密度与种类、hedge/booster、近重复开头。
判定阈值来自 assets/baseline.json（200 篇摘要 + 16 篇全文的实测）。
"""
import argparse
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BASELINE = os.path.join(os.path.dirname(HERE), "assets", "baseline.json")

CONNECTIVES = [
    "however", "moreover", "furthermore", "therefore", "thus", "consequently", "nevertheless",
    "in contrast", "by contrast", "although", "whereas", "while", "because", "since",
    "as a result", "in addition", "additionally", "finally", "first", "second", "third",
    "notably", "importantly", "specifically", "in particular", "for example", "for instance",
    "overall", "together", "meanwhile", "instead", "rather", "hence", "accordingly",
    "similarly", "conversely", "yet", "but",
]
HEDGES = ["may", "might", "could", "appears", "suggests", "suggest", "indicates", "likely",
          "probably", "approximately", "about", "somewhat", "tends", "consistent with"]
BOOSTERS = ["clearly", "obviously", "undoubtedly", "certainly", "definitely", "always", "never",
            "proves", "prove", "demonstrates unequivocally", "undeniably"]


def read(path):
    if path.lower().endswith(".docx"):
        from docx import Document
        d = Document(path)
        txt = "\n".join(p.text for p in d.paragraphs if p.text.strip())
    else:
        txt = open(path, encoding="utf-8", errors="replace").read()
    txt = re.sub(r"\{\{[A-Za-z0-9]+\}\}", "", txt)
    txt = re.sub(r"\*\*|\*|`", "", txt)
    txt = re.sub(r"^#+ ", "", txt, flags=re.M)
    return txt


def sentences(t):
    t = re.sub(r"\b(e\.g|i\.e|Fig|Figs|Eq|Ref|vs|et al|cf|approx|No)\.", r"\1<D>", t)
    t = re.sub(r"(\d)\.(\d)", r"\1<D>\2", t)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(“\"'\d])", t)
    return [p.replace("<D>", ".").strip() for p in parts if len(p.split()) > 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    a = ap.parse_args()

    base = json.load(open(a.baseline, encoding="utf-8"))["full_text"]
    t = read(a.file)
    S = sentences(t)
    L = sorted(len(s.split()) for s in S)
    n = len(L)
    mean = st.mean(L)
    long_pct = 100 * sum(1 for x in L if x >= 35) / n
    short_pct = 100 * sum(1 for x in L if x <= 15) / n

    low = t.lower()
    cc = {k: len(re.findall(rf"\b{re.escape(k)}\b", low)) for k in CONNECTIVES}
    cc = {k: v for k, v in cc.items() if v}
    dens = sum(cc.values()) / n * 100

    hed = sum(len(re.findall(rf"\b{re.escape(w)}\b", low)) for w in HEDGES)
    boo = sum(len(re.findall(rf"\b{re.escape(w)}\b", low)) for w in BOOSTERS)
    ratio = round(hed / boo, 2) if boo else float("inf")

    rows = [
        ("句子数", n, base["n_sent"], ""),
        ("平均句长", round(mean, 1), base["sent_mean"], "≤23 且 ≥20"),
        ("≥35 词句占比 %", round(long_pct, 1), base["long_pct"], "≤12"),
        ("≤15 词句占比 %", round(short_pct, 1), base["short_pct"], "28–33"),
        ("连接词密度 /百句", round(dens, 1), base["conn_density"], "≤22"),
        ("连接词种类", len(cc), base["conn_types"], "≥25 提示换叙事"),
        ("hedge /百句", round(hed / n * 100, 1), base["hedge_density"], "尽量接近基线"),
        ("booster /百句", round(boo / n * 100, 1), base["booster_density"], ""),
        ("hedge/booster", ratio, base["hedge_booster"], ">1"),
    ]

    def verdict(name, val, ref, rule):
        if not rule:
            return ""
        if name == "平均句长":
            return "⚠" if not (20 <= val <= 23) else "ok"
        if name == "≥35 词句占比 %":
            return "⚠" if val > 12 else "ok"
        if name == "≤15 词句占比 %":
            return "⚠" if not (28 <= val <= 33) else "ok"
        if name == "连接词密度 /百句":
            return "⚠" if val > 22 else "ok"
        if name == "连接词种类":
            return "⚠" if val < 25 else "ok"
        if name == "hedge/booster":
            return "⚠" if val < 1 else "ok"
        return ""

    L2 = ["# 文体体检（对照语料基线）", "",
          f"- 文件：`{a.file}`",
          f"- 基线：`{os.path.basename(a.baseline)}`（{base['source']}）", "",
          "| 指标 | 本稿 | 基线 | 建议 | 判定 |", "|---|---:|---:|---|---|"]
    for name, val, ref, rule in rows:
        L2.append(f"| {name} | {val} | {ref} | {rule} | {verdict(name, val, ref, rule)} |")
    L2 += ["", "## 连接词逐项（本稿 / 基线 每百句）", "", "| 词 | 本稿 | 基线 |", "|---|---:|---:|"]
    bc = base.get("conn_detail", {})
    for k in sorted(set(cc) | set(bc), key=lambda x: -(cc.get(x, 0) + bc.get(x, 0)))[:14]:
        L2.append(f"| {k} | {cc.get(k,0)/n*100:.2f} | {bc.get(k,0)/100:.2f} |")

    open(a.out, "w", encoding="utf-8").write("\n".join(L2))
    warn = sum(1 for name, val, ref, rule in rows if verdict(name, val, ref, rule) == "⚠")
    print(f"⚠ {warn} 项超阈值 → {a.out}")
    sys.exit(0)


if __name__ == "__main__":
    main()
