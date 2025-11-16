# MontagePy

一个现代、快速且可配置的命令行工具，用于从视频文件生成缩略图网格。

## 功能特性

- 🎬 支持多种视频格式
- 🖼️ 可配置的网格布局（列数、行数）
- 🎨 可自定义缩略图样式和外观
- ⚙️ 支持 YAML 配置文件
- 🚀 并行处理，快速生成
- 📊 支持跳过视频开头和结尾的指定百分比

## 安装

```bash
pip install -e .
```

或者使用 uv：

```bash
uv pip install -e .
```

## 使用方法

### 基本用法

```bash
montagepy <input_path> [options]
```

### 命令行选项

主要选项包括：

- `-o, --output`: 输出路径（使用 `-` 输出到 stdout）
- `-c, --columns`: 网格列数（默认：4）
- `-r, --rows`: 网格行数（默认：5）
- `--thumb-width`: 缩略图宽度（默认：480）
- `--thumb-height`: 缩略图高度（-1 表示自动计算）
- `--padding`: 缩略图之间的内边距（默认：8）
- `--margin`: 网格边距（默认：24）
- `--header`: 头部高度（默认：120）
- `--skip-start`: 跳过开始百分比（默认：5.0）
- `--skip-end`: 跳过结束百分比（默认：5.0）
- `--font-file`: 字体文件路径
- `--config`: 配置文件路径

### 使用配置文件

复制示例配置文件并修改：

```bash
cp config.sample.yaml config.yaml
```

然后使用配置文件：

```bash
montagepy <input_path> --config config.yaml
```

## 配置示例

查看 `config.sample.yaml` 了解所有可配置选项。

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 构建可执行文件

```bash
python build.py
```

