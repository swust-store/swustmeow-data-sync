# swustmeow-data-sync

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
$ uv run python src/main.py`
```

如需指定浏览器通道：`set SWUSTMEOW_BROWSER_CHANNEL=msedge` 或 `chrome`

## 打包

```powershell
$ pwsh scripts/build_onefile_uv.ps1
```

- 产物：`dist/swustmeow-data-sync.exe`
- 日志：`output/output.log`
