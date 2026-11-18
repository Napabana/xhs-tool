# xhs-tool

用一条小红书图文笔记链接，在本地按原帖顺序下载图片，或将图片合成 PDF。

**本项目仅供个人使用。** 请遵守小红书平台规则，并尊重内容作者的版权与授权范围。仅处理你有权访问和保存的内容，请勿用于批量抓取、商业用途或重新分发他人内容。

## 从克隆到首次运行

以下以 Windows PowerShell 为例。先安装 Git、Python 3.12 和 uv，确认 `git --version`、`python --version` 和 `uv --version` 可运行。若希望项目和下载留在 E 盘，先切换到 E 盘的目标目录。

```powershell
git clone https://github.com/Napabana/xhs-tool.git
cd xhs-tool

git clone --branch 2.8 --depth 1 https://github.com/JoeanAmier/XHS-Downloader.git ../upstream-phase1
uv sync --locked --python 3.12

$requirements = Get-Content ../upstream-phase1/requirements.txt | Where-Object {
    $_ -match '^[a-zA-Z]' -and $_ -notmatch '^pywebview=='
}
uv pip install $requirements

uv run --no-sync xhs-tool --help
```

这会在项目内创建 `.venv`，并把 XHS-Downloader 单独检出到同级目录。项目使用 [XHS-Downloader 2.8](https://github.com/JoeanAmier/XHS-Downloader/releases/tag/2.8) 的 Python API，固定提交为 `47840a1bee8438324ff10753c4291148c46071c8`。安装时跳过上游图形界面依赖。若已将该版本检出到其他位置，设定 `$env:XHS_DOWNLOADER_DIR = "<上游目录的绝对路径>"`，并用该目录的 `requirements.txt` 执行上述依赖安装。

## 下载图片或 PDF

在项目目录执行，将示例中的 URL 换成小红书 App 复制的图文分享链接，或浏览器内能打开的图文笔记链接。

```powershell
# 只下载图片，默认模式
uv run --no-sync xhs-tool "<图文笔记链接>" --mode images

# 生成 PDF，同时保留原图
uv run --no-sync xhs-tool "<图文笔记链接>" --mode pdf

# 将结果保存到仓库外的指定目录
uv run --no-sync xhs-tool "<图文笔记链接>" --mode pdf --output "E:\xhs-downloads"
```

默认在 `output/<笔记标题>/` 下生成 `images/`，图片按 `001`、`002` 等编号。PDF 模式还会在笔记目录生成同名 PDF。每张原图对应一页，保留顺序、像素尺寸和比例，自动校正 EXIF 方向，透明处铺白底。同名笔记会使用 ` (2)`、` (3)` 等后缀。命令会打印结果路径。

### 链接要求登录时

先在浏览器登录你自己的小红书账号并确认笔记可以打开。在开发者工具的「网络」面板中，找到发往 `www.xiaohongshu.com` 的笔记请求，将请求头中 `Cookie` 的**值**保存到仓库外的本地文本文件。将下列路径替换成实际文件路径。

```powershell
uv run --no-sync xhs-tool "<图文笔记链接>" --mode pdf --cookie-file "E:\private\xhs-cookies.txt"
```

也可通过环境变量 `XHS_COOKIE` 提供 Cookie。如果已有代理，可用 `--proxy <地址>` 或环境变量 `XHS_PROXY`。Cookie、代理凭据、下载图片及生成的 PDF 请留在本地。默认 `output/` 已被 Git 忽略，自定义输出建议放到仓库外。

遇到 `Failed to extract note` 时，先在浏览器确认链接和登录态。若短链仍跳到登录页，可复制浏览器地址栏中的完整笔记 URL 重试。
