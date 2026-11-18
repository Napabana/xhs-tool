# xhs-tool

一个面向个人学习资料整理的本地小红书图文处理工具。

目标是把目前的：

> 小红书链接 → Chrome 插件下载 ZIP → 解压 → 上传 Smallpdf → 下载 PDF

简化为：

> 小红书链接 → 本地工具 → 图片 / PDF / OCR

本项目以**源码可维护、模块清晰、方便 Codex 后续开发**为优先，不追求一开始就做 GUI 或打包成 EXE。

## 1. 项目目标

输入一条小红书图文笔记链接，工具能够自动获取该笔记的全部图片，并根据参数选择以下处理方式：

- `images`：只下载图片。
- `pdf`：下载图片并按照原始顺序生成 PDF。
- `ocr`：下载图片并进行本地 OCR，输出 Markdown / 文本。
- `all`：同时生成图片、PDF 和 OCR 结果。

目标使用方式：

~~~bash
uv run xhs-tool "https://www.xiaohongshu.com/..." --mode pdf
~~~

或者：

~~~bash
uv run xhs-tool "https://www.xiaohongshu.com/..." --mode images
uv run xhs-tool "https://www.xiaohongshu.com/..." --mode ocr
uv run xhs-tool "https://www.xiaohongshu.com/..." --mode all
~~~

最终希望用户不需要再手动处理 ZIP，也不需要使用 Smallpdf 等在线转换服务。

## 2. 当前状态

当前仓库是项目初始化阶段。

**第一阶段必须先完成：**

1. 从小红书 URL 获取图文笔记。
2. 下载全部图片。
3. 保持图片原始顺序。
4. 根据笔记标题建立输出目录。
5. 支持图片转 PDF。
6. 支持本地 OCR。
7. 提供清晰的 CLI。
8. 为核心逻辑编写测试。
9. 所有 Cookie、代理、个人配置都不能进入 Git。

后续再考虑批量链接、GUI、长图、增强 OCR 等功能。

## 3. 核心设计原则

### 3.1 不自己重新实现小红书解析

小红书页面和接口经常变化，因此不要在本项目中重新实现一套完整的小红书逆向解析逻辑。

下载层优先复用：

**XHS-Downloader**

官方仓库：

https://github.com/JoeanAmier/XHS-Downloader

当前上游版本已经支持图文作品下载、CLI/API 等能力，并且持续针对小红书规则变化进行维护。不要复制整个 XHS-Downloader 源码到本仓库，而应该通过独立 adapter 调用它。

重要：

- 不要把 XHS-Downloader 源码 vendor 到本项目。
- 不要把上游代码复制后再修改。
- 不要假设某个旧版本 CLI 参数永远有效。
- Codex 开始实现前，应先检查当前上游 README、release 和实际代码接口。
- 建议固定一个经过验证的 tag/commit，而不是无条件跟随 master。
- 上游发生变化时，只需要修改 downloader adapter。

### 3.2 本项目负责“后处理”

项目自身主要负责：

~~~text
XHS URL
  ↓
Downloader Adapter
  ↓
Downloaded Images
  ↓
Image Normalizer
  ├── PDF Generator
  └── OCR Engine
~~~

这样下载逻辑和后处理逻辑解耦。

### 3.3 OCR 必须优先本地运行

第一版不使用在线 OCR API。

优先使用：

- RapidOCR
- ONNX Runtime

原因：

- 不需要上传学习资料。
- 不依赖第三方 API Key。
- 适合个人长期使用。
- 中文教程图片是主要使用场景。

如果后续发现 RapidOCR 对复杂页面效果不足，再考虑 PaddleOCR 等方案。

### 3.4 PDF 不上传第三方网站

PDF 应在本地生成。

推荐使用 Pillow 或 img2pdf 等成熟库。

需要正确处理：

- PNG
- JPEG
- WebP
- RGBA
- RGB
- 灰度图
- EXIF orientation
- 不同图片尺寸
- 透明背景

默认策略：

**一张原始图片对应 PDF 中的一页，不进行裁剪。**

如果图片尺寸比例不同，应优先保持原始比例，而不是强行统一成 A4 后裁剪。

## 4. 推荐项目结构

第一版推荐使用：

~~~text
xhs-tool/
├── src/
│   └── xhs_tool/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── models.py
│       ├── pipeline.py
│       ├── downloader.py
│       ├── image.py
│       ├── pdf.py
│       ├── ocr.py
│       └── utils.py
│
├── tests/
│   ├── test_image.py
│   ├── test_pdf.py
│   ├── test_ocr.py
│   └── test_utils.py
│
├── output/
│   └── .gitkeep
│
├── pyproject.toml
├── README.md
├── .gitignore
└── LICENSE
~~~

不要为了第一版引入复杂的框架。

CLI 可以使用：

- Python 标准库 argparse；或者
- Typer。

如果没有明显理由，优先保持依赖较少。

项目环境优先使用：

- Python 3.12+
- uv

## 5. CLI 设计

最终目标：

~~~bash
uv run xhs-tool "<URL>" --mode pdf
~~~

### 必须支持

~~~text
xhs-tool URL --mode images
xhs-tool URL --mode pdf
xhs-tool URL --mode ocr
xhs-tool URL --mode all
~~~

### 建议参数

~~~text
--mode {images,pdf,ocr,all}
--output PATH
--cookie TEXT
--cookie-file PATH
--proxy TEXT
--keep-images
--overwrite
--verbose
~~~

参数设计可以根据实际实现调整，但不要为了增加参数而增加参数。

### 默认行为

如果用户没有指定 `--output`：

~~~text
./output/<safe-note-title>/
~~~

例如：

~~~text
output/
└── Qwen3.5技术解析/
    ├── images/
    │   ├── 001.png
    │   ├── 002.png
    │   ├── 003.png
    │   └── ...
    ├── Qwen3.5技术解析.pdf
    └── Qwen3.5技术解析.md
~~~

如果只执行 `--mode pdf`，是否保留图片由 `--keep-images` 控制。

但是开发初期建议始终保留图片，便于调试。

## 6. 图片顺序是核心要求

小红书笔记中的图片顺序必须保持。

例如原笔记：

~~~text
第 1 张
第 2 张
第 3 张
第 4 张
~~~

输出必须是：

~~~text
001.png
002.png
003.png
004.png
~~~

不能依赖随机下载完成顺序。

下载器返回的数据如果已经带有 index，则使用 index。

如果只能从文件名判断，则必须显式排序。

不能直接：

~~~python
for path in Path(...).iterdir():
    ...
~~~

然后假设文件系统顺序就是原始顺序。

## 7. 文件名处理

小红书标题可能包含 Windows 非法文件名字符：

~~~text
\ / : * ? " < > |
~~~

需要统一经过：

~~~text
sanitize_filename()
~~~

处理。

同时需要考虑：

- 标题为空。
- 标题过长。
- 标题包含换行。
- 标题末尾存在空格或点。
- Windows 保留名称，例如 CON、PRN、AUX、NUL。
- 同名笔记。

不能因为一个标题导致整个任务失败。

## 8. Cookie / Proxy

小红书访问可能受到登录状态、风控、网络环境等影响。

因此 CLI 应支持显式传入：

~~~bash
--cookie "..."
--cookie-file cookies.txt
--proxy "http://127.0.0.1:7890"
~~~

但是：

**绝对不能把 Cookie 写进源码、README、测试数据或 Git。**

推荐支持环境变量，例如：

~~~text
XHS_COOKIE
XHS_PROXY
~~~

如果未来支持自动读取浏览器 Cookie，也应该作为独立功能，不要让核心 downloader 强依赖浏览器。

## 9. Downloader Adapter

推荐抽象成类似：

~~~python
class Downloader(Protocol):
    def download(self, url: str, output_dir: Path) -> DownloadResult:
        ...
~~~

其中 `DownloadResult` 至少包含：

~~~text
title
note_id
image_paths
source_url
~~~

如果能获取更多信息，可以保存：

~~~text
author
publish_time
description
image_urls
~~~

但第一版不要为了保存完整笔记元数据而增加复杂度。

核心目标只有：

~~~text
URL → title + ordered image files
~~~

### 上游适配

XHS-Downloader 当前已经有 Python API / CLI 能力，具体调用方式以实际 pinned 版本为准。

Codex 实现时必须：

1. 查看上游当前版本。
2. 确认 Python API 或 CLI 的实际接口。
3. 写一个最小 adapter。
4. 用真实小红书图文链接验证。
5. 将上游版本写入项目依赖或配置。
6. 在 README 中记录经过验证的版本。

不要根据旧博客或搜索结果猜 API。

## 10. PDF Generator

建议：

~~~text
List[Path]
    ↓
validate image
    ↓
EXIF transpose
    ↓
convert to PDF-compatible mode
    ↓
write PDF
~~~

要求：

- 图片顺序严格一致。
- 每张图片一页。
- 不裁剪。
- 不降低分辨率，除非用户明确要求。
- 对 RGB/RGBA/L 等模式正确处理。
- 输出失败时给出具体文件名。
- 不因为单个坏图片产生难以理解的异常。

PDF 生成器应该可以独立于小红书 downloader 使用。

例如测试可以直接：

~~~python
generate_pdf(
    [
        Path("001.png"),
        Path("002.png"),
        Path("003.png"),
    ],
    Path("result.pdf"),
)
~~~

## 11. OCR

OCR 输入：

~~~text
001.png
002.png
003.png
~~~

输出：

~~~markdown
# 笔记标题

## Page 1

OCR text...

## Page 2

OCR text...

## Page 3

OCR text...
~~~

要求：

- 页码和图片一一对应。
- OCR 失败时不能导致整个下载任务崩溃。
- 单页失败应该记录 warning，并继续处理后面的图片。
- 保存原始 OCR 结果。
- 不要在第一版强行做复杂的 LLM 清洗。
- OCR 后处理应该和 OCR engine 解耦。

后续可以增加：

~~~text
--ocr-format md
--ocr-format txt
--ocr-format json
~~~

但第一版 Markdown 足够。

## 12. Pipeline

推荐：

~~~python
def run(url: str, mode: Mode, config: Config):
    metadata = downloader.download(url)

    images = normalize_images(metadata.image_paths)

    if mode in {"pdf", "all"}:
        generate_pdf(images)

    if mode in {"ocr", "all"}:
        run_ocr(images)
~~~

不要让 CLI 直接调用底层实现。

推荐层次：

~~~text
CLI
 ↓
Pipeline
 ↓
Downloader / PDF / OCR
 ↓
Utils / Models
~~~

这样未来增加 GUI、Web API 或批量任务时，可以复用 Pipeline。

## 13. 错误处理

需要区分：

### URL 错误

例如：

~~~text
Invalid Xiaohongshu URL
~~~

### 下载失败

例如：

~~~text
Failed to extract note
Failed to download image 3/8
~~~

### PDF 失败

例如：

~~~text
Failed to convert image 004.png
~~~

### OCR 失败

例如：

~~~text
OCR failed for page 5
~~~

错误信息必须告诉用户：

1. 哪一步失败。
2. 哪个文件失败。
3. 是否已经生成部分结果。
4. 是否建议重新运行。

不要直接打印巨大的第三方 traceback 作为唯一错误信息。

Debug 模式下可以保留 traceback。

## 14. 测试要求

第一版至少测试：

### PDF

- 1 张图片。
- 多张图片。
- 不同尺寸。
- RGBA。
- JPEG + PNG 混合。
- 图片顺序。
- 空输入。
- 不存在的图片。

### Utils

- Windows 非法字符。
- 超长文件名。
- 空标题。
- Windows 保留文件名。
- 重名处理。

### OCR

不要把真实小红书内容提交到仓库。

可以使用：

~~~text
tests/fixtures/
~~~

放置极小的人工测试图片。

### Downloader

Downloader 的真实网络测试不应该作为普通 unit test 每次执行。

可以单独提供：

~~~text
tests/integration/
~~~

并要求显式开启，例如：

~~~bash
uv run pytest tests/integration -m network
~~~

这样 CI 不会依赖小红书网络。

## 15. Git 安全

以下内容绝对不能提交：

~~~text
Cookie
Session
Access Token
代理账号密码
个人浏览器数据
下载的笔记图片
生成的 PDF
OCR 输出
~~~

因此 `.gitignore` 至少应该包含：

~~~text
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
output/*
!output/.gitkeep
.env
*.log
cookies.txt
cookies.json
~~~

如果需要测试图片，必须使用自己创建或明确允许再分发的 fixture。

## 16. 第一阶段实现顺序

不要一次实现所有功能。

### Phase 1：Downloader

目标：

~~~text
URL
 ↓
XHS-Downloader
 ↓
title
 ↓
ordered images
~~~

验收：

~~~bash
uv run xhs-tool "<real xhs url>" --mode images
~~~

能够得到完整图片。

### Phase 2：PDF

目标：

~~~text
images/
 ↓
PDF
~~~

验收：

~~~bash
uv run xhs-tool "<real xhs url>" --mode pdf
~~~

生成的 PDF 页数和图片数量一致，顺序一致。

### Phase 3：OCR

目标：

~~~text
images/
 ↓
RapidOCR
 ↓
markdown
~~~

验收：

~~~bash
uv run xhs-tool "<real xhs url>" --mode ocr
~~~

### Phase 4：All

~~~bash
uv run xhs-tool "<real xhs url>" --mode all
~~~

一次生成：

~~~text
images/
xxx.pdf
xxx.md
~~~

### Phase 5：质量改进

再处理：

- 重试。
- 日志。
- Cookie。
- Proxy。
- 重复下载。
- 缓存。
- 多链接。
- 并发。
- 更好的 OCR。
- GUI。

## 17. 不要在第一版做的事情

第一版明确不要做：

- Web 服务。
- FastAPI。
- 数据库。
- Docker。
- GUI。
- Chrome Extension。
- 云端 OCR。
- 用户系统。
- 登录系统。
- 自动同步云盘。
- MCP Server。
- 大模型总结。
- 向量数据库。
- 复杂任务队列。
- 多线程并发下载。

这个项目首先只是一个稳定的本地 CLI 工具。

## 18. 后续可能增加的功能

### 批量链接

~~~bash
uv run xhs-tool --input links.txt --mode pdf
~~~

### 剪贴板

复制链接后：

~~~bash
uv run xhs-tool --clipboard --mode pdf
~~~

### OCR + Markdown

~~~text
图片
 ↓
OCR
 ↓
Markdown
 ↓
后续可以交给 LLM 总结
~~~

### 长图

把多张图片拼成长图，适合手机阅读。

### 统一知识库

后续可以进一步生成：

~~~text
note/
├── source/
├── images/
├── note.pdf
├── note.md
└── metadata.json
~~~

最终可以作为个人知识库输入。

## 19. Codex 开发说明

如果由 Codex 接手本项目，**首先完整阅读本 README，然后再开始修改代码。**

执行顺序：

~~~text
1. git clone
2. 阅读 README
3. 检查当前仓库状态
4. 检查 Python / uv
5. 检查 XHS-Downloader 当前版本和接口
6. 设计 downloader adapter
7. 实现最小可运行版本
8. 写 unit tests
9. 使用真实小红书图文链接进行手动 integration test
10. 修复问题
11. 更新 README
12. commit
~~~

Codex 不应该：

- 直接把整个 XHS-Downloader 复制进来。
- 根据过时文章猜接口。
- 为了绕过问题重新实现小红书逆向。
- 把 Cookie 写入代码。
- 把真实笔记下载到 Git。
- 一次引入大量不必要依赖。
- 在没有验证的情况下宣称下载器可用。
- 修改用户已经存在的其他项目。

如果发现上游 XHS-Downloader 的 API 与预期不同，应优先调整 adapter，而不是破坏本项目的 Pipeline / PDF / OCR 架构。

## 20. 验收标准

第一版完成后，下面的命令应该成立：

~~~bash
uv run xhs-tool "<URL>" --mode images
uv run xhs-tool "<URL>" --mode pdf
uv run xhs-tool "<URL>" --mode ocr
uv run xhs-tool "<URL>" --mode all
~~~

对于一篇包含 N 张图片的图文笔记：

~~~text
images 数量 = N
PDF 页数 = N
PDF 第 i 页 = images/第 i 张图片
OCR Page i = 第 i 张图片的 OCR
~~~

最重要的最终体验：

~~~text
复制小红书链接
        ↓
运行一条命令
        ↓
得到 PDF
~~~

不再需要：

~~~text
Chrome 插件
→ ZIP
→ 解压
→ Smallpdf
→ 上传
→ 下载
~~~

## 21. 上游项目

XHS-Downloader：

https://github.com/JoeanAmier/XHS-Downloader

RapidOCR：

https://github.com/RapidAI/RapidOCR

本项目只是对上述能力进行本地化组合和后处理，不声称拥有上游项目的代码或接口。

## 22. 使用范围

本项目面向个人学习资料整理。

使用时应遵守小红书的服务条款、相关法律法规以及内容作者的版权和授权要求。不要用于大规模抓取、绕过访问控制、侵犯版权或其他违反平台规则的用途。
