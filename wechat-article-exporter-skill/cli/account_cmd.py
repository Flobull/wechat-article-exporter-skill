#!/usr/bin/env python3
# coding: utf-8
"""
公众号管理命令
"""
import json
import re
import time
from .utils import (
    read_config, write_config, get_conn, api_get,
    check_config, format_timestamp,
    B, R, C, Y, G, GR, RD
)


def search(args):
    """搜索公众号"""
    keyword = args.keyword
    data = api_get("/api/public/v1/account", {"keyword": keyword})
    if data is None:
        return

    results = data.get("list", [])
    total = data.get("total", len(results))

    if not results:
        print(f"\n  未找到包含「{keyword}」的公众号")
        return

    print(f"\n  {B}搜索结果{R} (共 {total} 个)")
    print(f"  {'─' * 60}")

    for i, r in enumerate(results, 1):
        fid = r.get("fakeid", "")
        name = r.get("nickname", "")
        desc = r.get("signature", "")[:40]
        stype = r.get("service_type", 0)
        stype_str = "服务号" if stype == 1 else "订阅号"
        print(f"  {i:2d}. {Y}{name}{R} ({stype_str})")
        print(f"      fakeid: {fid}")
        if desc:
            print(f"      简介: {desc}")

    print()


def add(args):
    """批量关注公众号"""
    print(f"\n  {B}批量关注公众号{R}")
    print(f"  {'─' * 50}")
    print("  输入方式：")
    print("  1. 粘贴文本（关键词用 , ; 或换行分隔）")
    print("  2. 提供文件路径")
    print()

    choice = input("  请选择 [1/2]: ").strip()
    keywords = []

    if choice == "1":
        raw = input("  粘贴关键词列表: ").strip()
        if not raw:
            return
        keywords = [k.strip() for k in re.split(r'[、,，;；\n]', raw) if k.strip()]
    elif choice == "2":
        from pathlib import Path
        fp = input("  文件路径: ").strip()
        if not fp:
            return
        fp = Path(fp)
        if not fp.exists():
            print(f"\n  {RD}文件不存在{R}")
            return
        with open(fp, 'r', encoding='utf-8') as f:
            keywords = [k.strip() for k in re.split(r'[、,，;；\n]', f.read()) if k.strip()]
    else:
        return

    if not keywords:
        print(f"\n  {RD}无有效关键词{R}")
        return

    print(f"\n  共 {len(keywords)} 个关键词：")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i}. {kw}")

    if not input("\n  确认开始搜索? (y/N): ").strip().lower() == 'y':
        return

    # 获取已关注列表
    conn = get_conn()
    existing = set(r["fakeid"] for r in conn.execute("SELECT fakeid FROM accounts").fetchall())
    conn.close()

    added = 0
    skipped = 0
    notfound = 0

    for i, kw in enumerate(keywords):
        print(f"\n  [{i+1}/{len(keywords)}] {Y}{kw}{R}")
        data = api_get("/api/public/v1/account", {"keyword": kw})
        if data is None:
            notfound += 1
            continue

        results = data.get("list", [])
        if not results:
            print(f"    {RD}未找到{R}")
            retry = input("    尝试其他关键词（回车=跳过）: ").strip()
            if retry:
                data = api_get("/api/public/v1/account", {"keyword": retry})
                if data:
                    results = data.get("list", [])

        if not results:
            notfound += 1
            continue

        # 过滤已关注
        new_results = [r for r in results if r.get("fakeid") not in existing]
        if not new_results:
            print(f"    {GR}全部已关注{R}")
            skipped += 1
            continue

        if len(new_results) == 1:
            r = new_results[0]
            fid = r.get("fakeid", "")
            name = r.get("nickname", "")
            print(f"    找到: {Y}{name}{R}")
            if input(f"    关注 [{name}]? (Y/n): ").strip().lower() != 'n':
                _add_account(fid, name, r)
                existing.add(fid)
                added += 1
            else:
                skipped += 1
        else:
            print(f"    找到 {len(new_results)} 个结果：")
            for j, r in enumerate(new_results, 1):
                print(f"      {j}. {r.get('nickname', '')}")
            pk = input("    选择编号关注（0=跳过）: ").strip()
            if pk:
                try:
                    idx = int(pk)
                    if 1 <= idx <= len(new_results):
                        r = new_results[idx - 1]
                        fid = r.get("fakeid", "")
                        name = r.get("nickname", "")
                        _add_account(fid, name, r)
                        existing.add(fid)
                        added += 1
                    else:
                        skipped += 1
                except ValueError:
                    skipped += 1
            else:
                skipped += 1

        time.sleep(0.3)

    print(f"\n  {'─' * 40}")
    print(f"  {GR}成功关注: {added}{R}")
    print(f"  跳过/已关注: {skipped}")
    if notfound:
        print(f"  {RD}未找到: {notfound}{R}")


def _add_account(fakeid, name, api_data=None):
    """添加公众号到数据库"""
    conn = get_conn()
    desc = ""
    img = ""
    stype = 0
    if api_data:
        desc = api_data.get("signature", "")
        img = api_data.get("round_head_img", "")
        stype = api_data.get("service_type", 0)

    conn.execute("""
        INSERT OR REPLACE INTO accounts (fakeid, name, description, round_head_img, service_type, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
    """, (fakeid, name, desc, img, stype))
    conn.commit()
    conn.close()
    print(f"    {GR}已关注: {name}{R}")


def remove(args):
    """取消关注"""
    fakeid = args.fakeid
    conn = get_conn()
    row = conn.execute("SELECT name FROM accounts WHERE fakeid=?", (fakeid,)).fetchone()
    if not row:
        print(f"\n  {RD}未找到公众号: {fakeid}{R}")
        conn.close()
        return

    name = row["name"]
    print(f"\n  确定取消关注 [{Y}{name}{R}]？")
    print(f"  注意：该操作会删除该公众号的所有文章和下载记录！")

    from .utils import confirm
    if not confirm("  确认取消关注"):
        conn.close()
        return

    conn.execute("DELETE FROM accounts WHERE fakeid=?", (fakeid,))
    conn.commit()
    conn.close()
    print(f"\n  {GR}已取消关注: {name}{R}")


def list_accounts(args=None):
    """列出已关注公众号"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT a.*,
               (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid) AS article_count,
               (SELECT COUNT(*) FROM articles WHERE fakeid=a.fakeid AND downloaded=1) AS downloaded_count
        FROM accounts a ORDER BY a.created_at DESC
    """).fetchall()
    conn.close()

    if not rows:
        print(f"\n  {G}暂无已关注的公众号{R}")
        return

    print(f"\n  {B}已关注公众号{R} (共 {len(rows)} 个)")
    print(f"  {'─' * 70}")
    print(f"  {'名称':20s} {'类型':6s} {'文章':>6s} {'已下载':>8s} {'简介'}")
    print(f"  {'─' * 70}")

    for r in rows:
        stype = "服务号" if r["service_type"] == 1 else "订阅号"
        desc = (r["description"] or "")[:25]
        print(f"  {r['name'][:18]:20s} {stype:6s} {r['article_count']:6d} {r['downloaded_count']:8d} {desc}")

    print()


def import_accounts(args):
    """从公众号.json导入"""
    file_path = args.file
    from pathlib import Path
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
    conn.close()

    added = 0
    for acct in accounts:
        fid = acct.get("fakeid", "")
        name = acct.get("nickname", "")
        if not fid or fid in existing:
            continue
        _add_account(fid, name, acct)
        existing.add(fid)
        added += 1

    print(f"\n  {GR}导入完成: 新增 {added} 个公众号{R}")


def export_accounts(args):
    """导出为公众号.json"""
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
        })

    data = {
        "version": "2.0",
        "usefor": "wechat-article-exporter",
        "accounts": accounts,
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  {GR}已导出 {len(accounts)} 个公众号到: {file_path}{R}")
