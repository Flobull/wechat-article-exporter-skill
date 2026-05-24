#!/usr/bin/env python3
# coding: utf-8
"""
下载管理命令
"""
import json
import os
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from .utils import (
    read_config, get_conn, safe_filename, format_date,
    check_config, confirm, get_download_dir,
    B, R, Y, G, GR, RD
)

# 最小有效文件大小（字节），低于此值视为无效
MIN_VALID_SIZE = 0


def _download_with_retry(url, filepath, max_retries=3, timeout=60):
    """带重试机制的下载函数"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    last_error = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                content = resp.read()

                # 验证内容大小
                if len(content) < MIN_VALID_SIZE:
                    raise Exception(f"内容过小 ({len(content)} 字节)")

                # 写入文件
                with open(filepath, "wb") as f:
                    f.write(content)

                return len(content)

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                time.sleep(wait_time)

    raise last_error


def _validate_file(filepath, min_size=MIN_VALID_SIZE):
    """验证下载的文件是否有效"""
    if not os.path.exists(filepath):
        return False, "文件不存在"

    file_size = os.path.getsize(filepath)
    if file_size < min_size:
        return False, f"文件过小 ({file_size} 字节)"

    # 检查文件内容是否为错误信息
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(500)
            if '"base_resp"' in content and '"ret"' in content and '"err_msg"' in content:
                return False, "API返回错误"
    except:
        pass

    return True, f"有效 ({file_size} 字节)"


def article(args):
    """下载单篇文章"""
    url = args.url
    fmt = getattr(args, 'fmt', None)
    out_dir = getattr(args, 'dir', None)
    out_name = getattr(args, 'out', None)

    cfg = read_config()
    base_url = cfg.get("base_url", "").rstrip("/")
    if not base_url:
        print(f"\n  {RD}请先配置 base_url{R}")
        return

    if not fmt:
        fmt = cfg.get("default_format", "markdown,html,text") or "markdown,html,text"
    if not out_dir:
        out_dir = get_download_dir() or "."

    os.makedirs(out_dir, exist_ok=True)

    fmt_list = [f.strip() for f in fmt.split(",")]
    ext_map = {"html": "html", "markdown": "md", "text": "txt", "json": "json"}

    encoded_url = urllib.parse.quote(url, safe="")

    print(f"\n  {B}下载文章{R}")
    print(f"  {'─' * 50}")

    success = 0
    fail = 0
    invalid = 0

    for fmt in fmt_list:
        ext = ext_map.get(fmt, fmt)
        download_url = f"{base_url}/api/public/v1/download?url={encoded_url}&format={fmt}"
        filename = f"{out_name}.{ext}" if out_name else f"article.{ext}"
        filepath = os.path.join(out_dir, filename)

        try:
            file_size = _download_with_retry(download_url, filepath)

            # 验证文件
            is_valid, msg = _validate_file(filepath)
            if is_valid:
                print(f"  {GR}✓{R} {fmt}: {filepath} ({file_size} 字节)")
                success += 1
            else:
                print(f"  {RD}✗{R} {fmt}: {msg}")
                os.remove(filepath)
                invalid += 1

        except Exception as e:
            print(f"  {RD}✗{R} {fmt}: {str(e)[:60]}")
            fail += 1

    print(f"\n  完成: 成功 {success}, 失败 {fail}, 无效 {invalid}")


def batch(args):
    """批量下载"""
    fakeid = getattr(args, 'fakeid', None)
    latest = getattr(args, 'latest', None)
    date_range = getattr(args, 'range', None)
    sync_all = getattr(args, 'all', False)
    fmt = getattr(args, 'fmt', None)

    if latest is None and date_range is None and not sync_all:
        latest = 15
    overwrite = getattr(args, 'overwrite', False)

    cfg = read_config()
    base_url = cfg.get("base_url", "").rstrip("/")
    if not base_url:
        print(f"\n  {RD}请先配置 base_url{R}")
        return

    if not fmt:
        fmt = cfg.get("default_format", "markdown,html,text") or "markdown,html,text"
    dl_dir = get_download_dir() or "."
    dir_structure = cfg.get("dir_structure", "account")  # account/date/flat

    conn = get_conn()

    # 确定要下载的公众号
    if fakeid and fakeid != 'all':
        accounts = conn.execute("SELECT fakeid, name FROM accounts WHERE fakeid=?", (fakeid,)).fetchall()
    else:
        accounts = conn.execute("SELECT fakeid, name FROM accounts ORDER BY name").fetchall()

    if not accounts:
        print(f"\n  {RD}暂无已关注的公众号{R}")
        conn.close()
        return

    # 统计总文章数
    total_articles = 0
    for acct in accounts:
        fid = acct["fakeid"]
        if latest:
            count = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE fakeid=?",
                (fid,)
            ).fetchone()[0]
            total_articles += min(count, latest)
        elif date_range:
            from_date, to_date = date_range
            from_ts = int(datetime.strptime(from_date, "%Y-%m-%d").timestamp())
            to_ts = int(datetime.strptime(to_date, "%Y-%m-%d").timestamp()) + 86399
            count = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE fakeid=? AND create_time BETWEEN ? AND ?",
                (fid, from_ts, to_ts)
            ).fetchone()[0]
            total_articles += count
        else:
            count = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE fakeid=?",
                (fid,)
            ).fetchone()[0]
            total_articles += count

    fmt_list = [f.strip() for f in fmt.split(",")]

    print(f"\n  {B}批量下载文章{R}")
    print(f"  格式: {fmt}")
    print(f"  目录: {dl_dir}")
    print(f"  结构: {dir_structure}")
    print(f"  预计: {total_articles} 篇文章 × {len(fmt_list)} 种格式")
    print(f"  {'─' * 50}")

    ext_map = {"html": "html", "markdown": "md", "text": "txt", "json": "json"}
    total_ok = 0
    total_fail = 0
    total_skip = 0
    total_invalid = 0

    for i, acct in enumerate(accounts, 1):
        fid = acct["fakeid"]
        name = acct["name"]
        print(f"\n  [{i}/{len(accounts)}] {Y}{name}{R}")

        # 获取要下载的文章
        if latest:
            rows = conn.execute("""
                SELECT * FROM articles WHERE fakeid=?
                ORDER BY create_time DESC LIMIT ?
            """, (fid, latest)).fetchall()
        elif date_range:
            from_date, to_date = date_range
            from_ts = int(datetime.strptime(from_date, "%Y-%m-%d").timestamp())
            to_ts = int(datetime.strptime(to_date, "%Y-%m-%d").timestamp()) + 86399
            rows = conn.execute("""
                SELECT * FROM articles
                WHERE fakeid=? AND create_time BETWEEN ? AND ?
                ORDER BY create_time DESC
            """, (fid, from_ts, to_ts)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM articles WHERE fakeid=?
                ORDER BY create_time DESC
            """, (fid,)).fetchall()

        if not rows:
            print(f"    无文章")
            continue

        acct_ok = 0
        acct_fail = 0
        acct_skip = 0
        acct_invalid = 0

        for j, row in enumerate(rows, 1):
            aid = row["aid"]
            title = row["title"]
            link = row["link"]

            if not link:
                acct_skip += 1
                continue

            safe_title = safe_filename(title)
            date_str = format_date(row["create_time"])[:10]
            out_name = f"{date_str}.{safe_title}"

            # 确定输出目录
            if dir_structure == "date":
                dir_path = os.path.join(dl_dir, date_str, name)
            elif dir_structure == "flat":
                dir_path = dl_dir
            else:  # account (默认)
                dir_path = os.path.join(dl_dir, name)

            os.makedirs(dir_path, exist_ok=True)

            for fmt_single in fmt_list:
                fmt_single = fmt_single.strip()
                ext = ext_map.get(fmt_single, fmt_single)

                # 检查是否已下载
                existing = conn.execute("""
                    SELECT id, file_path FROM downloads WHERE aid=? AND format=?
                """, (aid, fmt_single)).fetchone()

                if existing and not overwrite:
                    acct_skip += 1
                    continue

                # 如果覆盖，删除旧记录和文件
                if existing and overwrite:
                    old_filepath = os.path.join(dl_dir, existing["file_path"])
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)
                    conn.execute("DELETE FROM downloads WHERE id=?", (existing["id"],))
                    conn.commit()

                # 下载
                encoded_url = urllib.parse.quote(link, safe="")
                download_url = f"{base_url}/api/public/v1/download?url={encoded_url}&format={fmt_single}"
                filename = f"{out_name}.{ext}"
                filepath = os.path.join(dir_path, filename)

                # 显示进度
                progress = f"[{i}/{len(accounts)}:{j}/{len(rows)}]"
                print(f"    {progress} {fmt_single}: {title[:25]}...", end="", flush=True)

                try:
                    file_size = _download_with_retry(download_url, filepath)

                    # 验证文件
                    is_valid, msg = _validate_file(filepath)
                    if not is_valid:
                        print(f" {RD}✗{R} {msg}")
                        os.remove(filepath)
                        acct_invalid += 1
                        continue

                    # 记录下载
                    relpath = os.path.relpath(filepath, dl_dir).replace('\\', '/')
                    conn.execute("""
                        INSERT OR IGNORE INTO downloads (aid, format, file_path, file_size)
                        VALUES (?, ?, ?, ?)
                    """, (aid, fmt_single, relpath, file_size))
                    conn.execute("UPDATE articles SET downloaded=1 WHERE aid=?", (aid,))
                    conn.commit()

                    acct_ok += 1
                    print(f" {GR}✓{R} ({file_size} 字节)")

                except Exception as e:
                    print(f" {RD}✗{R} {str(e)[:30]}")
                    acct_fail += 1

        total_ok += acct_ok
        total_fail += acct_fail
        total_skip += acct_skip
        total_invalid += acct_invalid
        print(f"    成功: {acct_ok}, 失败: {acct_fail}, 跳过: {acct_skip}, 无效: {acct_invalid}")

    conn.close()
    print(f"\n  {'─' * 50}")
    print(f"  {GR}下载完成{R}: 成功 {total_ok}, 失败 {total_fail}, 跳过 {total_skip}, 无效 {total_invalid}")


def list_downloads(args):
    """列出下载记录"""
    fakeid = getattr(args, 'fakeid', None)

    conn = get_conn()

    if fakeid and fakeid != 'all':
        rows = conn.execute("""
            SELECT d.*, a.title, a.fakeid, ac.name as account_name
            FROM downloads d
            JOIN articles a ON d.aid=a.aid
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            WHERE a.fakeid=?
            ORDER BY d.downloaded_at DESC
        """, (fakeid,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT d.*, a.title, a.fakeid, ac.name as account_name
            FROM downloads d
            JOIN articles a ON d.aid=a.aid
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            ORDER BY d.downloaded_at DESC
        """).fetchall()

    conn.close()

    print(f"\n  {B}下载记录{R} (共 {len(rows)} 条)")
    print(f"  {'─' * 80}")

    if not rows:
        print(f"  {G}暂无下载记录{R}")
        return

    print(f"  {'格式':8s} {'大小':>10s} {'时间':12s} {'公众号':15s} {'标题'}")
    print(f"  {'─' * 80}")

    for r in rows[:50]:
        fmt = r["format"]
        size = f"{r['file_size']:,}" if r["file_size"] else "?"
        tm = (r["downloaded_at"] or "")[:10]
        acct = (r["account_name"] or "")[:13]
        title = r["title"][:25] if r["title"] else ""
        print(f"  {fmt:8s} {size:>10s} {tm:12s} {acct:15s} {title}")

    if len(rows) > 50:
        print(f"\n  ... 还有 {len(rows) - 50} 条记录")

    print()


def verify(args):
    """校验文件完整性"""
    fakeid = getattr(args, 'fakeid', None)
    repair = getattr(args, 'repair', False)

    cfg = read_config()
    dl_dir = get_download_dir()
    if not dl_dir:
        print(f"\n  {RD}请先配置 download_dir{R}")
        return

    conn = get_conn()

    if fakeid and fakeid != 'all':
        rows = conn.execute("""
            SELECT d.*, a.title
            FROM downloads d
            JOIN articles a ON d.aid=a.aid
            WHERE a.fakeid=?
            ORDER BY d.downloaded_at DESC
        """, (fakeid,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT d.*, a.title
            FROM downloads d
            JOIN articles a ON d.aid=a.aid
            ORDER BY d.downloaded_at DESC
        """).fetchall()

    print(f"\n  {B}校验文件完整性{R}")
    print(f"  {'─' * 50}")

    checked = 0
    ok_count = 0
    missing = []
    invalid = []

    for r in rows:
        checked += 1
        fp = os.path.join(dl_dir, r["file_path"])

        if not os.path.exists(fp):
            missing.append((r["id"], r["aid"], r["format"], r["file_path"], r["title"]))
            continue

        is_valid, msg = _validate_file(fp)
        if is_valid:
            ok_count += 1
        else:
            invalid.append((r["id"], r["aid"], r["format"], r["file_path"], r["title"], msg))

    print(f"  已检查: {checked} 条记录")
    print(f"  {GR}正常: {ok_count}{R}")

    if missing:
        print(f"  {RD}缺失: {len(missing)}{R}")
        print(f"\n  缺失文件:")
        for _, _, fmt, relpath, title in missing[:10]:
            print(f"    {fmt}: {title[:40]}")
        if len(missing) > 10:
            print(f"    ... 还有 {len(missing) - 10} 个文件")

    if invalid:
        print(f"  {RD}无效: {len(invalid)}{R}")
        print(f"\n  无效文件:")
        for _, _, fmt, relpath, title, msg in invalid[:10]:
            print(f"    {fmt}: {title[:30]} - {msg}")
        if len(invalid) > 10:
            print(f"    ... 还有 {len(invalid) - 10} 个文件")

    # 修复选项
    if repair and (missing or invalid):
        print(f"\n  {B}修复记录{R}")
        if not confirm("  确认删除无效的下载记录？"):
            conn.close()
            return

        fixed = 0
        for id_, aid, _, _, _ in missing:
            conn.execute("DELETE FROM downloads WHERE id=?", (id_,))
            # 检查是否还有其他格式的下载
            remaining = conn.execute(
                "SELECT COUNT(*) FROM downloads WHERE aid=?", (aid,)
            ).fetchone()[0]
            if remaining == 0:
                conn.execute("UPDATE articles SET downloaded=0 WHERE aid=?", (aid,))
            fixed += 1

        for id_, aid, _, _, _, _ in invalid:
            conn.execute("DELETE FROM downloads WHERE id=?", (id_,))
            remaining = conn.execute(
                "SELECT COUNT(*) FROM downloads WHERE aid=?", (aid,)
            ).fetchone()[0]
            if remaining == 0:
                conn.execute("UPDATE articles SET downloaded=0 WHERE aid=?", (aid,))
            fixed += 1

        conn.commit()
        print(f"  {GR}已修复 {fixed} 条记录{R}")

    elif missing or invalid:
        print(f"\n  提示: 使用 --repair 选项可自动修复无效记录")

    conn.close()
    print()
