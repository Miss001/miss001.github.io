# Miss001.github.io

宇宙超级无敌美少女的个人技术博客：数据工程师 / Agent 开发 / UI 设计

线上地址：<https://miss001.github.io>

## 特性

- 简体中文界面，柔和现代的 Bento 拼贴 + 毛玻璃风格，桌面 / 手机自适应
- 三个分类：数据工程 / Agent 开发 / UI 设计（`/categories/`），空分类显示「即将更新」
- 首页、文章页、分类页、标签页、关于页、404 页
- 站内搜索（导航栏放大镜、首页「搜索文章」按钮，或按 `Ctrl+K` / `/`），纯前端实现，不依赖第三方服务
- 深色 / 浅色模式切换（默认跟随系统，选择会被记住）
- 代码高亮、一键复制代码、文章目录（桌面端）、RSS（`/feed.xml`）、`sitemap.xml`

## 目录结构

```
_src/posts/       手写文章（Markdown），文件名格式：YYYY-MM-DD-英文短名.md
_src/notes/       由 import_notes.py 从笔记仓库自动生成（已在 .gitignore 里，不要手改）
_src/note_dates.json  笔记的发布日期覆盖表（笔记路径 → 日期），没写的用笔记仓库里的首次提交日期
import_notes.py   导入器：把 Miss001/data-engineering-notes 的每篇笔记转成一篇文章
.github/workflows/deploy.yml  GitHub Actions：导入笔记 + 构建 + 发布到 Pages
_src/about.md     关于页的自我介绍
assets/           样式、脚本、头像与图标（avatar.svg / favicon.svg / favicon-32.png / apple-touch-icon.png）
                  构建时只会重新生成 highlight.css
build.py          生成器：把 Markdown 渲染成静态 HTML
index.html、posts/、categories/、tags/、about/、search.json、feed.xml ……   ← 构建产物，需要一起提交
.nojekyll         告诉 GitHub Pages 不要再用 Jekyll 处理，直接按静态文件发布
```

这是一个「生成好的静态站」。仓库里仍然提交了一份构建好的 HTML，所以 Pages 源设为「Deploy from a branch」时也能正常显示；
切换到 GitHub Actions 发布后，笔记仓库一更新，博客就会自动跟着更新（见下文）。

## 发布到 GitHub Pages

1. 在 GitHub 上新建仓库，名字必须是 `Miss001.github.io`，选 **Public**，不要勾选 README / .gitignore / license。
2. 在本目录执行（本地已经初始化好 git，并有一次初始提交）：

   ```bash
   git remote add origin https://github.com/Miss001/Miss001.github.io.git
   git push -u origin main
   ```

3. 打开仓库的 **Settings → Pages**：
   - Source（Build and deployment）选 **Deploy from a branch**
   - Branch 选 **main**，目录选 **/ (root)**，点 Save
4. 等一两分钟，访问 <https://miss001.github.io> 即可。之后每次 push 到 main 都会自动更新。

## 笔记自动同步（GitHub Actions）

笔记仓库 [Miss001/data-engineering-notes](https://github.com/Miss001/data-engineering-notes) 里的每篇 Markdown 笔记都会变成一篇博客文章：

- 分类：`ai/` → Agent 开发，`design/` → UI 设计，其余（database / bigdata / ops / dev）→ 数据工程
- 标签：领域（数据库 / 大数据 / 运维 / 开发）+ 产品（MySQL、openGauss、Spark……，按目录名映射）
- 标题：「产品 + 子目录：文件名」，如「MySQL 复制：主从切换」；英文文件名在 `import_notes.py` 的 `LABELS` 里有中文名
- 网址：由笔记路径转拼音生成，路径不变网址就不变
- 跳过：所有 `README.md`、空文件，以及已经有手写文章的几篇（`SKIP` 列表）
- 只有脚本 / SQL 的目录（sql-helper、HDFS 小文件合并等）合成一篇代码合集
- 笔记开头也可以写 front matter（title / date / summary），会优先使用

**一次性设置**：仓库 **Settings → Pages → Build and deployment → Source** 改成 **GitHub Actions**。
之后以下情况都会自动导入笔记、构建并发布：

- push 到博客仓库的 main 分支
- 每小时第 17 分钟定时运行一次（笔记仓库有改动就会出现在博客上，最多延迟约一小时）
- 在 Actions 页面手动点 **Run workflow**

本地完整构建：

```bash
pip install markdown pygments pypinyin
git clone https://github.com/Miss001/data-engineering-notes _notes   # 已 clone 过就 git -C _notes pull
python3 import_notes.py --notes _notes
python3 build.py
python3 -m http.server 8000
```

> 笔记仓库是公开的，导入器不会再做脱敏：往笔记里加内容前请先确认没有密码、内网 IP、密钥。

## 写新文章

1. 在 `_src/posts/` 下新建 `2026-10-20-my-post.md`，开头写上：

   ```markdown
   ---
   title: 文章标题
   date: 2026-10-20
   category: data          # data=数据工程 / agent=Agent 开发 / design=UI 设计
   tags: [Spark, 大数据]
   summary: 一两句话的摘要，会显示在首页和搜索结果里。
   source: https://github.com/Miss001/xxx      # 可选，整理自哪个笔记仓库
   source_name: Miss001/xxx                    # 可选
   ---

   正文从二级标题 `##` 开始写……
   ```

2. 重新生成并本地预览：

   ```bash
   pip install markdown pygments pypinyin      # 只需第一次
   python3 import_notes.py --notes _notes      # 想一起预览笔记文章时
   python3 build.py
   python3 -m http.server 8000        # 浏览器打开 http://localhost:8000
   ```

3. 确认没问题后提交并推送：

   ```bash
   git add -A
   git commit -m "新文章：文章标题"
   git push
   ```

> 分类名称、简介和技术栈在 `build.py` 顶部的 `CATEGORIES`、`SKILLS` 里修改。
> 中文标签会映射成英文网址，映射表在 `build.py` 的 `TAG_SLUGS` 里，新增中文标签时记得加一行。
> 发布前请确认文章里没有密码、内网 IP、真实业务数据等敏感信息。

## 首批文章来源

首批 4 篇手写文章整理自以下公开笔记仓库，排版有调整，技术内容保持原样：

- [Miss001/ai](https://github.com/Miss001/ai)：Ollama 离线安装、Ollama 导入 GGUF 模型、Dify 部署
- [Miss001/docker](https://github.com/Miss001/docker)：CentOS 7.9 安装 Docker
- [Miss001/python](https://github.com/Miss001/python)：Conda 环境离线安装与迁移
