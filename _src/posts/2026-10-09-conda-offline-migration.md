---
title: Conda 环境离线安装与迁移：conda-pack 打包到内网服务器
date: 2026-10-09
category: data
tags: [Python, Conda, 离线部署]
summary: 内网服务器装不了包？在有网的机器上建好 conda 环境，用 conda-pack 打成压缩包拷过去解压即用；也可以只下载离线包，用 --offline / --no-index 安装。
source: https://github.com/Miss001/python
source_name: Miss001/python · 创建新环境-迁移.md、环境配置.md
---

数据开发经常要在内网服务器上跑 Python 脚本，但服务器没法 `pip install`。思路很简单：**在有网的机器上把环境准备好，再整体搬过去**。

Conda 本身的安装可以参考：<https://www.cnblogs.com/distance66/p/17772974.html>

## 一、创建新环境

创建基础环境：

```bash
conda create -n myenv python=3.10 pip
```

激活环境后安装依赖：

```bash
pip install 包名
```

## 二、打包环境（有网机器）

安装 `conda-pack`，导出环境描述并打包：

```bash
conda install -c conda-forge conda-pack

conda env export --name myenv > environment.yml
conda-pack --name myenv --output myenv.tar.gz
```

## 三、目标环境导入（内网机器）

把 `myenv.tar.gz` 拷到目标机器，解压到 conda 的 `envs` 目录下：

```bash
mkdir -p myenv
tar -xzf myenv.tar.gz -C myenv
mv myenv ${CONDA_HOME}/envs/
conda info --envs

conda activate myenv
```

也可以基于导出的 `environment.yml` 创建：

```bash
conda env create -f environment.yml
conda activate myenv
conda list
```

## 四、其他离线安装方式

### 离线安装虚拟环境

先在有网机器上只下载、不安装：

```bash
conda install --download-only --copy -p ./conda_packages python=3.8
```

再在目标机器上离线创建：

```bash
conda create -n myenv
conda install --use-local --offline -n myenv python=3.8
conda activate myenv
```

### 离线安装 pip 包

导出依赖清单并下载所有包：

```bash
pip list --format=freeze > requirements.txt
pip download -r requirements.txt -d pkgs
```

在目标机器上从本地目录安装：

```bash
pip install --no-index --find-links=pkgs -r requirements.txt
```

### 单独下载 conda 包

```bash
# 下载离线包（下载到 miniconda3/pkgs 目录）
conda install --download-only package_name
# 离线安装
conda install --offline /path/to/package_name.tar.bz2
```

> 小提示：conda-pack 打包的环境要求源机器和目标机器的操作系统、CPU 架构一致。
