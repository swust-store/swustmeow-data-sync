# swustmeow-data-sync

> [!WARNING]
> **本网站为「西科喵数据同步工具」源代码仓库，并非下载地址或使用教程！**
> 
> 请加入官方 QQ 群（**1030083864** 或 **1056742797**）并在群文件中进行下载，使用教程：[【腾讯文档】西科喵常见问题解答](
https://docs.qq.com/doc/DSmdaRHRWeXp6WWFq?g=Mzc4NC0xNw%253D%253D#g=Mzc4NC0xNw%253D%253D)。

西科喵数据同步工具

## 运行

环境：`Python 3.12`

1. 创建虚拟环境并切换

```powershell
$ uv venv
$ .venv\Scripts\active.bat
```

2. 运行：

```powershell
$ uv run python src/main.py
```

如需指定浏览器通道：`set SWUSTMEOW_BROWSER_CHANNEL=msedge` 或 `chrome`。

## 打包

```powershell
$ pwsh scripts/build_onefile_uv.ps1
```

- 产物：`dist/swustmeow-data-sync.exe`
- 日志：`output/output.log`

如需使用 UPX 压缩以减小体积：

- 将 `upx` 加入 PATH，脚本会自动检测并传入 `--upx-dir`。
- 或手动指定路径：

```powershell
$ pwsh scripts/build_onefile_uv.ps1 -UPXDir "C:\tools\upx"
```

若未安装 UPX，脚本会正常打包但不做 UPX 压缩。
