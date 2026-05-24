#!/usr/bin/env python3
# coding: utf-8
"""
文章查询命令
"""
from datetime import datetime
from .utils import get_conn, format_timestamp, format_date, B, R, Y, G, GR, RD


def list_articles(args):
    """列出已同步文章"""
    fakeid = getattr(args, 'fakeid', None)
    page = getattr(args, 'page', 1)
    size = getattr(args, 'size', 20)

    conn = get_conn()

    if fakeid and fakeid != 'all':
        total = conn.execute("SELECT COUNT(*) FROM articles WHERE fakeid=?", (fakeid,)).fetchone()[0]
        rows = conn.execute("""
            SELECT a.*, ac.name as account_name
            FROM articles a
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            WHERE a.fakeid=?
            ORDER BY a.create_time DESC LIMIT ? OFFSET ?
        """, (fakeid, size, (page - 1) * size)).fetchall()
    else:
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        rows = conn.execute("""
            SELECT a.*, ac.name as account_name
            FROM articles a
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            ORDER BY a.create_time DESC LIMIT ? OFFSET ?
        """, (size, (page - 1) * size)).fetchall()

    conn.close()

    pages = (total + size - 1) // size if total else 0

    print(f"\n  {B}文章列表{R} (共 {total} 篇, 第 {page}/{pages} 页)")
    print(f"  {'─' * 80}")

    if not rows:
        print(f"  {G}暂无文章{R}")
        return

    print(f"  {'日期':12s} {'状态':6s} {'公众号':15s} {'标题'}")
    print(f"  {'─' * 80}")

    for r in rows:
        ts = format_date(r["create_time"])[:10] if r["create_time"] else "unknown"
        status = ""
        if r["downloaded"]:
            status += f"{GR}✓{R}"
        if r["is_pay_subscribe"]:
            status += f"💰"
        status = status or "  "
        acct = (r["account_name"] or "")[:13]
        title = r["title"][:45]
        print(f"  {ts:12s} {status:6s} {acct:15s} {title}")

    print()


def latest(args):
    """最新N篇"""
    fakeid = getattr(args, 'fakeid', None)
    count = getattr(args, 'count', 5)

    conn = get_conn()

    if fakeid and fakeid != 'all':
        rows = conn.execute("""
            SELECT a.*, ac.name as account_name
            FROM articles a
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            WHERE a.fakeid=?
            ORDER BY a.create_time DESC LIMIT ?
        """, (fakeid, count)).fetchall()
    else:
        rows = conn.execute("""
            SELECT a.*, ac.name as account_name
            FROM articles a
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            ORDER BY a.create_time DESC LIMIT ?
        """, (count,)).fetchall()

    conn.close()

    print(f"\n  {B}最新 {count} 篇文章{R}")
    print(f"  {'─' * 80}")

    if not rows:
        print(f"  {G}暂无文章{R}")
        return

    print(f"  {'日期':12s} {'状态':6s} {'公众号':15s} {'标题'}")
    print(f"  {'─' * 80}")

    for r in rows:
        ts = format_date(r["create_time"])[:10] if r["create_time"] else "unknown"
        status = ""
        if r["downloaded"]:
            status += f"{GR}✓{R}"
        if r["is_pay_subscribe"]:
            status += f"💰"
        status = status or "  "
        acct = (r["account_name"] or "")[:13]
        title = r["title"][:45]
        print(f"  {ts:12s} {status:6s} {acct:15s} {title}")

    print()


def search(args):
    """搜索文章标题"""
    keyword = args.keyword
    fakeid = getattr(args, 'fakeid', None)

    conn = get_conn()

    if fakeid:
        rows = conn.execute("""
            SELECT a.*, ac.name as account_name
            FROM articles a
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            WHERE a.fakeid=? AND a.title LIKE ?
            ORDER BY a.create_time DESC LIMIT 50
        """, (fakeid, f"%{keyword}%")).fetchall()
    else:
        rows = conn.execute("""
            SELECT a.*, ac.name as account_name
            FROM articles a
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            WHERE a.title LIKE ?
            ORDER BY a.create_time DESC LIMIT 50
        """, (f"%{keyword}%",)).fetchall()

    conn.close()

    if not rows:
        print(f"\n  未找到包含「{keyword}」的文章")
        return

    print(f"\n  {B}搜索结果{R} (共 {len(rows)} 篇)")
    print(f"  {'─' * 80}")

    print(f"  {'日期':12s} {'状态':6s} {'公众号':15s} {'标题'}")
    print(f"  {'─' * 80}")

    for r in rows:
        ts = format_date(r["create_time"])[:10] if r["create_time"] else "unknown"
        status = ""
        if r["downloaded"]:
            status += f"{GR}✓{R}"
        if r["is_pay_subscribe"]:
            status += f"💰"
        status = status or "  "
        acct = (r["account_name"] or "")[:13]
        title = r["title"][:45]
        print(f"  {ts:12s} {status:6s} {acct:15s} {title}")

    print()


def range_articles(args):
    """时间范围筛选"""
    fakeid = args.fakeid
    date_from = args.date_from
    date_to = getattr(args, 'date_to', None)

    if date_to is None:
        date_to = datetime.now().strftime("%Y-%m-%d")

    from_ts = int(datetime.strptime(date_from, "%Y-%m-%d").timestamp())
    to_ts = int(datetime.strptime(date_to, "%Y-%m-%d").timestamp()) + 86399

    conn = get_conn()
    rows = conn.execute("""
        SELECT a.*, ac.name as account_name
        FROM articles a
        LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
        WHERE a.fakeid=? AND a.create_time BETWEEN ? AND ?
        ORDER BY a.create_time DESC
    """, (fakeid, from_ts, to_ts)).fetchall()
    conn.close()

    print(f"\n  {B}时间范围: {date_from} ~ {date_to}{R}")
    print(f"  {'─' * 80}")

    if not rows:
        print(f"  {G}该时间段内暂无文章{R}")
        return

    print(f"  {'日期':12s} {'状态':6s} {'公众号':15s} {'标题'}")
    print(f"  {'─' * 80}")

    for r in rows:
        ts = format_date(r["create_time"])[:10] if r["create_time"] else "unknown"
        status = ""
        if r["downloaded"]:
            status += f"{GR}✓{R}"
        if r["is_pay_subscribe"]:
            status += f"💰"
        status = status or "  "
        acct = (r["account_name"] or "")[:13]
        title = r["title"][:45]
        print(f"  {ts:12s} {status:6s} {acct:15s} {title}")

    print()


def undownloaded(args):
    """列出未下载文章"""
    fakeid = getattr(args, 'fakeid', None)

    conn = get_conn()

    if fakeid and fakeid != 'all':
        rows = conn.execute("""
            SELECT a.*, ac.name as account_name
            FROM articles a
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            WHERE a.fakeid=? AND a.downloaded=0
            ORDER BY a.create_time DESC
        """, (fakeid,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT a.*, ac.name as account_name
            FROM articles a
            LEFT JOIN accounts ac ON a.fakeid=ac.fakeid
            WHERE a.downloaded=0
            ORDER BY a.create_time DESC
        """).fetchall()

    conn.close()

    print(f"\n  {B}未下载文章{R} (共 {len(rows)} 篇)")
    print(f"  {'─' * 80}")

    if not rows:
        print(f"  {GR}所有文章均已下载{R}")
        return

    print(f"  {'日期':12s} {'💰':4s} {'公众号':15s} {'标题'}")
    print(f"  {'─' * 80}")

    for r in rows:
        ts = format_date(r["create_time"])[:10] if r["create_time"] else "unknown"
        pay = "💰" if r["is_pay_subscribe"] else "  "
        acct = (r["account_name"] or "")[:13]
        title = r["title"][:45]
        print(f"  {ts:12s} {pay:4s} {acct:15s} {title}")

    print()
