# EHentai ComicInfo（calibre 插件）

对选中的书籍，根据 `{gid}-{token}` 调用 E-Hentai API 获取元数据：

1. **写入 calibre 元数据**（覆盖式）：标题（日文优先，自动剥离 `(社团)[作者]` 包装）、
   作者（artist tag）、出版者（group tag）、标签（category + 全部 tags）、语言、
   评分（0-5 → 0-10）、发布日期、comments（英文标题 + gallery URL）、
   `ehentai` identifier（`gid_token`）。
2. **嵌入 ComicInfo.xml** 到压缩包内（zip 默认先转 cbz，可在配置中关闭）。

## gid/token 解析顺序

1. 书籍的 `ehentai` identifier（兼容 `gid_token` 与 `gid_token_0/1` 两种格式）；
2. 书名形如 `4105980-db7e47b670`（即直接以 `{gid}-{token}.zip` 导入、未改过标题的书）；
3. 书库内文件名形如 `{gid}-{token}.zip/.cbz`。

## 配套插件：EHentai Import

`../EHentaiImport` 是一个元数据读取插件：添加 `{gid}-{token}.zip` 到书库时
自动写入 `ehentai` identifier，后续即可被本插件精确识别。两个插件相互独立，
建议同时安装。

## 安装

```bash
calibre-customize -b /path/to/EHentaiComicInfo
calibre-customize -b /path/to/EHentaiImport
```

## 配置

工具栏「EHentai ComicInfo」菜单 → 配置：

- 代理开关与地址（默认 `http://127.0.0.1:7890`）
- 批量 API 请求间隔（默认 5 秒，每批最多 25 个）
- 嵌入 ComicInfo 前是否将 ZIP 转换为 CBZ（默认开）

## 注意

- 批量处理在 GUI 线程同步执行，书多时界面会暂时无响应，请等待完成弹窗。
- 元数据为**覆盖式**更新（仅覆盖 API 提供的字段）。
