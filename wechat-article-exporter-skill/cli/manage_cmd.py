#!/usr/bin/env python3
# coding: utf-8
"""
数据库管理命令
"""
import json
import os
import shutil
from pathlib import Path
from .utils import (
    read_config, write_config, get_conn, format_timestamp, format_date,
    confirm, check_config, get_download_dir,
    B, R, Y, G, GR, RD
)


def stats(args=None):
    """统计信息"""
    conn = get_conn()

    account_count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    article_count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    pay_count = conn.execute("SELECT COUNT(*) FROM articles WHERE is_pay_subscribe=1").fetchone()[0]
    downloaded_count = conn.execute("SELECT COUNT(*) FROM articles WHERE downloaded=1").fetchone()[0]
    download_records = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]

    # 公众号详情
    account_detail = conn.execute("""
        SELECT a.name,
               (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid) AS total,
               (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid AND is_pay_subscribe=1) AS pay,
               (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid AND downloaded=1) AS done
        FROM accounts a ORDER BY total DESC
    """).fetchall()

    conn.close()

    print(f"\n  {B}统计信息{R}")
    print(f"  {'─' * 50}")
    print(f"  公众号: {Y}{account_count}{R}")
    print(f"  文章:   {Y}{article_count}{R}")
    print(f"  付费:   {Y}{pay_count}{R}")
    print(f"  已下载: {Y}{downloaded_count}{R}")
    print(f"  下载记录: {Y}{download_records}{R}")

    if account_detail:
        print(f"\n  {B}公众号详情{R}")
        print(f"  {'─' * 60}")
        print(f"  {'公众号':24s} {'文章':>6s} {'付费':>4s} {'已下载':>6s} {'进度'}")
        print(f"  {'─' * 60}")

        for r in account_detail:
            pct = f"{r['done']/r['total']*100:.0f}%" if r['total'] else "0%"
            pay_str = f"💰{r['pay']}" if r['pay'] else ""
            print(f"  {r['name'][:22]:24s} {r['total']:6d} {r['pay']:4d} {r['done']:6d} {pct:>6s} {pay_str}")

    print()


def list_accounts(args=None):
    """列出公众号所有信息"""
    fakeid = getattr(args, 'fakeid', None)

    conn = get_conn()

    if fakeid and fakeid != 'all':
        rows = conn.execute("""
            SELECT a.*,
                   (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid) AS article_count,
                   (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid AND downloaded=1) AS downloaded_count,
                   (SELECT COUNT(*) FROM downloads d JOIN articles art ON d.aid=art.aid WHERE art.fakeid=a.fakeid) AS dl_records
            FROM accounts a WHERE a.fakeid=?
        """, (fakeid,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT a.*,
                   (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid) AS article_count,
                   (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid AND downloaded=1) AS downloaded_count,
                   (SELECT COUNT(*) FROM downloads d JOIN articles art ON d.aid=art.aid WHERE art.fakeid=a.fakeid) AS dl_records
            FROM accounts a ORDER BY a.created_at DESC
        """).fetchall()

    conn.close()

    if not rows:
        print(f"\n  {G}暂无公众号{R}")
        return

    print(f"\n  {B}公众号信息{R} (共 {len(rows)} 个)")
    print(f"  {'─' * 80}")

    for r in rows:
        print(f"\n  {Y}{r['name']}{R}")
        print(f"    fakeid:    {r['fakeid']}")
        print(f"    类型:      {'服务号' if r['service_type'] == 1 else '订阅号'}")
        print(f"    简介:      {r['description'] or '(无)'}")
        print(f"    地区:      {r['province']} {r['city']} {r['country']}")
        print(f"    文章:      {r['article_count']} 篇")
        print(f"    已下载:    {r['downloaded_count']} 篇")
        print(f"    下载记录:  {r['dl_records']} 条")
        print(f"    自动扫描:  {'是' if r['auto_scan'] else '否'}")
        print(f"    创建时间:  {r['created_at'] or '(无)'}")
        print(f"    更新时间:  {r['updated_at'] or '(无)'}")

    print()


def import_accounts(args):
    """导入公众号.json"""
    file_path = args.file
    fp = Path(file_path)
    if not fp.exists():
        print(f"\n  {RD}文件不存在: {file_path}{R}")
        return

    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)

    accounts = data.get("accounts", [])
    if not accounts:
        print(f"\n  {RD}无公众号数据{R}")
        return

    conn = get_conn()
    existing = set(r["fakeid"] for r in conn.execute("SELECT fakeid FROM accounts").fetchall())

    added = 0
    updated = 0

    for acct in accounts:
        fid = acct.get("fakeid", "")
        name = acct.get("nickname", "")
        if not fid:
            continue

        if fid in existing:
            # 更新
            conn.execute("""
                UPDATE accounts SET name=?, description=?, round_head_img=?,
                service_type=?, updated_at=datetime('now', 'localtime')
                WHERE fakeid=?
            """, (name, acct.get("signature", ""), acct.get("round_head_img", ""),
                  acct.get("service_type", 0), fid))
            updated += 1
        else:
            # 新增
            conn.execute("""
                INSERT INTO accounts (fakeid, name, description, round_head_img, service_type)
                VALUES (?, ?, ?, ?, ?)
            """, (fid, name, acct.get("signature", ""), acct.get("round_head_img", ""),
                  acct.get("service_type", 0)))
            added += 1

    conn.commit()
    conn.close()

    print(f"\n  {GR}导入完成{R}: 新增 {added}, 更新 {updated}")


def export_accounts(args):
    """导出公众号.json"""
    file_path = args.file if args.file else "公众号.json"

    conn = get_conn()
    rows = conn.execute("""
        SELECT a.*,
               (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid) AS count,
               (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid) AS articles,
               (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid AND downloaded=1) AS total_count
        FROM accounts a ORDER BY a.created_at DESC
    """).fetchall()
    conn.close()

    if not rows:
        print(f"\n  {G}暂无公众号数据{R}")
        return

    accounts = []
    for r in rows:
        accounts.append({
            "fakeid": r["fakeid"],
            "nickname": r["name"],
            "round_head_img": r["round_head_img"],
            "signature": r["description"],
            "service_type": r["service_type"],
            "count": r["count"],
            "articles": r["articles"],
            "total_count": r["total_count"],
            "create_time": r["created_at"],
            "update_time": r["updated_at"],
        })

    data = {
        "version": "2.0",
        "usefor": "wechat-article-exporter",
        "accounts": accounts,
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  {GR}已导出 {len(accounts)} 个公众号到: {file_path}{R}")


def unfollow(args):
    """取消关注并删除数据"""
    fakeid = args.fakeid
    delete_files = getattr(args, 'delete_files', False)

    conn = get_conn()
    row = conn.execute("SELECT name FROM accounts WHERE fakeid=?", (fakeid,)).fetchone()
    if not row:
        print(f"\n  {RD}未找到公众号: {fakeid}{R}")
        conn.close()
        return

    name = row["name"]
    print(f"\n  确定取消关注 [{Y}{name}{R}]？")
    print(f"  注意：该操作会删除该公众号的所有文章和下载记录！")

    if not confirm("  确认取消关注"):
        conn.close()
        return

    # 删除已下载文件
    if delete_files:
        cfg = read_config()
        dl_dir = get_download_dir()
        if dl_dir:
            rows = conn.execute("""
                SELECT d.file_path FROM downloads d
                JOIN articles a ON d.aid=a.aid
                WHERE a.fakeid=?
            """, (fakeid,)).fetchall()

            deleted = 0
            for r in rows:
                fp = os.path.join(dl_dir, r["file_path"])
                if os.path.exists(fp):
                    os.remove(fp)
                    deleted += 1

            # 删除目录
            dir_path = os.path.join(dl_dir, name)
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except:
                    pass

            print(f"  已删除 {deleted} 个文件")

    # 删除数据库记录
    conn.execute("DELETE FROM accounts WHERE fakeid=?", (fakeid,))
    conn.commit()
    conn.close()

    print(f"\n  {GR}已取消关注: {name}{R}")


def scan(args=None):
    """扫描库存更新"""
    auto = getattr(args, 'auto', False) if args else False

    if auto:
        cfg = read_config()
        auto_scan = cfg.get("auto_scan", True)
        print(f"\n  自动扫描: {'开启' if auto_scan else '关闭'}")
        if input("  切换状态? (y/N): ").strip().lower() == 'y':
            cfg["auto_scan"] = not auto_scan
            write_config(cfg)
            print(f"  已{'开启' if cfg['auto_scan'] else '关闭'}自动扫描")
        return

    cfg = read_config()
    dl_dir = get_download_dir()
    if not dl_dir:
        print(f"\n  {RD}请先配置 download_dir{R}")
        return

    if not os.path.exists(dl_dir):
        print(f"\n  {RD}下载目录不存在: {dl_dir}{R}")
        return

    conn = get_conn()
    accounts = conn.execute("SELECT fakeid, name FROM accounts ORDER BY name").fetchall()

    print(f"\n  {B}扫描库存{R}")
    print(f"  {'─' * 50}")

    total_found = 0
    total_new = 0

    for acct in accounts:
        fid = acct["fakeid"]
        name = acct["name"]
        dir_path = os.path.join(dl_dir, name)

        if not os.path.exists(dir_path):
            # 目录不存在，清理该公众号的所有下载记录
            db_paths = conn.execute("""
                SELECT d.id, d.aid, d.file_path
                FROM downloads d
                JOIN articles a ON d.aid = a.aid
                WHERE a.fakeid = ?
            """, (fid,)).fetchall()
            
            deleted_count = 0
            for row in db_paths:
                conn.execute("DELETE FROM downloads WHERE id=?", (row["id"],))
                deleted_count += 1
                # 检查该文章是否还有其他格式的下载
                remaining = conn.execute(
                    "SELECT COUNT(*) FROM downloads WHERE aid=?", (row["aid"],)
                ).fetchone()[0]
                if remaining == 0:
                    conn.execute("UPDATE articles SET downloaded=0 WHERE aid=?", (row["aid"],))
            
            if deleted_count > 0:
                conn.commit()
                print(f"  {Y}{name}{R}: 目录不存在，清理 {deleted_count} 条失效记录")
            continue

        # 扫描目录中的文件
        # 扫描目录中的文件
        found = 0
        new = 0
        deleted = 0
        valid_paths = set()  # 该公众号目录下所有有效的文件路径

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.startswith('.'):
                    continue
                found += 1
                total_found += 1

                # 检查是否已记录
                relpath = os.path.relpath(os.path.join(root, file), dl_dir).replace('\\', '/')
                valid_paths.add(relpath)
                existing = conn.execute("""
                    SELECT id FROM downloads WHERE file_path=?
                """, (relpath,)).fetchone()

                if not existing:
                    # 尝试匹配文章
                    # 文件名格式：日期.标题.扩展名
                    parts = file.rsplit('.', 2)
                    if len(parts) >= 2:
                        title_part = parts[-2] if len(parts) >= 3 else parts[0]
                        # 查找匹配的文章
                        article = conn.execute("""
                            SELECT aid FROM articles
                            WHERE fakeid=? AND title LIKE ?
                            LIMIT 1
                        """, (fid, f"%{title_part}%")).fetchone()

                        if article:
                            ext = parts[-1]
                            fmt_map = {"html": "html", "md": "markdown", "txt": "text", "json": "json"}
                            fmt = fmt_map.get(ext, ext)

                            conn.execute("""
                                INSERT OR IGNORE INTO downloads (aid, format, file_path)
                                VALUES (?, ?, ?)
                            """, (article["aid"], fmt, relpath))
                            conn.execute("""
                                UPDATE articles SET downloaded=1 WHERE aid=?
                            """, (article["aid"],))
                            new += 1
                            total_new += 1

        # 清理已删除文件的记录
        db_paths = conn.execute("""
            SELECT d.id, d.aid, d.file_path
            FROM downloads d
            JOIN articles a ON d.aid = a.aid
            WHERE a.fakeid = ?
        """, (fid,)).fetchall()

        for row in db_paths:
            if row["file_path"] not in valid_paths:
                # 文件已删除，清理记录
                conn.execute("DELETE FROM downloads WHERE id=?", (row["id"],))
                deleted += 1
                # 检查该文章是否还有其他格式的下载
                remaining = conn.execute(
                    "SELECT COUNT(*) FROM downloads WHERE aid=?", (row["aid"],)
                ).fetchone()[0]
                if remaining == 0:
                    conn.execute("UPDATE articles SET downloaded=0 WHERE aid=?", (row["aid"],))

        if new > 0 or deleted > 0:
            conn.commit()
            if new > 0 and deleted > 0:
                print(f"  {Y}{name}{R}: 发现 {found} 个文件，新增 {new} 条，清理 {deleted} 条")
            elif new > 0:
                print(f"  {Y}{name}{R}: 发现 {found} 个文件，新增记录 {new}")
            else:
                print(f"  {Y}{name}{R}: 清理 {deleted} 条失效记录")

    conn.close()
    print(f"\n  {'─' * 50}")
    print(f"  {GR}扫描完成{R}: 发现 {total_found} 个文件, 新增记录 {total_new}")


def clear_downloads(args=None):
    """清空下载记录"""
    yes = getattr(args, 'yes', False) if args else False

    conn = get_conn()

    download_count = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
    article_count = conn.execute("SELECT COUNT(*) FROM articles WHERE downloaded=1").fetchone()[0]

    print(f"\n  {B}清空下载记录{R}")
    print(f"  {'─' * 50}")
    print(f"  下载记录: {Y}{download_count}{R} 条")
    print(f"  已下载文章: {Y}{article_count}{R} 篇")

    if download_count == 0:
        print(f"\n  {G}无下载记录{R}")
        conn.close()
        return

    if not yes and not confirm("\n  确认清空所有下载记录？"):
        conn.close()
        return

    # 清空下载记录
    conn.execute("DELETE FROM downloads")
    # 重置文章下载状态
    conn.execute("UPDATE articles SET downloaded=0")
    conn.commit()
    conn.close()

    print(f"\n  {GR}已清空 {download_count} 条下载记录{R}")
    print(f"  {G}提示: 如需删除实际文件，请手动删除 downloads 目录{R}")
