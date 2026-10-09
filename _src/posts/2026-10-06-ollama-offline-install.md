---
title: Ollama 离线安装：systemd 服务与 Docker 两种方式
date: 2026-10-06
category: agent
tags: [Ollama, 大模型, 离线部署, Docker]
summary: 在无法直连外网的 Linux 服务器上安装 Ollama：改写官方 install.sh 走本地安装包、配置 systemd 开机自启，或者直接用 Docker 一条命令跑起来。
source: https://github.com/Miss001/ai/tree/main/ollama
source_name: Miss001/ai · ollama
---

内网服务器经常无法直接访问 `ollama.com`，官方一键脚本会卡在下载这一步。本文记录两种安装方式：**改写安装脚本离线安装（systemd 托管）**，以及 **Docker 部署**。

## 方式一：离线安装 + systemd

### 1. 下载安装包

到 GitHub Releases 页面下载对应架构的安装包（如 `ollama-linux-amd64.tgz`），上传到服务器：

<https://github.com/ollama/ollama/releases>

### 2. 下载安装脚本

```bash
wget https://ollama.com/install.sh
```

### 3. 修改安装脚本

用 `vi install.sh` 打开脚本，找到在线下载并解压的这段：

```bash
curl --fail --show-error --location --progress-bar \
            "https://ollama.com/download/ollama-linux-${ARCH}.tgz${VER_PARAM}" | \
            $SUDO tar -xzf - -C "$OLLAMA_INSTALL_DIR"
```

改为直接解压本地安装包（脚本里其他 `curl` 下载的地方也按同样思路修改）：

```bash
$SUDO tar -xzf ollama-linux-${ARCH}.tgz -C "$OLLAMA_INSTALL_DIR"
```

### 4. 执行安装

```bash
bash install.sh
```

### 5. 创建用户并授权

```bash
sudo useradd -r -s /bin/false -U -m -d /usr/share/ollama ollama
sudo usermod -a -G ollama $(whoami)
```

### 6. 创建 systemd 配置文件

`vi /etc/systemd/system/ollama.service`：

```ini
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin"

[Install]
WantedBy=default.target
```

> `OLLAMA_HOST=0.0.0.0:11434` 让服务监听所有网卡，其他机器（比如 Dify）才能访问到。

### 7. 启动服务

```bash
# 加载配置
sudo systemctl daemon-reload
# 设置开机启动
sudo systemctl enable ollama
# 启动 ollama 服务
sudo systemctl start ollama
```

## 方式二：Docker 部署

如果服务器上已经有 Docker，这种方式最省事：

```bash
docker pull ollama/ollama

docker run -d --name ollama \
  -p 11434:11434 \
  -v /opt/ollama:/root/.ollama \
  -e OLLAMA_HOST=0.0.0.0:11434 \
  ollama/ollama
```

模型数据挂载在宿主机的 `/opt/ollama`，容器重建后模型不会丢。之后可以用 Modelfile 导入本地模型：

```bash
ollama create qwen2.5-3b -f Modelfile
```

Modelfile 怎么写，见下一篇[《Ollama 导入本地 GGUF 模型：以 Qwen2.5-3B 为例》](/posts/ollama-qwen25-gguf/)。

## 参考链接

1. <https://yelog.org/2024/10/10/install-ollama-offline/>
2. <https://blog.csdn.net/sunyuhua_keyboard/article/details/144692663>
