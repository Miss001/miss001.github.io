---
title: Ollama 导入本地 GGUF 模型：以 Qwen2.5-3B 为例
date: 2026-10-07
tags: [Ollama, 大模型, 离线部署]
summary: 离线环境无法 ollama pull，可以从 Hugging Face 下载 GGUF 文件，写一个 Modelfile（模型路径 + 对话模板 + 停止词），再用 ollama create 导入并通过 API 测试。
source: https://github.com/Miss001/ai/blob/main/ollama/模型部署.md
source_name: Miss001/ai · ollama/模型部署.md
---

离线环境里 `ollama pull` 用不了，但 Ollama 支持通过 **Modelfile** 导入本地的 GGUF 模型文件。下面以 Qwen2.5-3B 为例。

## 1. 从 Hugging Face 下载模型

在 Hugging Face 上找到对应模型的 GGUF 版本并下载，例如：

<https://huggingface.co/Qwen/Qwen1.5-0.5B-Chat-GGUF/tree/main>

> 编者注：原笔记给的是 Qwen 系列 GGUF 仓库的示例链接，下载时按需要的模型和量化版本挑选文件即可，下文假设文件名为 `qwen2.5-3b.gguf`。

## 2. 创建 Modelfile

Modelfile 由三部分组成：模型文件路径（`FROM`）、对话模板（`TEMPLATE`）和参数（`PARAMETER`）。

```dockerfile
# 上一步的模型名
FROM ./qwen2.5-3b.gguf

# 可以到 ollama 网站上的模型库去寻找, 如 qwen2.5-3b 的模板地址: https://ollama.com/library/qwen2.5:3b/blobs/eb4402837c78
# 直接复制 ollama 上的 Template 到如下三个双引号中间
TEMPLATE """{{- if .Messages }}
{{- if or .System .Tools }}<|im_start|>system
{{- if .System }}
{{ .System }}
{{- end }}
{{- if .Tools }}

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{{- range .Tools }}
{"type": "function", "function": {{ .Function }}}
{{- end }}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>
{{- end }}<|im_end|>
{{ end }}
{{- range $i, $_ := .Messages }}
{{- $last := eq (len (slice $.Messages $i)) 1 -}}
{{- if eq .Role "user" }}<|im_start|>user
{{ .Content }}<|im_end|>
{{ else if eq .Role "assistant" }}<|im_start|>assistant
{{ if .Content }}{{ .Content }}
{{- else if .ToolCalls }}<tool_call>
{{ range .ToolCalls }}{"name": "{{ .Function.Name }}", "arguments": {{ .Function.Arguments }}}
{{ end }}</tool_call>
{{- end }}{{ if not $last }}<|im_end|>
{{ end }}
{{- else if eq .Role "tool" }}<|im_start|>user
<tool_response>
{{ .Content }}
</tool_response><|im_end|>
{{ end }}
{{- if and (ne .Role "assistant") $last }}<|im_start|>assistant
{{ end }}
{{- end }}
{{- else }}
{{- if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ end }}{{ .Response }}{{ if .Response }}<|im_end|>{{ end }}
"""

# 这一步参考 ollama 上的 parameters, 但是 ollama 上的 qwen2.5-3b 是没有参数的, 按照下面的格式添加即可
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
```

要点：

- `TEMPLATE` 不用自己写，直接到 Ollama 模型库对应模型的页面复制；
- `PARAMETER stop` 设置停止词，否则模型可能不停地输出下去。

## 3. 加载运行模型

```bash
# 通过模型描述文件, 创建并运行 qwen2.5 模型
ollama create qwen2.5 -f Modelfile
# 查看模型列表, 确认模型已创建
ollama ls
```

## 4. 测试

通过 API 调用模型，检查是否运行正常，顺便看看响应耗时：

```bash
curl --location --request POST 'http://127.0.0.1:11434/api/generate' \
--header 'Content-Type: application/json' \
--data '{
    "model": "qwen2.5",
    "stream": false,
    "prompt": "你好, 24节气的第一个节气是什么?"
}' \
-w "Time Total: %{time_total}s\n"
```

## 参考链接

- <https://yelog.org/2024/10/10/install-ollama-offline/>
