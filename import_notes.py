#!/usr/bin/env python3
"""把笔记仓库 Miss001/data-engineering-notes 导入为博客文章（可重复执行）。

用法：
    git clone https://github.com/Miss001/data-engineering-notes _notes
    python3 import_notes.py --notes _notes      # 生成 _src/notes/*.md
    python3 build.py                            # 生成静态站

规则：
- 每篇 Markdown 笔记生成一篇文章；README.md、空文件跳过；与 _src/posts 手写文章重复的笔记跳过（见 SKIP）。
- 只有脚本/SQL 的目录（如 sql-helper、HDFS 小文件合并）合成一篇「代码合集」文章，同目录的 说明.md 作为正文开头。
- 分类：ai/ → agent，design/ → design，其余 → data。标签：领域（数据库/大数据/运维/开发）+ 产品（MySQL、Spark……）。
- 日期优先级：笔记自带 front matter 的 date > _src/note_dates.json > 该文件在笔记仓库里首次提交的日期 > 今天。
- 只做轻量排版：标题降级、补代码块语言、去掉无法访问的图片、==高亮== 改为加粗、转义 <PASSWORD> 等占位符。正文不改写。
"""
import argparse, datetime, hashlib, json, re, shutil, subprocess, sys, urllib.parse
from pathlib import Path

try:
    from pypinyin import lazy_pinyin
except ImportError:  # 拼音只用于生成稳定的英文 URL，缺了就没法保证 URL 不变，直接报错
    sys.exit("缺少依赖：pip install pypinyin")

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_src" / "notes"
DATES_FILE = ROOT / "_src" / "note_dates.json"
REPO = "Miss001/data-engineering-notes"
REPO_URL = f"https://github.com/{REPO}"

# 已有手写文章覆盖的笔记，不重复导入
SKIP = {
    "ai/ollama/安装说明.md", "ai/ollama/docker安装.md", "ai/ollama/模型部署.md",
    "ai/dify/部署说明.md", "ops/docker/deploy-centos7.9.md",
    "dev/python/创建新环境-迁移.md", "dev/python/环境配置.md",
}
CODE_EXT = {".py": "python", ".sh": "bash", ".sql": "sql", ".cnf": "ini"}

AREAS = {"database": "数据库", "bigdata": "大数据", "ops": "运维", "dev": "开发", "ai": "大模型", "design": "UI 设计"}
# 目录名（小写）→ 产品名；路径里最深的那个作为文章的「产品」
PRODUCTS = {
    "mysql": "MySQL", "oracle": "Oracle", "postgresql": "PostgreSQL", "tidb": "TiDB", "dm": "达梦",
    "opengauss": "openGauss", "oceanbase": "OceanBase", "gaussdb": "GaussDB", "mycat": "MyCat",
    "domestic": "国产数据库", "cdh6.3.0部署": "CDH", "hdfs 磁盘均衡": "HDFS", "hdfs大文件拆分": "HDFS",
    "hdfs小文件合并": "HDFS", "elasticsearch": "Elasticsearch", "kettle": "Kettle", "kylin升级": "Kylin",
    "spark升级": "Spark", "linux": "Linux", "docker": "Docker", "python": "Python", "dify": "Dify",
    "ollama": "Ollama",
}
EXTRA_TAGS = {"logstash": "Logstash", "etl": "ETL", "domestic": "国产数据库", "kylin升级": "Spark"}
LABELS = {  # 目录名 / 文件名 → 标题里的显示名
    "sql-helper": "常用 SQL 片段", "logstash": "Logstash", "cdh6.3.0部署": "", "kylin升级": "", "spark升级": "",
    "deploy-single": "单节点部署", "single-deploy": "单节点部署", "single-deploy-docker": "Docker 单机部署",
    "single-deploy-rpm": "RPM 单机部署", "docker-deploy": "Docker 部署", "file-deploy": "安装包部署",
    "extension-deploy": "扩展安装", "deploy-extension": "扩展安装", "ora2pg-deploy": "ora2pg 安装",
    "deploy-gs_rep_portal": "gs_rep_portal 安装", "deploy-ora2og": "ora2og 安装",
    "deploy-single-ce": "社区版单机部署", "deploy-single-oms-ce": "OMS 社区版部署",
    "xtrabackup8": "XtraBackup 8 备份与恢复", "mysqldump": "mysqldump 备份与恢复",
    "mysql2es": "MySQL 同步到 Elasticsearch", "es2mysql": "Elasticsearch 同步到 MySQL",
    "navicate连接": "Navicat 连接", "kylin4安装文档": "Kylin 4 安装文档",
    "cdh6.3.0部署spark3": "CDH 6.3.0 部署 Spark 3",
}


def label(name):
    key = name.lower()
    if key in LABELS:
        return LABELS[key]
    return re.sub(r"^\d+\.\s*", "", name)


def slugify(rel):
    parts = [p for p in Path(rel).with_suffix("").parts if p.lower() not in AREAS and p.lower() != "domestic"]
    s = "-".join(lazy_pinyin(" ".join(parts)))
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return (s[:90].rstrip("-")) or "note"


def meta_for(rel, is_dir=False):
    """rel: 相对仓库根目录的路径（文件或代码目录）。返回 title, category, tags。"""
    parts = list(Path(rel).parts)
    area = parts[0].lower()
    if rel == "links.md":
        return "常用链接", "data", ["常用链接"]
    names = parts if is_dir else parts[:-1]
    stem = parts[-1] if is_dir else Path(parts[-1]).stem
    pidx, product = None, AREAS.get(area, "笔记")
    for i, p in enumerate(names):
        if p.lower() in PRODUCTS:
            pidx, product = i, PRODUCTS[p.lower()]
    tags = [AREAS[area]] if area in AREAS else []
    for p in names:
        t = PRODUCTS.get(p.lower())
        if t and t not in tags:
            tags.append(t)
        t = EXTRA_TAGS.get(p.lower())
        if t and t not in tags:
            tags.append(t)
    start = (pidx + 1) if pidx is not None else 1
    if is_dir:
        sec = [label(p) for p in names[start:-1]]
    else:
        sec = [label(p) for p in names[start:]]
    sec = [s for s in sec if s]
    name = label(stem)
    if is_dir and pidx == len(names) - 1:  # 目录本身就是产品目录，如 HDFS小文件合并
        name, sec = stem, []
    head = product
    if sec:
        head += " " + " ".join(sec)
    if not name or name == (sec[-1] if sec else None):
        title = head
    elif product.lower() in name.lower() and not sec:
        title = name
    else:
        title = f"{head}：{name}"
    cat = {"ai": "agent", "design": "design"}.get(area, "data")
    return title, cat, tags


# ---------------- 正文轻量清理 ----------------
FENCE = re.compile(r"^(\s*)(```+)\s*([\w+-]*)\s*$")
SQL_START = re.compile(r"^(select|insert|update|delete|create|alter|drop|grant|revoke|show|set|begin|declare|with|call|use|flush|start|stop|change|install|reset|purge|truncate|explain|vacuum|analyze|comment|merge|exec|commit|rollback|kill|lock|unlock)\b", re.I)


def guess_lang(lines):
    body = [l.strip() for l in lines if l.strip()]
    if not body:
        return "text"
    first = next((l for l in body if not l.startswith(("#", "--", "//"))), body[0])
    if first.startswith("<"):
        return "xml"
    if first.startswith("{") or re.match(r"^\[\s*[{\"']", first):
        return "js"
    if re.match(r"^\[\s*\d", first):  # 日志输出
        return "text"
    if SQL_START.match(first):
        return "sql"
    kv = sum(1 for l in body if re.match(r"^\[[^\]]+\]$|^[\w.\-]+\s*=", l))
    if kv >= max(2, len(body) * 0.6):
        return "ini"
    return "bash"


def protect(text):
    """非代码文本：转义 <PLACEHOLDER>，==高亮== 改加粗；跳过 `行内代码`。"""
    out = []
    for i, seg in enumerate(re.split(r"(`[^`]*`)", text)):
        if i % 2 == 0:
            seg = re.sub(r"<([A-Z][A-Z_]{2,})>", r"&lt;\1&gt;", seg)
            seg = re.sub(r"==\s*([^=\n]+?)\s*==", r"**\1**", seg)
        out.append(seg)
    return "".join(out)


IMG = re.compile(r"!\[[^\]]*\]\(([^)]*)\)")


def clean_markdown(text):
    text = text.replace("\r\n", "\n").replace("\t", "    ") if False else text.replace("\r\n", "\n")
    lines = text.split("\n")
    # 1) 拆出代码块，块内保持原样；缩进在列表里的代码块提到顶层
    blocks, i = [], 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m:
            indent, ticks, lang = m.group(1), m.group(2), m.group(3)
            j, code = i + 1, []
            while j < len(lines) and not re.match(r"^\s*" + ticks + r"\s*$", lines[j]):
                code.append(lines[j][len(indent):] if lines[j].startswith(indent) else lines[j].lstrip())
                j += 1
            blocks.append(("code", lang or guess_lang(code), code))
            i = j + 1
            continue
        blocks.append(("text", lines[i]))
        i += 1
    # 2) 标题层级：笔记里用了一级标题就整体降一级（文章页已有 h1）
    levels = [len(re.match(r"^(#{1,6})", b[1]).group(1)) for b in blocks
              if b[0] == "text" and re.match(r"^#{1,6}(\s|[^#!\s])", b[1])]
    shift = 2 - min(levels) if levels else 0  # 最高一级标题统一成 ##（文章页已有 h1，目录取 2-3 级）
    out, prev = [], ""

    def kind(l):
        if not l.strip():
            return "blank"
        if re.match(r"^#{1,6}\s", l):
            return "h"
        if re.match(r"^\s*([-*+]|\d+[.)])\s+", l):
            return "li"
        if l.lstrip().startswith("|"):
            return "table"
        return "p"

    for b in blocks:
        if b[0] == "code":
            if out and out[-1].strip():
                out.append("")
            out.append("```" + b[1])
            out.extend(b[2])
            out.append("```")
            out.append("")
            prev = "blank"
            continue
        l = b[1].rstrip("\n")
        # 去掉无法公开访问的图片（私有仓库附件、图片待补占位）
        if IMG.search(l):
            l = IMG.sub(lambda m: "" if ("user-attachments" in m.group(1) or "图片待补" in m.group(1)
                                         or "/assets/" in m.group(1) or not m.group(1).startswith("http")) else m.group(0), l)
            if not l.strip():
                continue
        hc = re.match(r"^\s*<!--\s*(.*?)\s*-->\s*$", l)
        if hc:
            l = f"*{hc.group(1)}*" if hc.group(1) else ""
        l = l.replace("\u200b", "")
        hm = re.match(r"^(#{1,6})\s*(.*?)\s*#*\s*$", l)
        if hm and not l.startswith("#!") and hm.group(2):
            l = "#" * max(2, min(6, len(hm.group(1)) + shift)) + " " + hm.group(2)
        k = kind(l)
        if k != "blank" and prev != "blank" and (k == "h" or prev == "h" or (k != prev and k in ("li", "table") and not l.startswith(" "))):
            out.append("")
        out.append(protect(l))
        prev = k
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def summary_of(md, title):
    heads, in_code = [], False
    for l in md.split("\n"):
        if l.startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            m = re.match(r"^#{2,3}\s+(.*)", l)
            if m:
                h = re.sub(r"^[\d.、\s)）]+", "", re.sub(r"[*`#]", "", m.group(1))).strip()
                if h and h not in heads and len(h) < 40:
                    heads.append(h)
    if heads:
        s = "要点：" + "、".join(heads[:6]) + ("等" if len(heads) > 6 else "") + "。"
        return s if len(s) < 140 else s[:137] + "…"
    plain = re.sub(r"```.*?```", " ", md, flags=re.S)
    plain = re.sub(r"[#>*`|\-]+", " ", plain)
    plain = re.sub(r"&lt;|&gt;", "", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    return (plain[:90] + "…") if len(plain) > 90 else (plain or title)


def git_first_dates(notes):
    dates = {}
    try:
        log = subprocess.run(["git", "-C", str(notes), "log", "--format=@@%as", "--name-only", "--diff-filter=AR",
                              "-z" if False else "--no-renames"], capture_output=True, text=True, check=True,
                             env={"GIT_CONFIG_PARAMETERS": "'core.quotepath=false'", "PATH": "/usr/bin:/bin:/usr/local/bin"}).stdout
    except Exception:
        return dates
    cur = None
    for line in log.splitlines():
        if line.startswith("@@"):
            cur = line[2:]
        elif line.strip() and cur:
            dates[line.strip()] = cur  # log 从新到旧，最后一次赋值就是首次提交日期
    return dates


def front(title, date, cat, tags, summary, rel):
    src = REPO_URL + "/blob/main/" + urllib.parse.quote(rel)
    if (Path(rel).suffix == ""):
        src = REPO_URL + "/tree/main/" + urllib.parse.quote(rel)
    clean = lambda s: s.replace("\n", " ").replace(",", "，") if isinstance(s, str) else s
    return ("---\n"
            f"title: {title}\n"
            f"date: {date}\n"
            f"category: {cat}\n"
            f"tags: [{', '.join(clean(t) for t in tags)}]\n"
            f"summary: {clean(summary)}\n"
            f"source: {src}\n"
            f"source_name: {REPO} · {rel}\n"
            f"note_path: {rel}\n"
            "---\n\n")


def parse_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes", default=str(ROOT / "_notes"), help="笔记仓库 checkout 路径")
    args = ap.parse_args()
    notes = Path(args.notes).resolve()
    if not (notes / "README.md").exists():
        sys.exit(f"找不到笔记仓库：{notes}")
    overrides = json.loads(DATES_FILE.read_text(encoding="utf-8")) if DATES_FILE.exists() else {}
    git_dates = git_first_dates(notes)
    today = datetime.date.today().isoformat()
    hand_slugs = {re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f.stem) for f in (ROOT / "_src" / "posts").glob("*.md")}

    files = sorted(p for p in notes.rglob("*") if p.is_file() and ".git" not in p.parts)
    items = []  # (rel, is_dir, body)
    code_groups = {}
    for p in files:
        rel = p.relative_to(notes).as_posix()
        if p.suffix.lower() in CODE_EXT:
            g = p.parent
            while g != notes and not (g / "说明.md").exists():
                g = g.parent
            if g == notes:
                g = p.parent
            code_groups.setdefault(g, []).append(p)
    group_readmes = {g / "说明.md" for g in code_groups}
    skipped = []
    for p in files:
        rel = p.relative_to(notes).as_posix()
        if p.suffix.lower() != ".md":
            continue
        if p.name.lower() == "readme.md" or rel in SKIP or p in group_readmes:
            skipped.append(rel if p not in group_readmes else rel + "（并入代码合集）")
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            skipped.append(rel + "（空文件）")
            continue
        items.append((rel, False, text))
    for g, fs in sorted(code_groups.items()):
        rel = g.relative_to(notes).as_posix()
        intro = (g / "说明.md").read_text(encoding="utf-8").strip() if (g / "说明.md").exists() else ""
        parts = [intro, ""] if intro else []
        for f in sorted(fs):
            parts += [f"## {f.relative_to(g).as_posix()}", "", "```" + CODE_EXT[f.suffix.lower()],
                      f.read_text(encoding="utf-8", errors="replace").rstrip("\n"), "```", ""]
        items.append((rel, True, "\n".join(parts)))

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    seen, report = set(), []
    for rel, is_dir, text in items:
        fm, body = parse_fm(text)
        title, cat, tags = meta_for(rel, is_dir)
        group = code_groups.get(notes / rel, [])
        if is_dir and len(group) == 1 and rel.split("/")[-1].lower() not in LABELS and \
                any(q.suffix == ".md" and q.name.lower() != "readme.md" for q in (notes / rel).iterdir()):
            # 单个配置/脚本文件，如 mysql/部署/my.cnf → 「MySQL 部署：my.cnf」
            t, _, _ = meta_for(rel + "/" + group[0].name)
            title = t.rsplit("：", 1)[0] + "：" + group[0].name if "：" in t else t
        title = fm.get("title", title)
        slug = slugify(rel)
        if slug in seen or slug in hand_slugs:
            slug += "-" + hashlib.md5(rel.encode()).hexdigest()[:6]
        seen.add(slug)
        md = clean_markdown(body)
        date = fm.get("date") or overrides.get(rel) or git_dates.get(rel) or (
            git_dates.get(next((k for k in git_dates if k.startswith(rel + "/")), ""), None)) or today
        date = min(date, today)
        (OUT / f"{slug}.md").write_text(front(title, date, cat, tags, fm.get("summary") or summary_of(md, title), rel) + md,
                                        encoding="utf-8")
        report.append((cat, rel, slug, title))
    cats = {}
    for c, *_ in report:
        cats[c] = cats.get(c, 0) + 1
    print(f"imported {len(report)} notes → {OUT.relative_to(ROOT)}  {cats}; skipped {len(skipped)}")
    for s in skipped:
        print("  skip:", s)


if __name__ == "__main__":
    main()
