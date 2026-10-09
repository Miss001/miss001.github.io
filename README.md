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
_src/posts/       文章源文件（Markdown），文件名格式：YYYY-MM-DD-英文短名.md
_src/about.md     关于页的自我介绍
assets/           样式、脚本、头像与图标（avatar.svg / favicon.svg / favicon-32.png / apple-touch-icon.png）
                  构建时只会重新生成 highlight.css
build.py          生成器：把 Markdown 渲染成静态 HTML
index.html、posts/、categories/、tags/、about/、search.json、feed.xml ……   ← 构建产物，需要一起提交
.nojekyll         告诉 GitHub Pages 不要再用 Jekyll 处理，直接按静态文件发布
```

这是一个「生成好的静态站」：GitHub Pages 直接托管仓库里的 HTML 文件，**不需要 Jekyll，也不需要 GitHub Actions**。

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
   pip install markdown pygments      # 只需第一次
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

首批 4 篇文章整理自以下公开笔记仓库，排版有调整，技术内容保持原样：

- [Miss001/ai](https://github.com/Miss001/ai)：Ollama 离线安装、Ollama 导入 GGUF 模型、Dify 部署
- [Miss001/docker](https://github.com/Miss001/docker)：CentOS 7.9 安装 Docker
- [Miss001/python](https://github.com/Miss001/python)：Conda 环境离线安装与迁移
