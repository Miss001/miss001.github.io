#!/usr/bin/env python3
"""极简静态博客生成器：把 _src/posts/*.md 渲染成静态 HTML，输出到仓库根目录。

用法：
    pip install markdown pygments
    python3 build.py
"""
import html, json, re, shutil, datetime
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
    "motto": "从未抵达，一直在路上",
    "desc": "数据工程师的技术笔记：大数据、数据库、容器与本地大模型部署。",
    "url": "https://miss001.github.io",
    "github": "https://github.com/Miss001",
    "email": "522160919@qq.com",
}

# 中文标签 → URL 友好的目录名；英文标签自动转小写
TAG_SLUGS = {"大模型": "llm", "离线部署": "offline"}

SKILLS = [
    ("大数据", ["Spark", "Hive", "Elasticsearch", "Kylin", "Azkaban"]),
    ("数据库", ["MySQL", "Oracle", "TiDB"]),
    ("国产数据库", ["openGauss", "OceanBase", "GaussDB"]),
    ("容器与运维", ["Docker", "Linux"]),
    ("AI / 大模型", ["Ollama", "Dify", "NL2SQL"]),
]


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
    out = md.convert(text)
    return out, md.toc_tokens


def plain_text(h):
    t = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def reading_minutes(text):
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9_]+", text))
    return max(1, round((cjk / 400) + (words / 200)))


ICON_SUN = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
ICON_MOON = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
ICON_SEARCH = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
ICON_GH = '<svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>'
ICON_MAIL = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>'


def layout(title, body, active="", desc=None, path="/"):
    full_title = f"{title} · {SITE['short']}" if title else SITE["title"]
    desc = desc or SITE["desc"]
    nav = [("/", "首页", "home"), ("/tags/", "标签", "tags"), ("/about/", "关于", "about")]
    nav_html = "".join(
        '<a href="%s"%s>%s</a>' % (u, ' class="active"' if k == active else "", n) for u, n, k in nav
    )
    year = datetime.date.today().year
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="author" content="{SITE['author']}">
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{SITE['url']}{path}">
<link rel="canonical" href="{SITE['url']}{path}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/atom+xml" title="{SITE['title']}" href="/feed.xml">
<script>(function(){{try{{var t=localStorage.getItem('theme');if(!t)t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
<link rel="stylesheet" href="/assets/style.css">
<link rel="stylesheet" href="/assets/highlight.css">
</head>
<body>
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="/"><span class="logo">M</span><span class="brand-text">{SITE['short']}<small>的技术笔记</small></span></a>
    <nav class="nav">{nav_html}</nav>
    <div class="actions">
      <button class="icon-btn" id="search-btn" aria-label="搜索" title="搜索 (Ctrl+K)">{ICON_SEARCH}</button>
      <button class="icon-btn" id="theme-btn" aria-label="切换深色模式" title="切换深色/浅色"><span class="i-sun">{ICON_SUN}</span><span class="i-moon">{ICON_MOON}</span></button>
    </div>
  </div>
</header>
<main class="container main">
{body}
</main>
<footer class="site-footer">
  <div class="container">
    <p class="motto">「{SITE['motto']}」</p>
    <p>© {year} {SITE['author']} · <a href="{SITE['github']}">GitHub</a> · <a href="mailto:{SITE['email']}">{SITE['email']}</a> · <a href="/feed.xml">RSS</a></p>
  </div>
</footer>
<div class="search-modal" id="search-modal" hidden>
  <div class="search-backdrop" data-close></div>
  <div class="search-panel" role="dialog" aria-label="搜索文章">
    <div class="search-input-wrap">{ICON_SEARCH}<input id="search-input" type="search" placeholder="搜索文章标题、标签、正文…" autocomplete="off"><kbd data-close>Esc</kbd></div>
    <ul class="search-results" id="search-results"></ul>
  </div>
</div>
<script src="/assets/main.js"></script>
</body>
</html>
"""


def tag_chips(tags):
    return "".join(f'<a class="tag" href="/tags/{tag_slug(t)}/">#{html.escape(t)}</a>' for t in tags)


def post_card(p):
    return f"""<article class="post-card">
  <div class="post-meta"><time datetime="{p['date']}">{p['date_cn']}</time><span>·</span><span>{p['minutes']} 分钟阅读</span></div>
  <h2><a href="{p['url']}">{html.escape(p['title'])}</a></h2>
  <p class="summary">{html.escape(p['summary'])}</p>
  <div class="tags">{tag_chips(p['tags'])}</div>
</article>"""


def toc_html(tokens):
    def walk(ts):
        if not ts:
            return ""
        items = "".join(
            f'<li><a href="#{t["id"]}">{html.escape(html.unescape(t["name"]))}</a>{walk(t["children"])}</li>' for t in ts
        )
        return f"<ul>{items}</ul>"
    flat = []
    for t in tokens:  # 文章正文从 h2 开始
        flat.extend(t["children"] if t["level"] == 1 else [t])
    return walk(flat)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def clean_output():
    for name in ["posts", "tags", "about"]:
        shutil.rmtree(ROOT / name, ignore_errors=True)
    for name in ["index.html", "404.html", "search.json", "feed.xml", "sitemap.xml"]:
        (ROOT / name).unlink(missing_ok=True)


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
        posts.append({
            "slug": slug, "title": meta["title"], "date": d.isoformat(),
            "date_cn": f"{d.year} 年 {d.month} 月 {d.day} 日", "tags": tags,
            "summary": meta.get("summary", ""), "source": meta.get("source"),
            "source_name": meta.get("source_name", meta.get("source")),
            "content": content, "toc": toc, "text": plain_text(content),
            "minutes": reading_minutes(body), "url": f"/posts/{slug}/",
        })
    posts.sort(key=lambda p: p["date"], reverse=True)

    # 标签统计
    tags = {}
    for p in posts:
        for t in p["tags"]:
            tags.setdefault(t, []).append(p)
    tag_list = sorted(tags.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    tag_cloud = "".join(
        f'<a class="tag" href="/tags/{tag_slug(t)}/">#{html.escape(t)}<span class="count">{len(ps)}</span></a>' for t, ps in tag_list
    )

    # 首页
    skills_flat = "".join(f'<span class="chip">{s}</span>' for _, ss in SKILLS for s in ss)
    home = f"""<section class="hero">
  <div class="avatar" aria-hidden="true">美</div>
  <div>
    <p class="hello">你好，我是</p>
    <h1>{SITE['author']}</h1>
    <p class="role">数据工程师 · 大数据 / 数据库 / 本地大模型</p>
    <p class="motto-big">「{SITE['motto']}」</p>
    <div class="hero-links">
      <a class="btn" href="/about/">关于我</a>
      <a class="btn ghost" href="{SITE['github']}">{ICON_GH} GitHub</a>
      <a class="btn ghost" href="mailto:{SITE['email']}">{ICON_MAIL} 邮箱</a>
    </div>
  </div>
</section>
<div class="chips hero-chips">{skills_flat}</div>
<div class="layout-2">
  <section class="post-list">
    <h2 class="section-title">最新文章 <span class="muted">共 {len(posts)} 篇</span></h2>
    {''.join(post_card(p) for p in posts)}
  </section>
  <aside class="sidebar">
    <div class="card">
      <h3>搜索</h3>
      <button class="fake-search" data-open-search>{ICON_SEARCH}<span>搜索文章…</span><kbd>Ctrl K</kbd></button>
    </div>
    <div class="card">
      <h3>标签</h3>
      <div class="tags">{tag_cloud}</div>
    </div>
  </aside>
</div>"""
    write(ROOT / "index.html", layout("", home, "home"))

    # 文章页
    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        nav = '<nav class="post-nav">'
        nav += f'<a class="prev" href="{older["url"]}"><small>上一篇</small>{html.escape(older["title"])}</a>' if older else "<span></span>"
        nav += f'<a class="next" href="{newer["url"]}"><small>下一篇</small>{html.escape(newer["title"])}</a>' if newer else "<span></span>"
        nav += "</nav>"
        src = ""
        if p["source"]:
            src = f'<div class="source-note">📒 本文整理自我的公开笔记仓库 <a href="{html.escape(p["source"])}">{html.escape(p["source_name"])}</a>，排版有调整，技术内容保持原样。</div>'
        toc = toc_html(p["toc"])
        body = f"""<div class="post-layout">
<article class="post">
  <header class="post-header">
    <div class="tags">{tag_chips(p['tags'])}</div>
    <h1>{html.escape(p['title'])}</h1>
    <div class="post-meta"><time datetime="{p['date']}">{p['date_cn']}</time><span>·</span><span>{p['minutes']} 分钟阅读</span><span>·</span><span>{SITE['author']}</span></div>
  </header>
  <div class="prose">
{p['content']}
  </div>
  {src}
  {nav}
</article>
<aside class="toc"><div class="toc-inner"><h3>目录</h3>{toc}</div></aside>
</div>"""
        write(ROOT / "posts" / p["slug"] / "index.html", layout(p["title"], body, "", p["summary"], p["url"]))

    # 标签页
    tag_index = f"""<h1 class="page-title">标签</h1>
<p class="muted">共 {len(tags)} 个标签</p>
<div class="tags big">{tag_cloud}</div>"""
    for t, ps in tag_list:
        tag_index += f'<section class="tag-group" id="{tag_slug(t)}"><h2><a href="/tags/{tag_slug(t)}/">#{html.escape(t)}</a> <span class="muted">{len(ps)}</span></h2><ul class="simple-list">'
        tag_index += "".join(f'<li><time>{q["date"]}</time><a href="{q["url"]}">{html.escape(q["title"])}</a></li>' for q in ps)
        tag_index += "</ul></section>"
    write(ROOT / "tags" / "index.html", layout("标签", tag_index, "tags", path="/tags/"))
    for t, ps in tag_list:
        b = f'<p class="crumb"><a href="/tags/">全部标签</a> / </p><h1 class="page-title">#{html.escape(t)}</h1><p class="muted">共 {len(ps)} 篇文章</p>'
        b += f'<section class="post-list">{"".join(post_card(q) for q in ps)}</section>'
        write(ROOT / "tags" / tag_slug(t) / "index.html", layout(f"#{t}", b, "tags", path=f"/tags/{tag_slug(t)}/"))

    # 关于页
    about_md, _ = md_render((SRC / "about.md").read_text(encoding="utf-8"))
    skills_html = "".join(
        f'<div class="skill-row"><h3>{g}</h3><div class="chips">' + "".join('<span class="chip">%s</span>' % s for s in ss) + '</div></div>'
        for g, ss in SKILLS
    )
    about = f"""<section class="about">
  <div class="about-head">
    <div class="avatar" aria-hidden="true">美</div>
    <div><h1>{SITE['author']}</h1><p class="role">数据工程师</p></div>
  </div>
  <div class="prose">{about_md}</div>
  <h2 class="section-title">技术栈</h2>
  <div class="skills card">{skills_html}</div>
  <h2 class="section-title">联系我</h2>
  <div class="contact card">
    <a href="mailto:{SITE['email']}">{ICON_MAIL}<span>{SITE['email']}</span></a>
    <a href="{SITE['github']}">{ICON_GH}<span>github.com/Miss001</span></a>
  </div>
</section>"""
    write(ROOT / "about" / "index.html", layout("关于", about, "about", path="/about/"))

    # 404
    write(ROOT / "404.html", layout("页面不存在", '<div class="notfound"><h1>404</h1><p>这个页面还在路上……</p><a class="btn" href="/">回到首页</a></div>'))

    # 搜索索引
    idx = [{"title": p["title"], "url": p["url"], "date": p["date"], "tags": p["tags"],
            "summary": p["summary"], "text": p["text"][:6000]} for p in posts]
    write(ROOT / "search.json", json.dumps(idx, ensure_ascii=False))

    # RSS (Atom)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = "".join(f"""
  <entry>
    <title>{xml_escape(p['title'])}</title>
    <link href="{SITE['url']}{p['url']}"/>
    <id>{SITE['url']}{p['url']}</id>
    <updated>{p['date']}T00:00:00+08:00</updated>
    <summary>{xml_escape(p['summary'])}</summary>
  </entry>""" for p in posts)
    write(ROOT / "feed.xml", f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{SITE['title']}</title>
  <link href="{SITE['url']}/"/>
  <id>{SITE['url']}/</id>
  <updated>{now}</updated>
  <author><name>{SITE['author']}</name></author>{entries}
</feed>
""")
    urls = ["/", "/tags/", "/about/"] + [p["url"] for p in posts] + [f"/tags/{tag_slug(t)}/" for t in tags]
    write(ROOT / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{SITE['url']}{u}</loc></url>" for u in urls) + "</urlset>\n")

    # 代码高亮样式（浅色 + 深色）
    light = HtmlFormatter(style="friendly").get_style_defs('[data-theme="light"] .highlight')
    dark = HtmlFormatter(style="github-dark").get_style_defs('[data-theme="dark"] .highlight')
    write(ROOT / "assets" / "highlight.css", light + "\n" + dark + "\n")
    (ROOT / ".nojekyll").touch()
    print(f"built {len(posts)} posts, {len(tags)} tags")


if __name__ == "__main__":
    main()
