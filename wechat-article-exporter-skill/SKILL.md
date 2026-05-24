---
name: wechat-article-exporter-skill
description: 微信公众号文章命令行下载工具。支持搜索关注公众号、同步文章、批量下载、管理下载记录。触发词包括 "下载公众号"、"同步文章"、"公众号文章"、"文章下载"、"批量下载"、"公众号管理"。
---

# 微信公众号文章 CLI 下载工具

## 快速使用

```bash
python3 wechat-cli/wechat.py <命令>
```

配置文件和数据库都在 `wechat-cli/` 目录下。

## 初始化配置

首次运行时自动创建 `config.json`，默认格式为 `txt,html,md`。如果缺少 `base_url` / `api_key` / `download_dir`，用 `question` 工具依次询问：

- **网站网址**（默认 `https://down.mptext.top`）
- **API Key**（从网站「API 页面」获取）
- **下载目录**（询问用户）
- **默认下载格式**（默认 `text,html,markdown`，保持即可）

写入 `config.json` 并回复 "✅ 配置已保存。"

## 命令参考

### 配置管理

| 命令 | 说明 |
|------|------|
| `config show` | 查看当前配置 |
| `config set <key> <value>` | 修改配置项 |

### 公众号管理

| 命令 | 说明 |
|------|------|
| `account search <keyword>` | 搜索公众号 |
| `account add` | 批量关注公众号（交互式） |
| `account remove <fakeid>` | 取消关注 |
| `account list` | 列出已关注公众号 |
| `account import <file>` | 从公众号.json导入 |
| `account export [file]` | 导出为公众号.json |

### 同步管理

| 命令 | 说明 |
|------|------|
| `sync run [fakeid]` | 同步文章链接，默认同步最新15篇 |
| `sync run --latest <N>` | 同步最新的N篇 |
| `sync run --range <from> <to>` | 同步给定时间段 |
| `sync run --all` | ⚠️ 全部同步（耗时较长，谨慎使用） |
| `sync check-new [fakeid]` | 检查新文章 |

### 文章查询

| 命令 | 说明 |
|------|------|
| `article list [fakeid]` | 列出已同步文章，默认所有公众号 |
| `article latest [fakeid] <N>` | 最新N篇 |
| `article search <keyword>` | 搜索文章标题 |
| `article range <fakeid> <from> <to>` | 时间范围筛选 |
| `article undownloaded [fakeid]` | 列出未下载文章 |

### 下载管理

| 命令 | 说明 |
|------|------|
| `download article <url>` | 下载单篇文章 |
| `download batch [fakeid]` | 批量下载，默认所有公众号 |
| `download batch --latest <N>` | 下载最新的X篇 |
| `download batch --range <from> <to>` | 下载给定时间段 |
| `download batch --all` | 全部下载 |
| `download batch --format <fmt>` | 指定格式 (html/markdown/text/json) |
| `download batch --overwrite` | 覆盖已下载的文件 |
| `download list [fakeid]` | 列出下载记录 |
| `download verify [fakeid]` | 校验文件完整性 |
| `download verify --repair` | 自动修复无效记录 |

### 数据库管理

| 命令 | 说明 |
|------|------|
| `manage stats` | 统计信息 |
| `manage list [fakeid]` | 列出公众号所有信息 |
| `manage import <file>` | 导入公众号.json |
| `manage export [file]` | 导出公众号.json |
| `manage unfollow <fakeid>` | 取消关注并删除数据 |
| `manage unfollow <fakeid> --delete-files` | 同时删除已下载文件 |
| `manage scan` | 扫描库存更新 |
| `manage scan --auto` | 切换自动扫描状态 |
| `manage clear-downloads` | 清空下载记录 |
| `manage clear-downloads -y` | 跳过确认 |

---

## 交互流程指引

### 下载公众号文章流程

**触发词**：用户说"下载公众号"、"文章下载"、"批量下载"、"下载文章"等。

1. **检查配置**
   - 运行 `python3 wechat-cli/wechat.py config show`
   - 如果缺少 `base_url` 或 `api_key`，用 `question` 询问并设置

2. **确认下载范围**
   - 用 `question` 询问下载方式：
     - 下载所有公众号最新N篇
     - 下载指定公众号
     - 按时间范围下载
   - 用 `question` 询问数量或时间范围

3. **确认格式**
   - 用 `question` 选择格式（可多选）：html / markdown / text / json
   - 默认：markdown,html,text

4. **执行下载**
   ```bash
   python3 wechat-cli/wechat.py download batch --latest <N> --format <fmt>
   ```

5. **输出结果**
   - 显示成功/失败/跳过数量
   - 显示下载目录位置

### 同步文章流程

**触发词**：用户说"同步文章"、"更新文章"、"检查新文章"等。

1. **检查配置**
   - 确认 `base_url` 和 `api_key` 已配置

2. **确认同步范围**
   - **注意**：`sync run --all` 会同步所有公众号的全部文章，可能耗费大量时间，应避免直接使用
   - 用 `question` 询问：同步所有公众号还是指定公众号
   - 用 `question` 询问：最新N篇（推荐） / 时间范围 / 全部同步（谨慎）
   - 优先推荐使用 `--latest <N>` 同步最新N篇，满足最低需求

3. **执行同步**
   ```bash
   python3 wechat-cli/wechat.py sync run --latest <N>
   ```

4. **输出结果**
   - 显示同步的文章数量
   - 显示新增文章数量

### 搜索关注公众号流程

**触发词**：用户说"搜索公众号"、"关注公众号"、"添加公众号"等。

1. **获取关键词**
   - 用 `question` 询问要搜索的公众号名称

2. **执行搜索**
   ```bash
   python3 wechat-cli/wechat.py account search <keyword>
   ```

3. **选择关注**
   - 如果有多个结果，用 `question` 让用户选择
   - 确认后执行关注

### 批量导入公众号流程

**触发词**：用户说"导入公众号"、"批量关注"、"批量导入"等。

1. **获取输入**
   - 用 `question` 询问输入方式：粘贴文本 / 提供文件路径
   - 获取关键词列表

2. **执行导入**
   ```bash
   python3 wechat-cli/wechat.py account import <file>
   ```

3. **输出结果**
   - 显示导入的公众号数量

---

## 行为准则

1. 所有交互使用中文
2. 命令执行前检查配置是否完整
3. 使用 `bash` 工具调用脚本，解析输出
4. 下载前确认用户意图，避免误操作
5. 提供清晰的操作反馈和结果统计
6. 调用 `sync run --all` 前必须先提示用户此操作可能耗时较长，优先推荐 `sync run --latest <N>`
