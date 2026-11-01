# -*- coding: utf-8 -*-
"""semantic_audit.py — 稿件语义一致性审计（确定性规则层）

只做**可判定**的检查：凡是需要"理解领域知识才能判断对错"的，本脚本不做，
交给人或 LLM 复核（见 references/protocol.md）。

用法：
    python semantic_audit.py --file manuscript.md --out report.md [--json out.json]

支持 .md / .txt / .docx（docx 需 python-docx）。
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher

# ---------------------------------------------------------------- 读取

def read_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        try:
            from docx import Document
        except ImportError:
            sys.exit("需要 python-docx 才能读 .docx")
        doc = Document(path)
        parts = []
        for p in doc.paragraphs:
            if p.text.strip():
                parts.append(p.text)
        for t in doc.tables:
            for row in t.rows:
                parts.append("\t".join(c.text.strip() for c in row.cells))
        return "\n".join(parts)
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def strip_markup(t):
    t = re.sub(r"\{\{[A-Za-z0-9]+\}\}", "", t)      # 文献占位符
    t = re.sub(r"\*\*|\*|`", "", t)
    t = re.sub(r"^#+ ", "", t, flags=re.M)
    return t


def split_sentences(t):
    """保守切句：不动 e.g. / i.e. / Fig. / et al. / 数字小数点"""
    t = re.sub(r"\b(e\.g|i\.e|Fig|Figs|Eq|Ref|vs|et al|cf|approx|no|No)\.", r"\1<DOT>", t)
    t = re.sub(r"(\d)\.(\d)", r"\1<DOT>\2", t)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(“\"']|\d)", t)
    return [p.replace("<DOT>", ".").strip() for p in parts if len(p.split()) > 2]


def paragraphs(t):
    return [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]


# 已知专名/基因家族/数据库缩写，不要求在本稿定义
STOP_ABBR = {
    "SD", "CI", "HR", "OR", "MAE", "RNA", "DNA", "FIG", "TABLE", "AND", "THE", "IQR", "ORCID",
    "REMARK", "TRIPOD", "CONSORT", "PRISMA", "STROBE", "GDSC", "CCLE", "TCGA", "GEO", "CMS",
    "PDX", "ECM", "GWAS", "SNP", "FDR", "BH", "LASSO", "PCA", "AUC", "ROC",
    "BCL", "MYC", "TP53", "KRAS", "EGFR", "HCC", "CRC", "GBM", "NSCLC", "AML", "CLL",
    "CRISPR", "ZIP", "CSV", "SHA", "API", "URL", "JSON", "PDF", "TIFF", "TSV",
}

# ---------------------------------------------------------------- 检查项

def check_number_conflict(text):
    """同名指标在不同处给出不同数值 —— 只统计带统计单位的量，避免把 n=25 / n=500 误判为冲突"""
    pat = re.compile(
        r"(?P<name>[A-Za-z][A-Za-z \-]{4,40}?)\s*"
        r"(?:was|were|is|are|=|of|reached|showed|gave)\s*"
        r"(?P<val>[-\u2212\u2013]?\d+(?:[.,]\d+)?)\s*(?P<unit>%|SD|MAE|HR|OR|CI|P)(?![A-Za-z])", re.I)
    BAN = {"at n", "of n", "in n", "n", "replicates", "of replicates", "patients", "samples",
           "cohorts", "genes", "pathways", "pairs", "agents", "events", "features"}
    seen = defaultdict(set)
    where = defaultdict(list)
    for m in pat.finditer(text):
        name = re.sub(r"\s+", " ", m.group("name")).strip().lower()
        name = re.sub(r"^(the|a|an|and|but|which|that|this|these|its|their|with|of)\s+", "", name)
        name = name.strip()
        # 整词匹配：单字母 "n" 若用子串匹配会误伤 random / linear 等词
        if len(name.split()) < 2 or any(re.search(rf"\b{re.escape(b)}\b", name) for b in BAN):
            continue
        if re.fullmatch(r"[-\d\s.,]+", name):
            continue
        val = m.group("val").replace("\u2212", "-").replace("\u2013", "-").replace(",", ".")
        seen[(name, (m.group("unit") or "").upper())].add(val)
        where[(name, (m.group("unit") or "").upper())].append(m.start())
    out = []
    for (name, unit), vals in seen.items():
        if len(vals) > 1 and len(where[(name, unit)]) <= 5:
            out.append(dict(kind="number_conflict", name=name, unit=unit,
                            values=sorted(vals), count=len(where[(name, unit)])))
    return out


def check_figure_refs(text):
    """图号引用 vs 图注：引用了却没图注 / 有图注却从未引用 / 顺序错乱"""
    legends = {}
    LEG = r"^\s*\*{0,2}(?:Fig(?:ure)?|FIG(?:URE)?)\.?\s*(\d+)\*{0,2}\.?\s"
    for m in re.finditer(LEG, text, re.M):
        legends[int(m.group(1))] = m.start()
    body_end = min(legends.values()) if legends else len(text)
    body = text[:body_end]
    cited = Counter(int(x) for x in re.findall(r"Fig(?:ure)?\.?\s*(\d+)", body))
    issues = []
    for n in sorted(set(cited) - set(legends)):
        issues.append(dict(kind="fig_cited_no_legend", fig=n, count=cited[n]))
    for n in sorted(set(legends) - set(cited)):
        issues.append(dict(kind="fig_legend_not_cited", fig=n))
    order = []
    for m in re.finditer(r"Fig(?:ure)?\.?\s*(\d+)", body):
        n = int(m.group(1))
        if n not in order:
            order.append(n)
    if order != sorted(order):
        issues.append(dict(kind="fig_out_of_order", order=order))
    return issues


def check_abbreviations(text):
    """缩写首次出现前未定义 —— 读者第一次看到不知道是什么。
    只在正文（Declarations 之前）检查；缩略语表与作者缩写不计。"""
    cut = re.search(r"\n#+\s*(Declarations|Abbreviations|List of abbreviations)", text, re.I)
    body = text[:cut.start()] if cut else text
    issues = []
    freq = Counter(re.findall(r"\b[A-Z]{2,6}\b", body))
    for m in re.finditer(r"\b([A-Z]{2,6})\b", body):
        abbr = m.group(1)
        if abbr in STOP_ABBR or len(abbr) <= 2:
            continue
        # 全大写且出现 ≤2 次：多为基因符号/专名，不是需要定义的缩写
        if freq[abbr] <= 2:
            continue
        before = body[:m.start()]
        # ① 首次出现即定义：ABBR (expansion) 或 (expansion, ABBR)
        defined_inline = re.search(rf"\([^)]*{abbr}[^)]*\)", before) or \
                         re.search(rf"\b{abbr}\b\s*\([^)]*\)", before)
        # ② 出现即当定义：expansion (ABBR) —— 前面紧跟括号内容
        defined_inline = defined_inline or re.search(rf"\([^)]{{3,60}}\)\s*{abbr}\b", before)
        # ③ 定义在文末缩写表：视为"先用后定义"，仍报
        if not defined_inline:
            issues.append(dict(kind="abbr_undefined", abbr=abbr, pos=m.start(),
                               ctx=body[max(0, m.start() - 50):m.start() + 20].replace("\n", " ")))
    # 同一缩写重复报，只留第一次
    seen = set(); uniq = []
    for i in issues:
        if i["abbr"] in seen:
            continue
        seen.add(i["abbr"]); uniq.append(i)
    return uniq


def check_dangling(text):
    """指代无先行词 / 指向不存在的位置"""
    sents = split_sentences(text)
    issues = []
    for i, s in enumerate(sents):
        low = s.lower()
        for word in ["the former", "the latter", "respectively"]:
            if word in low and i == 0:
                issues.append(dict(kind="dangling_reference", word=word, sent=s[:120]))
        if re.search(r"\b(as (shown|described|noted|above|below)|see above|the above)\b", low):
            issues.append(dict(kind="positional_reference", sent=s[:120]))
    return issues


def check_duplicate_sentences(text):
    """近重复句：同一意思写两遍，或同一句式反复起句"""
    sents = [s for s in split_sentences(text) if len(s.split()) >= 8]
    norm = [re.sub(r"[^a-z0-9 ]", "", s.lower()) for s in sents]
    issues = []
    for i in range(len(sents)):
        for j in range(i + 1, len(sents)):
            if abs(len(norm[i]) - len(norm[j])) > 40:
                continue
            r = SequenceMatcher(None, norm[i], norm[j]).ratio()
            if r >= 0.82:
                issues.append(dict(kind="near_duplicate", ratio=round(r, 2),
                                   a=sents[i][:110], b=sents[j][:110]))
    return issues[:8]


def check_repeated_openers(text):
    """同一开头（前 3 词）出现 ≥3 次 —— 读者最先察觉的机器痕迹"""
    sents = split_sentences(text)
    heads = Counter()
    for s in sents:
        w = s.split()[:3]
        if len(w) == 3:
            heads[" ".join(w).lower().strip(",;:")] += 1
    return [dict(kind="repeated_opener", head=h, count=c)
            for h, c in heads.items() if c >= 3]


def check_hedge_drift(text):
    """强断言词：prove/demonstrate/establish 用于相关性结果时属越级"""
    strong = re.findall(r"\b(prove[sd]?|proves|demonstrate[sd]?|establish(?:es|ed)?|"
                        r"confirm(?:s|ed)?|definitive(?:ly)?)\b", text, re.I)
    return [dict(kind="strong_claim", word=w, count=strong.count(w))
            for w in sorted(set(x.lower() for x in strong))]


def check_terminology(text):
    """同一对象的不同叫法（signature / score / model / panel），提示统一"""
    groups = {
        "评分/签名": r"\b(signature|score|index|panel|model|classifier|predictor)\b",
    }
    out = []
    for g, pat in groups.items():
        hits = Counter(m.group(1).lower() for m in re.finditer(pat, text, re.I))
        if len(hits) >= 4 and sum(hits.values()) >= 12:
            out.append(dict(kind="terminology_variants", group=g, variants=dict(hits)))
    return out


def check_section_contradiction(text):
    """局限段说"未验证"，正文说"验证了" —— 典型的跨节矛盾"""
    m = re.search(r"(limitation|limitations|caveat)", text, re.I)
    if not m:
        return []
    lim = text[m.start():m.start() + 2500].lower()
    body = text[:m.start()].lower()
    pairs = [("validat", "validat"), ("prospectiv", "prospectiv"), ("causal", "causal")]
    out = []
    for key, _ in pairs:
        in_lim = bool(re.search(rf"(not|no|lack|absence|without|remain)\w*\s+\w*\s*{key}", lim))
        in_body = bool(re.search(rf"\b{key}\w*\b", body))
        if in_lim and in_body:
            out.append(dict(kind="cross_section_tension", theme=key,
                            note="局限段否认、正文出现同类断言，需确认是否同指"))
    return out


# ---------------------------------------------------------------- 汇总

SEVERITY = {
    "number_conflict": "高",
    "fig_cited_no_legend": "高",
    "fig_legend_not_cited": "高",
    "fig_out_of_order": "中",
    "abbr_undefined": "中",
    "near_duplicate": "中",
    "repeated_opener": "中",
    "cross_section_tension": "高",
    "dangling_reference": "低",
    "positional_reference": "低",
    "strong_claim": "低",
    "terminology_variants": "低",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()

    raw = read_text(a.file)
    text = strip_markup(raw)

    issues = []
    issues += check_number_conflict(text)
    issues += check_figure_refs(text)
    issues += check_abbreviations(text)
    issues += check_dangling(text)
    issues += check_duplicate_sentences(text)
    issues += check_repeated_openers(text)
    issues += check_hedge_drift(text)
    issues += check_terminology(text)
    issues += check_section_contradiction(text)

    by_sev = defaultdict(list)
    for i in issues:
        by_sev[SEVERITY.get(i["kind"], "低")].append(i)

    L = ["# 语义一致性审计（确定性规则层）", "",
         f"- 文件：`{a.file}`",
         f"- 词数：{len(text.split())}｜句数：{len(split_sentences(text))}",
         f"- 命中：**{len(issues)}** 条｜高 {len(by_sev['高'])}｜中 {len(by_sev['中'])}｜低 {len(by_sev['低'])}", "",
         "> 本层只报**可判定**的不一致。真正的语义对错（机制说不通、证据不支持结论）"
         "见 `references/protocol.md` 的 LLM 复核流程。", ""]

    titles = {
        "number_conflict": "同名指标数值冲突",
        "fig_cited_no_legend": "图被引用但无图注",
        "fig_legend_not_cited": "有图注但正文未引用",
        "fig_out_of_order": "图号引用顺序错乱",
        "abbr_undefined": "缩写首次出现未定义",
        "near_duplicate": "近重复句",
        "repeated_opener": "同一句式反复起句",
        "cross_section_tension": "跨节陈述张力",
        "dangling_reference": "指代无先行词",
        "positional_reference": "指向性表述（as shown above）",
        "strong_claim": "强断言词",
        "terminology_variants": "术语变体不统一",
    }
    for sev in ["高", "中", "低"]:
        if not by_sev[sev]:
            continue
        L.append(f"## {sev}风险（{len(by_sev[sev])} 条）")
        L.append("")
        for i in by_sev[sev]:
            t = titles.get(i["kind"], i["kind"])
            L.append(f"### {t} — `{i['kind']}`")
            for k, v in i.items():
                if k == "kind":
                    continue
                L.append(f"- {k}: {v}")
            L.append("")
    open(a.out, "w", encoding="utf-8").write("\n".join(L))

    if a.json:
        json.dump(issues, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"命中 {len(issues)} 条（高 {len(by_sev['高'])} / 中 {len(by_sev['中'])} / 低 {len(by_sev['低'])}）")
    print(f"→ {a.out}")
    sys.exit(1 if by_sev["高"] else 0)


if __name__ == "__main__":
    main()
