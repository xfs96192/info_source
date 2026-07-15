#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 doc_searcher 检索到的券商研报原始 JSON 格式化为按【资产/主题】分类的 markdown 日报。
用法: python3 format_report.py <raw_json_path> <output_md_path> <date_str>
"""
import json, sys, re

# 资产/主题分类关键词（按优先级顺序匹配）
CATEGORIES = [
    ("宏观", ["宏观", "经济形势", "GDP", "通胀", "CPI", "PPI", "财政", "货币政策", "逆周期", "社融", "PMI"]),
    ("策略", ["策略", "市场展望", "配置", "大势研判", "周观点", "行业比较", "风格"]),
    ("固收", ["债", "利率", "信用", "转债", "固收", "收益率", "国债", "城投", "ETF跟踪"]),
    ("A股", ["A股", "上证", "沪深", "创业板", "科创", "IPO", "打新", "两融", "北向"]),
    ("港股", ["港股", "恒生", "香港", "南向", "H股"]),
    ("美股", ["美股", "纳斯达克", "标普", "美国股", "海外算力", "美联储"]),
    ("黄金/贵金属", ["黄金", "金价", "贵金属", "白银"]),
    ("外汇/商品", ["外汇", "美元", "汇率", "原油", "油价", "大宗", "商品", "铜", "铝"]),
]

TYPE_MAP = {1:"个股点评",4:"晨报/市场动态",5:"行业/策略周报",13:"行业深度",6:"公司深度",3:"宏观研究"}

def classify(rec):
    text = (rec.get("title","") or "") + " " + (rec.get("content","") or "")[:200]
    ind = rec.get("industry.name")
    ind = ind[0] if isinstance(ind, list) and ind else (ind or "")
    for cat, kws in CATEGORIES:
        for kw in kws:
            if kw in text:
                return cat
    # 行业类归到行业观点
    return "行业观点"

def get_inst(rec):
    v = rec.get("institution.name")
    if isinstance(v, list) and v: return v[0]
    return v or "未知机构"

def summarize(content, limit=280):
    if not content: return ""
    # 去多余空白，取核心结论段
    c = re.sub(r"\s+"," ", content).strip()
    # 优先截取包含结论性词汇的部分
    return c[:limit] + ("…" if len(c) > limit else "")

def main():
    raw, out, date_str = sys.argv[1], sys.argv[2], sys.argv[3]
    data = json.load(open(raw, encoding="utf-8"))
    # 分类
    buckets = {}
    for rec in data:
        cat = classify(rec)
        buckets.setdefault(cat, []).append(rec)

    order = ["宏观","策略","固收","A股","港股","美股","黄金/贵金属","外汇/商品","行业观点"]
    lines = []
    lines.append(f"# 券商研报核心观点日报（{date_str}）\n")
    lines.append(f"> 汇总 {date_str} 各主流券商研报核心观点结论，覆盖宏观、策略、固收、A股/港股/美股、黄金、外汇及主要行业。共 {len(data)} 篇。\n")
    insts = sorted(set(get_inst(r) for r in data))
    lines.append(f"**覆盖机构**：{'、'.join(insts)}\n")
    lines.append("---\n")

    for cat in order:
        recs = buckets.get(cat, [])
        if not recs: continue
        lines.append(f"## {cat}\n")
        # 按机构排序
        recs.sort(key=lambda r: get_inst(r))
        for r in recs:
            inst = get_inst(r)
            title = r.get("title","").strip()
            author = r.get("author.name")
            author = author[0] if isinstance(author,list) and author else (author or "")
            aid = r.get("artifact_id","")
            summ = summarize(r.get("content",""))
            head = f"**【{inst}】{title}**"
            if author: head += f"（{author}）"
            lines.append(head + f" {aid}")
            lines.append(f"- {summ}\n")

    with open(out,"w",encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"OK wrote {out}, categories={ {k:len(v) for k,v in buckets.items()} }")

if __name__ == "__main__":
    main()
