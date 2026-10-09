---
title: CentOS 7.9 安装 Docker 并用 Docker Compose 部署 Dify
date: 2026-10-08
category: agent
tags: [Docker, Dify, CentOS, 大模型]
summary: CentOS 7 停止维护后官方源不好用了：换成阿里云的 yum 源和 docker-ce 源，安装指定版本 Docker；再拉取 Dify 源码，一条 docker compose 命令启动 Dify。
source: https://github.com/Miss001/docker/blob/main/部署/deploy-centos7.9.md
source_name: Miss001/docker · 部署/deploy-centos7.9.md，Miss001/ai · dify/部署说明.md
---

CentOS 7 已经停止维护，默认的 yum 源基本不可用。这篇先把 yum 源和 docker-ce 源换成阿里云镜像，装好 Docker，再在上面部署 [Dify](https://github.com/langgenius/dify)。Dify 可以接入[上一篇](/posts/ollama-qwen25-gguf/)用 Ollama 部署的本地模型。

## 一、安装 Docker

### 1. 安装 yum-utils

```bash
sudo yum install -y yum-utils
```

### 2. 配置 docker-ce.repo

```bash
sudo wget -O /etc/yum.repos.d/docker-ce.repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
```

### 3. 配置 CentOS-Base.repo

`vi /etc/yum.repos.d/CentOS-Base.repo`，替换为阿里云镜像：

```ini
# CentOS-Base.repo
#
# The mirror system uses the connecting IP address of the client and the
# update status of each mirror to pick mirrors that are updated to and
# geographically close to the client.  You should use this for CentOS updates
# unless you are manually picking other mirrors.
#
# If the mirrorlist= does not work for you, as a fall back you can try the
# remarked out baseurl= line instead.

[base]
name=CentOS-$releasever - Base - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/os/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/os/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/os/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

#released updates
[updates]
name=CentOS-$releasever - Updates - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/updates/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/updates/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/updates/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/extras/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/extras/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/extras/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/centosplus/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/centosplus/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/centosplus/$basearch/
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

#contrib - packages by Centos Users
[contrib]
name=CentOS-$releasever - Contrib - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/contrib/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/contrib/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/contrib/$basearch/
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
```

更新 yum 缓存：

```bash
yum clean all
yum makecache
```

### 4. 查看可安装的版本

```bash
yum list docker-ce --showduplicates | sort -r
```

### 5. 安装指定版本的 Docker

```bash
sudo yum -y install docker-ce-20.10.0 docker-ce-cli-20.10.0 containerd.io
# 安装最新版（含 buildx 和 compose 插件）：
# sudo yum -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

> 后面部署 Dify 要用 `docker compose` 命令，需要装上 `docker-compose-plugin`。

### 6. 启动 Docker

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

## 二、部署 Dify

### 1. 下载源码

```bash
git clone https://github.com/langgenius/dify.git
```

### 2. 替换镜像源

国内拉取 Docker Hub 镜像经常失败，可以把 `docker/docker-compose.yaml` 里的镜像地址替换成国内镜像。镜像地址可以在这里查：

<https://docker.aityp.com/>

### 3. 启动

```bash
cd dify
cd docker
cp .env.example .env
docker compose up -d
```

启动后用浏览器访问服务器地址，按提示初始化管理员账号。之后在「设置 → 模型供应商」里添加 Ollama，就能用上本地模型了。
