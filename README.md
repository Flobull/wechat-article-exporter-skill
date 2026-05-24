# 微信公众号文章 CLI 下载工具

> **告别鼠标，拥抱终端** — 让你和 AI 都能丝滑操控微信公众号文章的批量下载。

## 🙏 致敬上游

本项目基于 [wechat-article-exporter](https://github.com/wechat-article/wechat-article-exporter) 构建。

**感谢原作者** — 那个优雅的 Web 工具让公众号文章导出变得前所未有的简单。我们在它的肩膀上，做了一层**命令行外壳**，让批量操作可以脱离浏览器，直接在你的终端里跑。

---

## 为什么你需要它？

**如果你是人：**
还在 Web 页面里一篇一篇点下载？一条命令同步所有公众号，一条命令批量下载全部文章，喝着咖啡等结果就好。

**如果你是 AI（Agent）：**
每个命令都结构清晰、返回可解析，AI 可以精准调用。`wechat.py` 就是你的 API。

**人机复用，同一套工具，人和机器都能上手。**

---

## 一句话展示

```bash
python3 wechat.py sync run --latest 10     # 同步所有公众号最新 10 篇
python3 wechat.py download batch --latest 10  # 批量下载
python3 wechat.py ui                        # 进入交互式菜单
```

---

## 功能总览

| 模块 | 功能 | 说明 |
|------|------|------|
| **配置管理** | `config show / set` | 管理 API 地址、密钥、下载目录、格式 |
| **公众号管理** | `account search / add / remove / list / import / export` | 搜索、关注、导入导出公众号 |
| **同步管理** | `sync run --latest / --range / --all` | 同步文章链接（增量/全量） |
| **文章查询** | `article list / latest / search / range / undownloaded` | 按各种条件查询已同步文章 |
| **下载管理** | `download article / batch / list / verify --repair` | 下载文章、校验、修复记录 |
| **数据库管理** | `manage stats / list / unfollow / scan / clear-downloads` | 统计、清理、库存扫描 |
| **交互式 TUI** | `ui` | 不间断菜单界面，所有功能指尖可及 |

---

## 快速开始

```bash
# 1. 配置（首次使用）
python3 wechat.py config set base_url https://你的部署地址
python3 wechat.py config set api_key 你的API密钥
python3 wechat.py config set download_dir ./下载

# 2. 搜索并关注公众号
python3 wechat.py account search 量化

# 3. 同步文章链接
python3 wechat.py sync run --latest 10

# 4. 下载文章
python3 wechat.py download batch --latest 10

# 5. 查看统计
python3 wechat.py manage stats
```

---

## 命令行参考

### 配置管理

```
wechat config show                    查看配置
wechat config set <key> <value>       修改配置项
```

### 公众号管理

```
wechat account search <keyword>       搜索公众号
wechat account add                    批量关注（交互式）
wechat account remove <fakeid>        取消关注
wechat account list                   列出已关注
wechat account import <file>          导入公众号.json
wechat account export [file]          导出公众号.json
```

### 同步管理

```
wechat sync run [fakeid]              同步文章链接
  --latest <N>                        最新 N 篇
  --range <from> <to>                 给定时间段
  --all                               全部同步
wechat sync check-new [fakeid]        检查新文章
```

### 文章查询

```
wechat article list [fakeid]          列出已同步文章
wechat article latest [fakeid] <N>    最新 N 篇
wechat article search <keyword>       搜索标题
wechat article range <fakeid> <from> <to>  时间筛选
wechat article undownloaded [fakeid]  列出未下载
```

### 下载管理

```
wechat download article <url>         下载单篇
wechat download batch [fakeid]        批量下载
  --latest <N>                        最新 N 篇
  --range <from> <to>                 给定时间段
  --format <fmt>                      指定格式
  --overwrite                         覆盖已下载
wechat download list [fakeid]         列出下载记录
wechat download verify [fakeid]       校验文件完整性
  --repair                            自动修复
```

### 数据库管理

```
wechat manage stats                   统计信息
wechat manage list [fakeid]           列出公众号详情
wechat manage import <file>           导入
wechat manage export [file]           导出
wechat manage unfollow <fakeid>       取消关注并删除数据
  --delete-files                      同时删除文件
wechat manage scan                    扫描库存更新
  --auto                              切换自动扫描
wechat manage clear-downloads         清空下载记录
```

### 交互式 TUI

```
wechat ui                             进入交互菜单
```

---

## 特色亮点

- **全平台兼容**：Windows / macOS / Linux / WSL，路径自动适配
- **智能库存扫描**：自动检测新文件、已删除文件，数据库与文件系统始终一致
- **校验修复**：`verify --repair` 一键清理无效记录
- **增量下载**：已下载的文件自动跳过，不会重复浪费
- **多格式导出**：HTML / Markdown / Text / JSON，一次下载全部到手
- **AI 友好**：每条命令返回清晰的结构化输出，Agent 可直接调用

---

## 配置说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `base_url` | 上游服务地址 | — |
| `api_key` | API 密钥 | — |
| `download_dir` | 下载保存目录 | — |
| `default_format` | 默认下载格式 | `text,html,markdown` |
| `auto_scan` | 启用自动库存扫描 | `true` |
| `dir_structure` | 目录结构 | `account` |

---

## 许可证

基于 MIT 许可证开源。详见 [LICENSE](./LICENSE)。

上游项目 [wechat-article-exporter](https://github.com/wechat-article/wechat-article-exporter) 同样使用 MIT 许可证。

**感谢所有开源贡献者，让好工具惠及更多人。**
