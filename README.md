# EssayReader · PDF 生词速查（离线词典）

读英文论文时随手查词的小工具：在 PDF 里选中单词或句子按 `Ctrl+C`，工具自动读取剪贴板并在本地词典中查询，全程离线、不联网、不调用任何翻译 API。

## 功能

- **剪贴板自动查词**：监听系统剪贴板变化，复制后自动清洗文本并查询。
- **全局热键**：`Ctrl+Alt+Q` 随时把查词窗口调到最前并聚焦输入框。
- **暂停/恢复监视**：`Ctrl+Alt+S` 或窗口内的“暂停监视/恢复监视”按钮切换。暂停期间复制不会触发查询，恢复时不会补查暂停期间复制的内容。
- **语言过滤**：剪贴板内容含中文字符、或不含任何英文字词时静默忽略，避免在聊天软件、浏览器里复制时误触发。
- **离线词库**：使用 [ECDICT](https://github.com/skywind3000/ECDICT) 的 `stardict.csv`，首次启动建立 SQLite 索引，之后查询都在本地完成。
- **文本清洗**：自动去除软连字符（`U+00AD`）、把 Unicode 连字符统一为 `-`，并拼接被换行拆开的连字符单词（如 `organi-` + `zation` → `organization`）。
- **词组优先**：先按整个词组查询；查不到时逐词给出释义；单词还支持前缀匹配兜底。
- **词条内容**：单词、音标、词性、中文释义、英文释义。

## 环境要求

- Windows（依赖全局热键与剪贴板序列号相关的 Win32 API）。
- Python 3.8 及以上（仅用标准库 `tkinter` / `sqlite3` / `ctypes`，无需 pip 安装）。
- 一份 ECDICT `stardict.csv`（仓库不附带词库文件）。

## 使用

1. 把 `stardict.csv` 放到 `start.ps1` 同目录；也可以设置环境变量 `ECDICT_CSV` 指向它的路径。
2. 在 PowerShell 中运行：

   ```powershell
   .\start.ps1
   ```

   `start.ps1` 会依次尝试：`python` → `py -3`；找不到词库时回退到 `%APPDATA%\GoldenDict\dictionaries\ECDICT\stardict.csv`。
3. 首次启动会生成 `ecdict_lookup.sqlite3` 索引（与 CSV 同目录），需要一点时间；之后启动直接复用索引。
4. 在任意 PDF 阅读器里选中文字按 `Ctrl+C`，窗口原地刷新释义（窗口保持置顶，但不会抢焦点、也不会闪烁任务栏）；也可直接在输入框中输入单词。
5. 按 `Ctrl+Alt+Q` 可随时呼出窗口；暂时不想被复制触发时按 `Ctrl+Alt+S` 或点窗口里的“暂停监视”。

## 目录结构

```
essayreader/
├── paper_lookup.py   # 主程序：字典索引、剪贴板监听、查词窗口
├── start.ps1         # 启动脚本：定位 Python 与词库并运行
├── stardict.csv      # ECDICT 词库（需自行下载，未包含在仓库中）
└── ecdict_lookup.sqlite3  # 首次运行生成的索引，可随时删除重建
```

## 说明

- 索引按 CSV 的修改时间判断是否需要重建，更新词库后删掉 `ecdict_lookup.sqlite3` 或直接重新运行即可。
- 全程无网络请求、无文档上传、无 API Key；适合处理不便外传的论文。
- 仅对可选中文字的 PDF 有效。扫描版 PDF 需要先自行 OCR。
- ECDICT 依据其项目仓库采用 MIT 协议：<https://github.com/skywind3000/ECDICT>。
