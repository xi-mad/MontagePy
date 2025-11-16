# MontagePy

一个现代、快速且可配置的命令行工具，用于从视频文件生成缩略图网格（静态图片或动画 GIF）。

## 功能特性

- 🎬 **支持多种视频格式** - 使用 PyAV 处理各种视频格式
- 🖼️ **两种输出模式** - 静态 JPG 图片或动画 GIF
- 📐 **灵活的网格布局** - 可配置列数、行数，支持自动网格
- 🎨 **丰富的自定义选项** - 缩略图尺寸、间距、边距、字体、颜色等
- ⚙️ **YAML 配置文件** - 支持通过配置文件管理所有选项
- 🚀 **并行处理** - 多线程提取和处理，快速生成
- 📊 **智能帧提取** - 支持跳过视频开头和结尾的指定百分比
- 📁 **批量处理** - 支持单个文件或整个目录

## 安装

### 使用 pip

```bash
pip install -e .
```

### 使用 uv（推荐）

```bash
uv pip install -e .
```

### 系统要求

- Python >= 3.10
- 依赖：PyAV, Pillow, Click, PyYAML

## 使用方法

### 基本命令

MontagePy 提供两个主要命令：

#### 生成静态图片（JPG）

```bash
montagepy jpg <input_path> [options]
```

#### 生成动画 GIF

```bash
montagepy gif <input_path> [options]
```

### 输入路径

`<input_path>` 可以是：
- 单个视频文件：`montagepy jpg video.mp4`
- 目录（批量处理）：`montagepy jpg /path/to/videos/`

### 常用选项

#### 网格布局

- `-c, --columns <N>` - 网格列数（默认：4）
- `-r, --rows <N>` - 网格行数（默认：5）
- `--auto-grid` - 根据视频时长自动调整网格大小
- `--thumb-width <N>` - 缩略图宽度，像素（默认：640）
- `--thumb-height <N>` - 缩略图高度，像素（-1 表示自动计算）
- `--padding <N>` - 缩略图之间的间距（默认：5）
- `--margin <N>` - 网格四周的边距（默认：20）
- `--header <N>` - 头部信息区域高度（默认：120）

#### 输出选项

- `-o, --output <path>` - 输出路径（默认：输入文件同目录）
- `--overwrite` - 覆盖已存在的文件

#### 帧提取

- `--skip-start <percent>` - 跳过开始百分比（默认：5.0）
- `--skip-end <percent>` - 跳过结束百分比（默认：5.0）
- `--max-workers <N>` - 最大工作线程数（默认：8）

#### 外观选项

- `--font-file <path>` - 字体文件路径（用于显示视频信息和时间戳）
- `--font-color <color>` - 字体颜色（默认：white）
- `--shadow-color <color>` - 阴影颜色（默认：black）
- `--background-color <color>` - 背景颜色（默认：#222222）
- `--show-full-path` - 显示完整文件路径

#### GIF 专用选项

- `--clip-duration <seconds>` - 每个片段时长（默认：2.0）
- `--fps <N>` - GIF 帧率（默认：10，建议 8-15）
- `--colors <N>` - 颜色数量（默认：256，范围 2-256）
- `--loop <N>` - 循环次数（默认：0，0=无限循环）
- `--no-optimize` - 禁用 GIF 优化

#### JPG 专用选项

- `--jpeg-quality <N>` - JPEG 质量（默认：85，范围 1-100）

#### 全局选项

- `-c, --config <path>` - 配置文件路径
- `-q, --quiet` - 静默模式
- `-v, --verbose` - 详细输出
- `--version` - 显示版本信息

### 使用示例

#### 基本用法

```bash
# 生成静态图片
montagepy jpg video.mp4

# 生成动画 GIF
montagepy gif video.mp4

# 自定义网格大小
montagepy jpg video.mp4 -c 6 -r 4

# 使用自动网格
montagepy jpg video.mp4 --auto-grid

# 批量处理目录
montagepy gif /path/to/videos/ --overwrite
```

#### 高级用法

```bash
# 自定义外观
montagepy jpg video.mp4 \
  --font-file "/System/Library/Fonts/STHeiti Light.ttc" \
  --font-color "white" \
  --background-color "#1a1a1a" \
  --thumb-width 800

# 高质量 GIF
montagepy gif video.mp4 \
  --fps 12 \
  --colors 256 \
  --clip-duration 3.0

# 输出到指定位置
montagepy jpg video.mp4 -o /path/to/output.jpg
```

### 使用配置文件

复制示例配置文件：

```bash
cp config.sample.yaml config.yaml
```

编辑 `config.yaml` 并根据需要调整值，然后使用：

```bash
montagepy jpg video.mp4 --config config.yaml
montagepy gif video.mp4 --config config.yaml
```

配置文件支持所有选项，详见 `config.sample.yaml`。

## 配置说明

### 自动网格

启用 `--auto-grid` 后，系统会根据视频时长自动调整网格大小：

- 0-2 分钟：2x2 网格
- 2-10 分钟：3x3 网格
- 10-30 分钟：4x4 网格
- 30+ 分钟：5x5 网格

可以在配置文件中自定义这些规则。

### 输出文件命名

- 如果未指定输出路径，默认在输入文件同目录生成
- 命名格式：`<原文件名>_montage.<扩展名>`
- 例如：`video.mp4` → `video_montage.jpg` 或 `video_montage.gif`

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 构建可执行文件

使用 PyInstaller 构建独立可执行文件：

```bash
python build.py
```

或使用选项：

```bash
python build.py --clean    # 清理构建文件
python build.py --build    # 构建可执行文件
python build.py --clean --build  # 清理后构建
```

构建完成后，可执行文件位于 `dist/` 目录。

### 项目结构

```
montagepy/
├── cli/              # 命令行接口
│   ├── commands/     # 命令（jpg, gif）
│   └── options/      # 选项定义
├── core/             # 核心功能
│   ├── config.py     # 配置管理
│   ├── handlers.py   # 文件处理逻辑
│   └── logger.py     # 日志系统
├── converters/       # 格式转换器
├── extractors/       # 帧/片段提取器
├── renderers/        # 渲染器
└── utils/            # 工具函数
```

## 性能优化

项目已实现多项性能优化：

- ✅ 字体预加载（避免重复加载）
- ✅ 时间戳图层复用（避免每帧重复绘制）
- ✅ 并行帧提取（多线程处理）
- ✅ 优化的图像重采样算法

## 贡献

欢迎提交 Issue 和 Pull Request！
