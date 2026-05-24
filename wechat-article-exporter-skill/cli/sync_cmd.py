#!/usr/bin/env python3
# coding: utf-8
"""
同步管理命令
"""
import json
import time
from datetime import datetime
from .utils import (
    get_conn, api_get, format_timestamp, check_config,
    B, R, C, Y, G, GR, RD
)


def run(args):
    """同步文章链接"""
    fakeid = getattr(args, 'fakeid', None)
    latest = getattr(args, 'latest', None)
    date_range = getattr(args, 'range', None)
    sync_all = getattr(args, 'all', False)

    if latest is None and date_range is None and not sync_all:
        latest = 15

    # 检查配置
    missing = check_config()
    if missing:
        print(f"\n  {RD}请先配置: {', '.join(missing)}{R}")
        print(f"  使用: wechat config set <key> <value>")
        return

    conn = get_conn()

    # 确定要同步的公众号
    if fakeid and fakeid != 'all':
        rows = conn.execute("SELECT fakeid, name FROM accounts WHERE fakeid=?", (fakeid,)).fetchall()
        if not rows:
            print(f"\n  {RD}未找到公众号: {fakeid}{R}")
            conn.close()
            return
    else:
        rows = conn.execute("SELECT fakeid, name FROM accounts ORDER BY name").fetchall()

    if not rows:
        print(f"\n  {RD}暂无已关注的公众号{R}")
        conn.close()
        return

    print(f"\n  {B}开始同步文章链接{R}")
    print(f"  {'─' * 50}")

    total_synced = 0
    total_new = 0

    for row in rows:
        fid = row["fakeid"]
        name = row["name"]
        print(f"\n  {Y}{name}{R}")

        if latest:
            count, new = _sync_latest(fid, latest)
        elif date_range:
            from_date, to_date = date_range
            count, new = _sync_range(fid, from_date, to_date)
        else:
            count, new = _sync_all(fid)

        total_synced += count
        total_new += new
        print(f"    同步: {count} 篇, 新增: {new} 篇")
        time.sleep(0.5)

    conn.close()
    print(f"\n  {'─' * 50}")
    print(f"  {GR}同步完成{R}: 共同步 {total_synced} 篇, 新增 {total_new} 篇")


def _sync_latest(fakeid, count):
    """同步最新的N篇"""
    conn = get_conn()
    total_fetched = 0
    new_count = 0
    begin = 0
    size = 20

    while total_fetched < count:
        data = api_get("/api/public/v1/article", {"fakeid": fakeid, "begin": begin, "size": size})
        if data is None:
            break

        articles = data.get("articles", [])
        if not articles:
            break

        for art in articles:
            if total_fetched >= count:
                break
            aid = art.get("aid")
            if not aid:
                continue

            existing = conn.execute("SELECT aid FROM articles WHERE aid=?", (aid,)).fetchone()
            if not existing:
                _save_article(conn, fakeid, art)
                new_count += 1

            total_fetched += 1

        conn.commit()
        begin += size

        if len(articles) < size:
            break
        time.sleep(0.3)

    conn.close()
    return total_fetched, new_count


def _sync_range(fakeid, from_date, to_date=None):
    """同步指定时间段"""
    if to_date is None:
        to_date = datetime.now().strftime("%Y-%m-%d")

    from_ts = int(datetime.strptime(from_date, "%Y-%m-%d").timestamp())
    to_ts = int(datetime.strptime(to_date, "%Y-%m-%d").timestamp()) + 86399

    conn = get_conn()
    total_fetched = 0
    new_count = 0
    begin = 0
    size = 20
    done = False

    while not done:
        data = api_get("/api/public/v1/article", {"fakeid": fakeid, "begin": begin, "size": size})
        if data is None:
            break

        articles = data.get("articles", [])
        if not articles:
            break

        for art in articles:
            ts = art.get("create_time", 0)
            if ts < from_ts:
                done = True
                break
            if ts <= to_ts:
                aid = art.get("aid")
                if aid:
                    existing = conn.execute("SELECT aid FROM articles WHERE aid=?", (aid,)).fetchone()
                    if not existing:
                        _save_article(conn, fakeid, art)
                        new_count += 1
                    total_fetched += 1

        conn.commit()
        begin += size

        if len(articles) < size:
            break
        time.sleep(0.3)

    conn.close()
    return total_fetched, new_count


def _sync_all(fakeid):
    """同步全部文章"""
    conn = get_conn()
    total_fetched = 0
    new_count = 0
    begin = 0
    size = 20

    while True:
        data = api_get("/api/public/v1/article", {"fakeid": fakeid, "begin": begin, "size": size})
        if data is None:
            break

        articles = data.get("articles", [])
        if not articles:
            break

        for art in articles:
            aid = art.get("aid")
            if not aid:
                continue

            existing = conn.execute("SELECT aid FROM articles WHERE aid=?", (aid,)).fetchone()
            if not existing:
                _save_article(conn, fakeid, art)
                new_count += 1

            total_fetched += 1

        conn.commit()
        begin += size
        print(f"    已获取: {total_fetched} 篇...", end='\r')

        if len(articles) < size:
            break
        time.sleep(0.3)

    conn.close()
    return total_fetched, new_count


def _save_article(conn, fakeid, art):
    """保存文章到数据库（全量字段）"""
    conn.execute("""
        INSERT OR IGNORE INTO articles
        (aid, fakeid, title, link, author, digest, create_time, update_time,
         cover, pic_crop_1_1, pic_crop_16_9, is_deleted, is_pay_subscribe,
         is_only_fans, item_show_type, article_type, send_fan_count, appmsg_album_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        art.get("aid"),
        fakeid,
        art.get("title", ""),
        art.get("link", ""),
        art.get("author", art.get("author_name", "")),
        art.get("digest", ""),
        art.get("create_time", 0),
        art.get("update_time", 0),
        art.get("cover", ""),
        art.get("pic_crop_1_1", ""),
        art.get("pic_crop_16_9", ""),
        1 if art.get("is_deleted") else 0,
        1 if art.get("is_pay_subscribe") else 0,
        1 if art.get("is_only_fans") else 0,
        art.get("item_show_type", 0),
        art.get("article_type", 0),
        art.get("send_fan_count", 0),
        str(art.get("appmsg_album_id", "")),
    ))


def check_new(args):
    """检查新文章"""
    fakeid = getattr(args, 'fakeid', None)

    missing = check_config()
    if missing:
        print(f"\n  {RD}请先配置: {', '.join(missing)}{R}")
        return

    conn = get_conn()
    if fakeid:
        accounts = conn.execute("SELECT fakeid, name FROM accounts WHERE fakeid=?", (fakeid,)).fetchall()
    else:
        accounts = conn.execute("SELECT fakeid, name FROM accounts ORDER BY name").fetchall()

    if not accounts:
        print(f"\n  {RD}暂无已关注的公众号{R}")
        conn.close()
        return

    print(f"\n  {B}检查新文章{R}")
    print(f"  {'─' * 50}")

    total_new = 0
    accts_with_new = 0

    for acct in accounts:
        fid = acct["fakeid"]
        name = acct["name"]

        # 找到最新已下载文章的 create_time
        row = conn.execute(
            "SELECT MAX(create_time) AS max_ts FROM articles WHERE fakeid=? AND downloaded=1",
            (fid,)
        ).fetchone()
        threshold = row["max_ts"]
        if threshold is None:
            continue

        # 查找新文章
        new_articles = []
        begin = 0
        size = 20
        done = False

        while not done:
            data = api_get("/api/public/v1/article", {"fakeid": fid, "begin": begin, "size": size})
            if data is None:
                break

            articles = data.get("articles", [])
            if not articles:
                break

            for art in articles:
                ts = art.get("create_time", 0)
                if ts > threshold:
                    new_articles.append(art)
                else:
                    done = True
                    break

            if len(articles) < size:
                done = True
            begin += size
            time.sleep(0.3)

        if new_articles:
            accts_with_new += 1
            total_new += len(new_articles)
            print(f"\n  {Y}{name}{R}: {len(new_articles)} 篇新文章")
            for art in new_articles[:5]:
                title = art.get("title", "")[:40]
                ts = format_timestamp(art.get("create_time", 0))[:10]
                print(f"    {ts} {title}")
            if len(new_articles) > 5:
                print(f"    ... 还有 {len(new_articles) - 5} 篇")

    conn.close()
    print(f"\n  {'─' * 50}")
    print(f"  共 {total_new} 篇新文章, 涉及 {accts_with_new} 个公众号")
