#!/usr/bin/env python3
"""极简静态博客生成器：把 _src/posts/*.md 渲染成静态 HTML，输出到仓库根目录。

用法：
    pip install markdown pygments
    python3 build.py
"""
import html, json, re, shutil, datetime
ASSET_V = datetime.datetime.now().strftime("%Y%m%d%H%M")
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import markdown
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "_src"

SITE = {
    "title": "宇宙超级无敌美少女的技术博客",
    "short": "Miss001",
    "author": "宇宙超级无敌美少女",
    "roles": ["数据工程师", "Agent 开发", "UI 设计"],
    "desc": "宇宙超级无敌美少女的技术博客：数据工程、Agent 开发与 UI 设计笔记。",
    "url": "https://miss001.github.io",
    "github": "https://github.com/Miss001",
    "email": "522160919@qq.com",
}

# 三个分类（文章 front matter 里写 category: data / agent / design）
CATEGORIES = [
    {"slug": "data", "name": "数据工程", "color": "sage",
     "desc": "Spark / Hive / ES / Kylin 数据链路，MySQL、Oracle、TiDB 与国产数据库，环境与部署。"},
    {"slug": "agent", "name": "Agent 开发", "color": "sky",
     "desc": "Ollama、Dify 本地大模型部署，NL2SQL 与工具调用，让 Agent 能查数、能干活。"},
    {"slug": "design", "name": "UI 设计", "color": "peach",
     "desc": "排版、配色与交互细节，把数据和 Agent 的能力做成清楚好用的界面。"},
]
CAT = {c["slug"]: c for c in CATEGORIES}

# 中文标签 → URL 友好的目录名；英文标签自动转小写
TAG_SLUGS = {"大模型": "llm", "离线部署": "offline"}

SKILLS = [
    ("大数据", "sage", ["Spark", "Hive", "Elasticsearch", "Kylin", "Azkaban"]),
    ("数据库", "ink", ["MySQL", "Oracle", "TiDB", "openGauss", "OceanBase", "GaussDB"]),
    ("Agent", "sky", ["Ollama", "Dify", "NL2SQL", "工具调用"]),
    ("UI 设计", "peach", ["界面设计", "交互设计", "设计系统"]),
    ("容器与运维", "butter", ["Docker", "Linux"]),
]

ICONS = {
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    "sun": '<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    "moon": '<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    "github": '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
    "rss": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1.5" fill="currentColor"/></svg>',
    "data": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5.5" rx="7" ry="2.5"/><path d="M5 5.5v13c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-13M5 12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5"/></svg>',
    "agent": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="6" r="2.5"/><circle cx="19" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M7.5 6h9M6.3 8.2l4.4 7.6M17.7 8.2l-4.4 7.6"/></svg>',
    "design": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.6 7.6"/><circle cx="11" cy="11" r="2"/></svg>',
}


def tag_slug(t):
    return TAG_SLUGS.get(t) or re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def parse_front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    meta, body = {}, text
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
            meta[k.strip()] = v
    return meta, body


def md_render(text):
    md = markdown.Markdown(
        extensions=["fenced_code", "codehilite", "tables", "toc", "sane_lists"],
        extension_configs={
            "codehilite": {"guess_lang": False, "css_class": "highlight"},
            "toc": {"toc_depth": "2-3", "permalink": "#", "permalink_title": "本节链接"},
        },
    )
    return md.convert(text), md.toc_tokens


def plain_text(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def reading_minutes(text):
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9_]+", text))
    return max(1, round((cjk / 400) + (words / 200)))


def e(s):
    return html.escape(str(s))


def layout(title, body, active="", desc=None, path="/"):
    full_title = f"{title} · {SITE['short']}" if title else SITE["title"]
    desc = desc or SITE["desc"]
    nav = [("/", "首页", "home"), ("/categories/", "分类", "cats"), ("/tags/", "标签", "tags"), ("/about/", "关于", "about")]
    nav_html = "".join('<a class="l%s" href="%s">%s</a>' % (" on" if k == active else "", u, n) for u, n, k in nav)
    year = datetime.date.today().year
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="{SITE['author']}">
<meta name="theme-color" content="#f2efe9" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0e1412" media="(prefers-color-scheme: dark)">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE['url']}{path}">
<meta property="og:image" content="{SITE['url']}/assets/avatar-512.png">
<link rel="canonical" href="{SITE['url']}{path}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="alternate" type="application/atom+xml" title="{SITE['title']}" href="/feed.xml">
<script>(function(){{try{{var t=localStorage.getItem('theme');if(!t)t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
<link rel="stylesheet" href="/assets/style.css?v={ASSET_V}">
<link rel="stylesheet" href="/assets/highlight.css?v={ASSET_V}">
</head>
<body>
<div class="blobs" aria-hidden="true"><i></i><i></i><i></i></div>
<nav class="nav glass" aria-label="主导航">
  <a class="me" href="/"><img src="/assets/avatar.svg" alt="" width="32" height="32"><span>{SITE['short']}</span></a>
  {nav_html}
  <span class="sep"></span>
  <button class="ib" id="search-btn" aria-label="搜索" title="搜索 (Ctrl+K 或 /)">{ICONS['search']}</button>
  <button class="ib" id="theme-btn" aria-label="切换深色模式" title="切换深色/浅色">{ICONS['sun']}{ICONS['moon']}</button>
</nav>
<main class="wrap main">
{body}
</main>
<footer class="wrap foot">
  <div class="glass">
    <span>© {year} {SITE['author']}</span>
    <span class="foot-links"><a href="{SITE['github']}">GitHub</a><a href="mailto:{SITE['email']}">{SITE['email']}</a><a href="/feed.xml">RSS</a></span>
  </div>
</footer>
<div class="search-modal" id="search-modal" hidden>
  <div class="search-backdrop" data-close></div>
  <div class="search-panel glass" role="dialog" aria-label="搜索文章">
    <div class="search-input-wrap">{ICONS['search']}<input id="search-input" type="search" placeholder="搜索文章标题、标签、正文…" autocomplete="off"><kbd data-close>Esc</kbd></div>
    <ul class="search-results" id="search-results"></ul>
  </div>
</div>
<script src="/assets/main.js?v={ASSET_V}"></script>
</body>
</html>
"""


def cat_pill(slug):
    c = CAT[slug]
    return f'<a class="cat-pill c-{c["color"]}" href="/categories/{slug}/">{c["name"]}</a>'


def tag_text(tags):
    return "".join(f'<a href="/tags/{tag_slug(t)}/">{e(t)}</a>' for t in tags)


def post_row(p):
    c = CAT[p["category"]]
    return f"""<article class="post-row c-{c['color']}">
  <a class="day" href="{p['url']}" aria-hidden="true" tabindex="-1"><b>{p['d'].day:02d}</b><span>{p['d'].month} 月</span></a>
  <div class="pr-body">
    <div class="pr-meta">{cat_pill(p['category'])}<span>{p['date']}</span><span>·</span><span>{p['minutes']} 分钟</span></div>
    <h3><a href="{p['url']}">{e(p['title'])}</a></h3>
    <p>{e(p['summary'])}</p>
    <div class="tags">{tag_text(p['tags'])}</div>
  </div>
  <a class="arrow" href="{p['url']}" aria-label="阅读：{e(p['title'])}">{ICONS['arrow']}</a>
</article>"""


def post_list(posts):
    return '<section class="glass posts">' + "".join(post_row(p) for p in posts) + "</section>"


def empty_state(cat):
    return f"""<section class="glass empty">
  <img src="/assets/avatar.svg" alt="" width="96" height="96">
  <h3>即将更新</h3>
  <p>「{cat['name']}」分类的文章正在整理中，敬请期待。</p>
  <a class="pill" href="/">回到首页</a>
</section>"""


def toc_html(tokens):
    def walk(ts):
        if not ts:
            return ""
        return "<ul>" + "".join(
            f'<li><a href="#{t["id"]}">{e(html.unescape(t["name"]))}</a>{walk(t["children"])}</li>' for t in ts
        ) + "</ul>"
    flat = []
    for t in tokens:
        flat.extend(t["children"] if t["level"] == 1 else [t])
    return walk(flat)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def clean_output():
    for name in ["posts", "tags", "about", "categories"]:
        shutil.rmtree(ROOT / name, ignore_errors=True)
    for name in ["index.html", "404.html", "search.json", "feed.xml", "sitemap.xml"]:
        (ROOT / name).unlink(missing_ok=True)


def role_tile(c, count, href=True):
    status = f"{count} 篇文章" if count else "即将更新"
    tag = "a" if href else "div"
    return f"""<{tag} class="tile glass t-role c-{c['color']}" href="/categories/{c['slug']}/">
  <span class="ri">{ICONS[c['slug']]}</span>
  <h3>{c['name']}</h3>
  <p>{c['desc']}</p>
  <span class="role-count{' soon' if not count else ''}">{status}</span>
</{tag}>"""


def skills_html():
    return "".join(
        f'<div class="grp"><h4><i class="dot-{color}"></i>{g}</h4><ul>' + "".join(f"<li>{s}</li>" for s in ss) + "</ul></div>"
        for g, color, ss in SKILLS
    )


def roles_line():
    colors = ["sage", "sky", "peach"]
    return '<p class="roles-line">' + "".join(f'<span class="c-{c}">{r}</span>' for r, c in zip(SITE["roles"], colors)) + "</p>"


def main():
    clean_output()
    posts = []
    for f in sorted((SRC / "posts").glob("*.md")):
        meta, body = parse_front_matter(f.read_text(encoding="utf-8"))
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f.stem)
        content, toc = md_render(body)
        d = datetime.date.fromisoformat(str(meta["date"]))
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        cat = meta.get("category", "data")
        assert cat in CAT, f"{f.name}: 未知分类 {cat}"
        posts.append({
            "slug": slug, "title": meta["title"], "d": d, "date": d.isoformat(),
            "date_cn": f"{d.year} 年 {d.month} 月 {d.day} 日", "tags": tags, "category": cat,
            "summary": meta.get("summary", ""), "source": meta.get("source"),
            "source_name": meta.get("source_name", meta.get("source")),
            "content": content, "toc": toc, "text": plain_text(content),
            "minutes": reading_minutes(body), "url": f"/posts/{slug}/",
        })
    posts.sort(key=lambda p: p["date"], reverse=True)

    tags = {}
    for p in posts:
        for t in p["tags"]:
            tags.setdefault(t, []).append(p)
    tag_list = sorted(tags.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    by_cat = {c["slug"]: [p for p in posts if p["category"] == c["slug"]] for c in CATEGORIES}

    def chips(active=None):
        out = f'<a class="chip{" on" if active is None else ""}" href="/tags/">全部<small>{len(posts)}</small></a>'
        out += "".join(
            f'<a class="chip{" on" if t == active else ""}" href="/tags/{tag_slug(t)}/">{e(t)}<small>{len(ps)}</small></a>'
            for t, ps in tag_list
        )
        return f'<div class="chips">{out}</div>'

    # ---------- 首页 ----------
    latest = posts[0]
    home = f"""<section class="bento">
  <div class="tile glass t-intro">
    <div class="intro-top">
      <img class="avatar" src="/assets/avatar.svg" alt="头像：小库库" width="104" height="104">
      <div><h1>{SITE['author']}</h1>{roles_line()}</div>
    </div>
    <div class="intro-stats">
      <div><b>{len(posts)}</b><span>篇文章</span></div>
      <div><b>{len(CATEGORIES)}</b><span>个分类</span></div>
      <div><b>{len(tags)}</b><span>个标签</span></div>
    </div>
    <div class="intro-actions">
      <a class="pill dark" href="#posts">读读文章</a>
      <button class="pill search-pill" type="button" data-open-search>{ICONS['search']}<span>搜索文章</span><kbd>Ctrl K</kbd></button>
      <a class="pill" href="{SITE['github']}">{ICONS['github']}GitHub</a>
    </div>
  </div>
  <a class="tile glass t-latest" href="{latest['url']}">
    <span class="badge">最新文章</span>
    <svg class="art" viewBox="0 0 190 150" fill="none" aria-hidden="true">
      <rect x="18" y="40" width="70" height="56" rx="12" fill="var(--sage-soft)" stroke="var(--sage)" stroke-width="2"/>
      <path d="M30 58h46M30 70h30M30 82h38" stroke="var(--sage)" stroke-width="3" stroke-linecap="round"/>
      <path d="M94 68h34" stroke="var(--peach)" stroke-width="3" stroke-linecap="round" stroke-dasharray="2 7"/>
      <path d="M124 60l10 8-10 8" stroke="var(--peach)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
      <ellipse cx="160" cy="44" rx="20" ry="7" fill="var(--sky-soft)" stroke="var(--sky)" stroke-width="2"/>
      <path d="M140 44v46c0 4 9 7 20 7s20-3 20-7V44" stroke="var(--sky)" stroke-width="2" fill="var(--sky-soft)"/>
      <path d="M140 66c0 4 9 7 20 7s20-3 20-7" stroke="var(--sky)" stroke-width="2"/>
    </svg>
    <div class="latest-cat">{CAT[latest['category']]['name']}</div>
    <h2>{e(latest['title'])}</h2>
    <p>{e(latest['summary'])}</p>
    <div class="meta"><span>{latest['d'].month} 月 {latest['d'].day} 日</span><span>·</span><span>{latest['minutes']} 分钟</span><span class="go">{ICONS['arrow']}</span></div>
  </a>
  {''.join(role_tile(c, len(by_cat[c['slug']])) for c in CATEGORIES)}
  <div class="tile glass t-stack">{skills_html()}</div>
  <div class="tile glass t-contact">
    <div class="eyebrow">联系我</div>
    <a href="mailto:{SITE['email']}"><span class="ic c-sky">{ICONS['mail']}</span>{SITE['email']}</a>
    <a href="{SITE['github']}"><span class="ic c-peach">{ICONS['github']}</span>github.com/Miss001</a>
    <a href="/feed.xml"><span class="ic c-sage">{ICONS['rss']}</span>RSS 订阅</a>
  </div>
</section>
<div class="sec-head" id="posts"><h2>全部文章</h2>{chips()}</div>
{post_list(posts)}"""
    write(ROOT / "index.html", layout("", home, "home"))

    # ---------- 文章页 ----------
    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        nav = '<nav class="post-nav">'
        nav += f'<a class="glass prev" href="{older["url"]}"><small>上一篇</small>{e(older["title"])}</a>' if older else "<span></span>"
        nav += f'<a class="glass next" href="{newer["url"]}"><small>下一篇</small>{e(newer["title"])}</a>' if newer else "<span></span>"
        nav += "</nav>"
        src = ""
        if p["source"]:
            src = f'<div class="source-note">本文整理自我的公开笔记仓库 <a href="{e(p["source"])}">{e(p["source_name"])}</a>，排版有调整，技术内容保持原样。</div>'
        body = f"""<div class="post-layout">
<article class="post">
  <header class="glass post-header c-{CAT[p['category']]['color']}">
    <div class="pr-meta">{cat_pill(p['category'])}<span>{p['date_cn']}</span><span>·</span><span>{p['minutes']} 分钟阅读</span></div>
    <h1>{e(p['title'])}</h1>
    <p class="post-summary">{e(p['summary'])}</p>
    <div class="post-author"><img src="/assets/avatar.svg" alt="" width="28" height="28"><span>{SITE['author']}</span><span class="tags">{tag_text(p['tags'])}</span></div>
  </header>
  <div class="glass prose">
{p['content']}
    {src}
  </div>
  {nav}
</article>
<aside class="toc"><div class="toc-inner glass"><h3>目录</h3>{toc_html(p['toc'])}</div></aside>
</div>"""
        write(ROOT / "posts" / p["slug"] / "index.html", layout(p["title"], body, "", p["summary"], p["url"]))

    # ---------- 分类 ----------
    cat_index = '<header class="page-head"><h1>分类</h1><p>按三个方向整理：数据工程、Agent 开发、UI 设计。</p></header>'
    cat_index += '<section class="bento cats">' + "".join(role_tile(c, len(by_cat[c["slug"]])) for c in CATEGORIES) + "</section>"
    for c in CATEGORIES:
        ps = by_cat[c["slug"]]
        cat_index += f'<div class="sec-head"><h2><span class="ri sm c-{c["color"]}">{ICONS[c["slug"]]}</span>{c["name"]}</h2><a class="more" href="/categories/{c["slug"]}/">查看分类 →</a></div>'
        cat_index += post_list(ps) if ps else empty_state(c)
    write(ROOT / "categories" / "index.html", layout("分类", cat_index, "cats", path="/categories/"))
    for c in CATEGORIES:
        ps = by_cat[c["slug"]]
        b = f"""<header class="glass cat-hero c-{c['color']}">
  <span class="ri lg">{ICONS[c['slug']]}</span>
  <div><p class="crumb"><a href="/categories/">分类</a> / </p><h1>{c['name']}</h1><p>{c['desc']}</p></div>
  <span class="role-count{' soon' if not ps else ''}">{f'{len(ps)} 篇文章' if ps else '即将更新'}</span>
</header>"""
        b += post_list(ps) if ps else empty_state(c)
        write(ROOT / "categories" / c["slug"] / "index.html", layout(c["name"], b, "cats", c["desc"], f"/categories/{c['slug']}/"))

    # ---------- 标签 ----------
    tag_index = f'<header class="page-head"><h1>标签</h1><p>共 {len(tags)} 个标签，{len(posts)} 篇文章。</p></header>{chips()}'
    tag_index += '<section class="tag-groups">'
    for t, ps in tag_list:
        tag_index += f'<div class="glass tag-group" id="{tag_slug(t)}"><h2><a href="/tags/{tag_slug(t)}/"># {e(t)}</a><small>{len(ps)}</small></h2><ul>'
        tag_index += "".join(f'<li><time>{q["date"]}</time><a href="{q["url"]}">{e(q["title"])}</a></li>' for q in ps)
        tag_index += "</ul></div>"
    tag_index += "</section>"
    write(ROOT / "tags" / "index.html", layout("标签", tag_index, "tags", path="/tags/"))
    for t, ps in tag_list:
        b = f'<header class="page-head"><p class="crumb"><a href="/tags/">标签</a> / </p><h1># {e(t)}</h1><p>共 {len(ps)} 篇文章</p></header>{chips(t)}'
        b += post_list(ps)
        write(ROOT / "tags" / tag_slug(t) / "index.html", layout(f"#{t}", b, "tags", path=f"/tags/{tag_slug(t)}/"))

    # ---------- 关于 ----------
    about_md, _ = md_render((SRC / "about.md").read_text(encoding="utf-8"))
    about = f"""<section class="glass about-hero">
  <img class="avatar" src="/assets/avatar.svg" alt="头像：小库库" width="132" height="132">
  <div><h1>{SITE['author']}</h1>{roles_line()}
    <div class="intro-actions"><a class="pill dark" href="mailto:{SITE['email']}">{ICONS['mail']}{SITE['email']}</a><a class="pill" href="{SITE['github']}">{ICONS['github']}GitHub</a></div>
  </div>
</section>
<section class="glass prose about-prose">{about_md}</section>
<div class="sec-head"><h2>三个方向</h2></div>
<section class="bento cats">{''.join(role_tile(c, len(by_cat[c['slug']])) for c in CATEGORIES)}</section>
<div class="sec-head"><h2>技术栈</h2></div>
<section class="tile glass t-stack">{skills_html()}</section>"""
    write(ROOT / "about" / "index.html", layout("关于", about, "about", path="/about/"))

    # ---------- 404 ----------
    write(ROOT / "404.html", layout("页面不存在", """<section class="glass empty notfound">
  <img src="/assets/avatar.svg" alt="" width="120" height="120">
  <h1>404</h1><p>这个页面不存在，可能已经搬家了。</p>
  <div class="intro-actions"><a class="pill dark" href="/">回到首页</a><button class="pill" type="button" data-open-search>搜索文章</button></div>
</section>"""))

    # ---------- 搜索索引 / RSS / sitemap ----------
    idx = [{"title": p["title"], "url": p["url"], "date": p["date"], "tags": p["tags"] + [CAT[p["category"]]["name"]],
            "summary": p["summary"], "text": p["text"][:6000]} for p in posts]
    write(ROOT / "search.json", json.dumps(idx, ensure_ascii=False))
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = "".join(f"""
  <entry>
    <title>{xml_escape(p['title'])}</title>
    <link href="{SITE['url']}{p['url']}"/>
    <id>{SITE['url']}{p['url']}</id>
    <updated>{p['date']}T00:00:00+08:00</updated>
    <category term="{xml_escape(CAT[p['category']]['name'])}"/>
    <summary>{xml_escape(p['summary'])}</summary>
  </entry>""" for p in posts)
    write(ROOT / "feed.xml", f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{SITE['title']}</title>
  <subtitle>{xml_escape(SITE['desc'])}</subtitle>
  <link href="{SITE['url']}/"/>
  <link rel="self" href="{SITE['url']}/feed.xml"/>
  <id>{SITE['url']}/</id>
  <updated>{now}</updated>
  <author><name>{SITE['author']}</name></author>{entries}
</feed>
""")
    urls = ["/", "/categories/", "/tags/", "/about/"] + [p["url"] for p in posts] \
        + [f"/categories/{c['slug']}/" for c in CATEGORIES] + [f"/tags/{tag_slug(t)}/" for t in tags]
    write(ROOT / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{SITE['url']}{u}</loc></url>" for u in urls) + "</urlset>\n")

    light = HtmlFormatter(style="friendly").get_style_defs('[data-theme="light"] .highlight')
    dark = HtmlFormatter(style="github-dark").get_style_defs('[data-theme="dark"] .highlight')
    write(ROOT / "assets" / "highlight.css", light + "\n" + dark + "\n")
    (ROOT / ".nojekyll").touch()
    print(f"built {len(posts)} posts, {len(tags)} tags, {len(CATEGORIES)} categories")


if __name__ == "__main__":
    main()
