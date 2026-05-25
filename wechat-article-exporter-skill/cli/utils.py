#!/usr/bin/env python3
# coding: utf-8
"""
通用工具函数
"""
import json
import os
import sqlite3
import sys
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

# 路径常量
CLI_DIR = Path(__file__).parent
PROJECT_DIR = CLI_DIR.parent
CONFIG_PATH = PROJECT_DIR / "config.json"
DB_PATH = PROJECT_DIR / "wechat_articles.db"

# ANSI 颜色
R = "\033[0m"    # reset
B = "\033[1m"    # bold
D = "\033[2m"    # dim
G = "\033[38;5;245m"  # gray
Y = "\033[38;5;220m"  # gold
C = "\033[38;5;39m"   # blue
GR = "\033[38;5;82m"  # green
RD = "\033[38;5;196m" # red


def enable_ansi_colors():
    """启用 ANSI 颜色（Windows 需激活）"""
    if sys.platform == "win32":
        os.system("")
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass


def ensure_config():
    """若配置文件不存在，用默认值自动创建"""
    if CONFIG_PATH.exists():
        return
    cfg = {
        "default_format": "text,html,markdown",
        "auto_scan": True,
        "dir_structure": "account",
    }
    write_config(cfg)


def read_config():
    """读取配置文件"""
    ensure_config()
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except UnicodeDecodeError:
            with open(CONFIG_PATH, 'r', encoding='gbk') as f:
                return json.load(f)
    return {}


def write_config(cfg):
    """写入配置文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_conn():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库"""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            fakeid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            round_head_img TEXT DEFAULT '',
            service_type INTEGER DEFAULT 0,
            qrcodeurl TEXT DEFAULT '',
            province TEXT DEFAULT '',
            city TEXT DEFAULT '',
            country TEXT DEFAULT '',
            sync_cursor INTEGER DEFAULT 0,
            syncing INTEGER DEFAULT 0,
            sync_total INTEGER DEFAULT 0,
            auto_scan INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS articles (
            fakeid TEXT NOT NULL,
            aid TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT DEFAULT '',
            author TEXT DEFAULT '',
            digest TEXT DEFAULT '',
            create_time INTEGER DEFAULT 0,
            update_time INTEGER DEFAULT 0,
            cover TEXT DEFAULT '',
            pic_crop_1_1 TEXT DEFAULT '',
            pic_crop_16_9 TEXT DEFAULT '',
            is_deleted INTEGER DEFAULT 0,
            is_pay_subscribe INTEGER DEFAULT 0,
            is_only_fans INTEGER DEFAULT 0,
            item_show_type INTEGER DEFAULT 0,
            article_type INTEGER DEFAULT 0,
            send_fan_count INTEGER DEFAULT 0,
            appmsg_album_id TEXT DEFAULT '',
            downloaded INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            PRIMARY KEY (fakeid, aid),
            FOREIGN KEY (fakeid) REFERENCES accounts(fakeid) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aid TEXT NOT NULL,
            format TEXT NOT NULL,
            file_path TEXT DEFAULT '',
            file_size INTEGER DEFAULT 0,
            downloaded_at TEXT DEFAULT (datetime('now', 'localtime')),
            UNIQUE(aid, format)
        );

        CREATE INDEX IF NOT EXISTS idx_articles_fakeid ON articles(fakeid);
        CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title);
        CREATE INDEX IF NOT EXISTS idx_articles_create_time ON articles(create_time);
        CREATE INDEX IF NOT EXISTS idx_articles_fakeid_time ON articles(fakeid, create_time);
        CREATE INDEX IF NOT EXISTS idx_downloads_aid ON downloads(aid);
    """)
    conn.commit()
    conn.close()


def migrate_db():
    """数据库迁移"""
    conn = get_conn()

    # accounts 表迁移
    existing_cols = [row["name"] for row in conn.execute("PRAGMA table_info(accounts)").fetchall()]
    migrations = {
        "service_type": "ALTER TABLE accounts ADD COLUMN service_type INTEGER DEFAULT 0",
        "qrcodeurl": "ALTER TABLE accounts ADD COLUMN qrcodeurl TEXT DEFAULT ''",
        "province": "ALTER TABLE accounts ADD COLUMN province TEXT DEFAULT ''",
        "city": "ALTER TABLE accounts ADD COLUMN city TEXT DEFAULT ''",
        "country": "ALTER TABLE accounts ADD COLUMN country TEXT DEFAULT ''",
        "sync_cursor": "ALTER TABLE accounts ADD COLUMN sync_cursor INTEGER DEFAULT 0",
        "syncing": "ALTER TABLE accounts ADD COLUMN syncing INTEGER DEFAULT 0",
        "sync_total": "ALTER TABLE accounts ADD COLUMN sync_total INTEGER DEFAULT 0",
        "auto_scan": "ALTER TABLE accounts ADD COLUMN auto_scan INTEGER DEFAULT 1",
        "updated_at": "ALTER TABLE accounts ADD COLUMN updated_at TEXT DEFAULT (datetime('now', 'localtime'))",
    }
    for col, sql in migrations.items():
        if col not in existing_cols:
            conn.execute(sql)

    # articles 表迁移
    art_cols = [row["name"] for row in conn.execute("PRAGMA table_info(articles)").fetchall()]
    art_migrations = {
        "update_time": "ALTER TABLE articles ADD COLUMN update_time INTEGER DEFAULT 0",
        "cover": "ALTER TABLE articles ADD COLUMN cover TEXT DEFAULT ''",
        "pic_crop_1_1": "ALTER TABLE articles ADD COLUMN pic_crop_1_1 TEXT DEFAULT ''",
        "pic_crop_16_9": "ALTER TABLE articles ADD COLUMN pic_crop_16_9 TEXT DEFAULT ''",
        "is_only_fans": "ALTER TABLE articles ADD COLUMN is_only_fans INTEGER DEFAULT 0",
        "item_show_type": "ALTER TABLE articles ADD COLUMN item_show_type INTEGER DEFAULT 0",
        "article_type": "ALTER TABLE articles ADD COLUMN article_type INTEGER DEFAULT 0",
        "send_fan_count": "ALTER TABLE articles ADD COLUMN send_fan_count INTEGER DEFAULT 0",
        "appmsg_album_id": "ALTER TABLE articles ADD COLUMN appmsg_album_id TEXT DEFAULT ''",
        "is_pay_subscribe": "ALTER TABLE articles ADD COLUMN is_pay_subscribe INTEGER DEFAULT 0",
    }
    for col, sql in art_migrations.items():
        if col not in art_cols:
            conn.execute(sql)

    # downloads 表迁移
    dl_cols = [row["name"] for row in conn.execute("PRAGMA table_info(downloads)").fetchall()]
    if "file_size" not in dl_cols:
        conn.execute("ALTER TABLE downloads ADD COLUMN file_size INTEGER DEFAULT 0")

    # 修复 downloads 表 FOREIGN KEY (aid) REFERENCES articles(aid) 不匹配问题
    # articles 表的 PK 是 (fakeid, aid)，单独 aid 不是键，SQLite 拒绝该外键
    dl_schema = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='downloads'"
    ).fetchone()
    if dl_schema and 'FOREIGN KEY' in (dl_schema[0] or ''):
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS downloads_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aid TEXT NOT NULL,
                format TEXT NOT NULL,
                file_path TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                downloaded_at TEXT DEFAULT (datetime('now', 'localtime')),
                UNIQUE(aid, format)
            );
            INSERT INTO downloads_new SELECT * FROM downloads;
            DROP TABLE downloads;
            ALTER TABLE downloads_new RENAME TO downloads;
            CREATE INDEX IF NOT EXISTS idx_downloads_aid ON downloads(aid);
        """)
        conn.execute("PRAGMA foreign_keys=ON")

    # articles 表复合主键迁移（aid 跨号重复修复）
    pk_info = conn.execute("PRAGMA table_info(articles)").fetchall()
    pk_cols = [r for r in pk_info if r["pk"] > 0]
    if len(pk_cols) == 1 and pk_cols[0]["name"] == "aid":
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles_new (
                fakeid TEXT NOT NULL,
                aid TEXT NOT NULL,
                title TEXT NOT NULL,
                link TEXT DEFAULT '',
                author TEXT DEFAULT '',
                digest TEXT DEFAULT '',
                create_time INTEGER DEFAULT 0,
                update_time INTEGER DEFAULT 0,
                cover TEXT DEFAULT '',
                pic_crop_1_1 TEXT DEFAULT '',
                pic_crop_16_9 TEXT DEFAULT '',
                is_deleted INTEGER DEFAULT 0,
                is_pay_subscribe INTEGER DEFAULT 0,
                is_only_fans INTEGER DEFAULT 0,
                item_show_type INTEGER DEFAULT 0,
                article_type INTEGER DEFAULT 0,
                send_fan_count INTEGER DEFAULT 0,
                appmsg_album_id TEXT DEFAULT '',
                downloaded INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                PRIMARY KEY (fakeid, aid)
            );
            INSERT OR IGNORE INTO articles_new SELECT * FROM articles;
            DROP TABLE articles;
            ALTER TABLE articles_new RENAME TO articles;
        """)
        conn.execute("PRAGMA foreign_keys=ON")
        # 重建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_fakeid ON articles(fakeid)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_create_time ON articles(create_time)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_fakeid_time ON articles(fakeid, create_time)")

    conn.commit()
    conn.close()


def api_get(path, params=None, need_auth=True):
    """调用 API"""
    cfg = read_config()
    base_url = cfg.get("base_url", "").rstrip("/")
    if not base_url:
        print(f"{RD}错误: base_url 未配置{R}")
        return None
    url = f"{base_url}{path}"
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"
    headers = {}
    if need_auth:
        api_key = cfg.get("api_key", "")
        if api_key:
            headers["X-Auth-Key"] = api_key
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return {"base_resp": {"ret": -1, "err_msg": f"HTTP {e.code}: {body[:200]}"}}
    except Exception as e:
        return {"base_resp": {"ret": -1, "err_msg": str(e)[:200]}}


def check_config():
    """检查配置完整性，返回缺失项列表"""
    cfg = read_config()
    missing = []
    if not cfg.get("base_url"):
        missing.append("base_url")
    if not cfg.get("api_key"):
        missing.append("api_key")
    if not cfg.get("download_dir"):
        missing.append("download_dir")
    if not cfg.get("default_format"):
        missing.append("default_format")
    return missing


def normalize_path(p: str) -> str:
    """路径跨平台转换，兼容 Windows 和 WSL"""
    if not p:
        return p
    # Linux/WSL: D:\xxx 或 D:/xxx → /mnt/d/xxx
    if sys.platform != "win32" and len(p) > 2 and p[1] == ':':
        drive = p[0].lower()
        rest = p[2:].replace('\\', '/')
        return f"/mnt/{drive}{rest}"
    # Windows: /mnt/d/xxx → D:\xxx
    if sys.platform == "win32" and p.startswith("/mnt/"):
        parts = p.split("/")
        if len(parts) > 2 and len(parts[2]) == 1:
            return f"{parts[2].upper()}:\\" + "\\".join(parts[3:])
    return p


def get_download_dir() -> str:
    """获取标准化后的下载目录（自动适配当前运行平台）"""
    cfg = read_config()
    return normalize_path(cfg.get("download_dir", "") or "")


def safe_filename(s):
    """安全文件名"""
    for ch in '/\\:?|*"<>':
        s = s.replace(ch, '_')
    return s


def format_timestamp(ts):
    """格式化时间戳"""
    from datetime import datetime
    if not ts:
        return "unknown"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def format_date(ts):
    """格式化日期"""
    from datetime import datetime
    if not ts:
        return "unknown"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def print_table(headers, rows, widths=None):
    """打印表格"""
    if not widths:
        widths = [len(h) for h in headers]
    header_line = "  ".join(f"{h:<{w}}" for h, w in zip(headers, widths))
    print(header_line)
    print("  " + "-" * len(header_line))
    for row in rows:
        print("  ".join(f"{str(v):<{w}}" for v, w in zip(row, widths)))


def confirm(prompt="确认操作？"):
    """确认操作"""
    ans = input(f"{prompt} (y/N): ").strip().lower()
    return ans == 'y'
