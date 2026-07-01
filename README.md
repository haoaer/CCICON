# VibeCoding PROJ_TOOL
# CCICON — Claude Code 状态托盘指示灯--目前只在windows下测试

# 简介
```
  CCICON 是一个 Windows 桌面程序，用于显示 Claude Code 运行状态
  先右键执行setup，更改配置文件，并添加Hooks 即可使用
```

系统托盘显示 Claude Code 任务状态：

| 图标 | 状态 | 行为 | 优先级 |
|------|------|------|--------|
| 🟢 绿色 | 完成 | 闪烁 3 秒后变灰 | 最高 |
| 🔴 红色 | 出错/询问 | 常亮 | ↑ |
| 🟡 黄色 | 工作中 | 常亮 | ↑ |
| ⚫ 灰色 | 空闲 | 常亮 | 最低 |

支持多 Claude 进程并发。Hook 以 JSONL 格式追加写入 `~/.claude/ccicon/status/current.jsonl`，托盘应用按 `pid` 分组取最新状态，再按优先级聚合显示。

## 安装

```bash
uv sync
```

## 打包命令
```bash
uv run pyinstaller --onefile --noconsole --name CCICON --icon=asset/icon.ico main.py
```

## 启动托盘应用

```bash
uv run main.py
```

托盘图标会出现在系统通知区域，每秒自动刷新状态。

## 配置 Claude Code Hooks

在 `~/.claude/settings.json` 中添加 hooks，让 Claude Code 自动上报状态：


## 状态文件

JSONL 格式，每行一条记录，追加写入 `~/.claude/ccicon/current.jsonl`：

```jsonl
{"pid": 12345, "status": "working", "task": "正在使用 Bash...", "updated_at": 1719849600}
{"pid": 12345, "status": "done", "task": "", "updated_at": 1719849602}
{"pid": 67890, "status": "working", "task": "正在读取文件...", "updated_at": 1719849603}
```

- `pid` — Claude Code 进程 ID，用于区分不同会话
- 按 pid 分组取最新一条，再按优先级聚合：`done` > `error` > `working` > `idle`
- 超过 10 分钟未更新的记录自动清理

