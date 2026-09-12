# eh-meta

E-Hentai 漫画的 calibre 元数据插件组：根据 `{gid}-{token}` 文件名自动识别 gallery，
调用 E-Hentai API 获取元数据，**写入 calibre 书库**的同时**在压缩包内嵌入 ComicInfo.xml**。

包含两个相互独立的插件（一个 calibre 插件包只能注册一个插件类，因此拆分为两个）：

| 插件 | 类型 | 作用 |
|---|---|---|
| **EHentai Import** | 元数据读取（导入钩子） | 添加 `{gid}-{token}.zip` 进书库时自动写入 `ehentai` identifier |
| **EHentai ComicInfo** | 界面动作（工具栏按钮） | 批量获取元数据 → 覆盖写入 calibre → 嵌入 ComicInfo.xml |

## 功能

### EHentai Import（导入时自动）

向书库添加形如 `2231376-a7584a5932.zip` 的文件时，自动解析出 gallery id 与 token，
写入书籍的 `ehentai` identifier。文件名不匹配时静默回退到 calibre 默认的文件名解析，
不影响普通 zip 的导入。

### EHentai ComicInfo（选中书籍后点击）

对选中的书籍批量执行：

1. **解析 gid/token**，按以下顺序：
   - `ehentai` identifier（兼容 `gid_token` 与 `gid_token_0/1` 格式）
   - 书名形如 `2231376-a7584a5932`（直接以原文件名导入、未改过标题的书）
   - 书库内文件名形如 `{gid}-{token}.zip/.cbz`
2. **调用 E-Hentai gdata API** 获取元数据（每批最多 25 个，批间限速）；
3. **覆盖写入 calibre 元数据**：
   - 标题：日文优先（`title_jpn`），自动剥离 `(社团)[作者]` 等包装
   - 作者：`artist` tag；出版者：`group` tag
   - 标签：`category:xxx` + 全部原始 tags
   - 语言（ISO 639-3）、评分（0-5 → calibre 0-10）、发布日期
   - comments：英文标题 + gallery URL；`ehentai` identifier
4. **嵌入 ComicInfo.xml** 到压缩包内：
   - ZIP 默认先转为 CBZ（内容不变，可在配置中关闭）
   - 已存在 ComicInfo.xml 时原位替换，不产生重复条目

字段映射与 Komga / Kavita / CDisplayEx 等支持 ComicInfo 的阅读器兼容。

## 安装

在 [Releases](../../releases) 下载两个 zip（**不要解压**），然后：

calibre → 首选项 → 插件 → 从文件加载插件 → 分别选择两个 zip。

建议两个都装：导入钩子负责「新书自动识别」，界面动作负责「批量获取与嵌入」。

## 使用

1. 把 `{gid}-{token}.zip` 加入书库（自动获得 identifier）；
2. 选中一本书或多本书；
3. 点击工具栏「EHentai ComicInfo」（或下拉菜单中选择）：
   - **获取元数据并嵌入 ComicInfo（全部）** — 主按钮默认动作
   - 仅更新 calibre 元数据
   - 仅嵌入 ComicInfo.xml

## 配置

工具栏菜单 → 配置：

- 代理开关与地址（默认 `http://127.0.0.1:7890`；直连可关闭）
- 批量 API 请求间隔（默认 5 秒）
- 嵌入 ComicInfo 前是否将 ZIP 转换为 CBZ（默认开）

## 从源码构建

```bash
./build.sh        # 在 dist/ 下生成 EHentaiComicInfo.zip 与 EHentaiImport.zip
```

或直接以目录形式安装（开发调试）：

```bash
calibre-customize -b EHentaiComicInfo
calibre-customize -b EHentaiImport
```

## 注意事项

- 批量处理在 GUI 线程同步执行，书多时界面会暂时无响应，请等待完成弹窗
  （每批 25 本 + 5 秒间隔，100 本约 20 秒）。
- 元数据为**覆盖式**更新，仅覆盖 API 提供的字段。
- 仅支持表站（e-hentai.org）公开画廊；未实现里站（exhentai.org）cookie 与封面下载。

## 致谢

开发参考了以下两个开源项目：

- [Ehentai_metadata](https://github.com/nonpricklycactus/Ehentai_metadata) — E-Hentai API 调用与标题结构解析思路
- [EmbedComicMetadata](https://github.com/dickloraine/EmbedComicMetadata) — calibre 书库内压缩包的 ComicInfo.xml 读写方式

## License

GPL v3
