# YouTube 视频下载器

一个基于 Python + tkinter 的 YouTube 视频下载工具，支持图形界面和命令行两种模式，内置 FFmpeg 和 Deno，开箱即用。

## 功能特性

- 🎬 **图形界面**：直观的 GUI 操作，适合普通用户
- 🎯 **多质量选择**：支持 best / 1080p / 720p / 480p / 360p
- 🔊 **音频提取**：仅下载音频并转换为 MP3
- 🔄 **音视频合并**：自动合并最佳画质视频流和最佳音质音频流
- 📊 **实时进度**：进度条 + 百分比显示，实时展示下载速度和剩余时间
- ⚡ **FFmpeg 自动安装**：缺失时一键自动安装，无需手动配置
- 📦 **单文件打包**：PyInstaller 打包为单个 EXE，内置 deno + ffmpeg
- 📝 **命令行版本**：CLI 模式，适合脚本集成

## 快速开始

### 方式一：直接运行 EXE（推荐）

下载 `YouTube_Downloader.exe`，双击即可运行，无需安装 Python 和任何依赖。

> 首次运行会解压内置的 deno 和 ffmpeg，启动稍慢，属于正常现象。

### 方式二：源码运行

```bash
# 克隆仓库
git clone https://github.com/fangbb-coder/Youtube_downloader.git
cd Youtube_downloader

# 安装依赖
pip install yt-dlp imageio-ffmpeg

# 运行 GUI 版本
python youtube_downloader_gui.py

# 或运行 CLI 版本
python youtube_downloader.py <视频URL>
```

## GUI 使用说明

1. 输入 YouTube 视频 URL
2. 选择输出目录（默认当前目录）
3. 选择视频质量（best / 1080p / 720p / 480p / 360p）
4. 可选：勾选「仅下载音频 (MP3)」
5. 可选：勾选「合并音视频 (需要 FFmpeg)」以获得最佳画质
6. 点击「开始下载」

### 关于 FFmpeg

- 勾选「合并音视频」或「仅下载音频」时需要 FFmpeg
- 如果系统没有 FFmpeg，程序会弹出提示，点击「是」即可自动安装
- EXE 版本已内置 FFmpeg，无需额外安装

### 关于 Deno

YouTube 视频解析需要 JavaScript runtime，程序会自动检测并使用：
- EXE 版本：内置 deno.exe
- 源码版本：自动查找系统 PATH 中的 deno

## CLI 使用说明

```bash
python youtube_downloader.py <URL> [选项]
```

**选项**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出目录 | 当前目录 |
| `-q, --quality` | 视频质量 (best/1080p/720p/480p/360p) | best |
| `-a, --audio-only` | 仅下载音频为 MP3 | 否 |
| `-l, --list-formats` | 列出可用格式 | 否 |
| `-n, --no-merge` | 不合并音视频流 | 否 |

**示例**：

```bash
# 下载最佳画质
python youtube_downloader.py "https://www.youtube.com/watch?v=xxx"

# 下载 1080p 并合并音视频
python youtube_downloader.py "https://www.youtube.com/watch?v=xxx" -q 1080p

# 仅下载音频
python youtube_downloader.py "https://www.youtube.com/watch?v=xxx" -a

# 查看可用格式
python youtube_downloader.py "https://www.youtube.com/watch?v=xxx" -l
```

## 打包 EXE

```bash
# 安装 PyInstaller
pip install pyinstaller

# 运行打包脚本
python build_exe.py
```

打包完成后，EXE 文件位于 `dist/YouTube_Downloader.exe`。

## 项目结构

```
Youtube_downloader/
├── youtube_downloader_gui.py   # GUI 主程序
├── youtube_downloader.py       # CLI 命令行版本
├── build_exe.py                # 打包脚本
├── .gitignore                  # Git 忽略配置
└── README.md                   # 项目说明
```

## 技术栈

- **GUI 框架**：tkinter / ttk
- **下载引擎**：[yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **音视频处理**：FFmpeg（通过 [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) 分发）
- **JS 运行时**：Deno
- **打包工具**：PyInstaller

## 常见问题

### Q: 下载时提示「ffmpeg is not installed」怎么办？

A: 点击弹窗中的「是」按钮，程序会自动安装 FFmpeg。源码运行时也可手动执行：

```bash
pip install imageio-ffmpeg
```

### Q: 下载速度慢怎么办？

A: YouTube 下载速度受网络环境影响，可尝试：
- 使用代理
- 选择较低画质
- 取消「合并音视频」（单文件下载更快）

### Q: 支持批量下载吗？

A: 当前版本暂不支持批量下载，可多次添加单个视频。

### Q: 支持下载播放列表吗？

A: 暂不支持播放列表下载，仅支持单个视频。

## License

MIT
