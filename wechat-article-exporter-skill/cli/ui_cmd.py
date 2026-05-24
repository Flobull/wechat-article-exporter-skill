#!/usr/bin/env python3
# coding: utf-8
"""
TUI 交互式菜单 — python wechat.py ui
"""
import sys
import argparse

from cli.utils import (
    B, R, C, Y, G, GR, RD, D,
    read_config, check_config, init_db, migrate_db, get_download_dir,
    DB_PATH,
)


def tui():
    """TUI 入口"""
    init_db()
    migrate_db()

    cfg = read_config()
    missing = check_config()
    auto_scan = cfg.get("auto_scan", True)

    if missing:
        print(f"\n  {RD}⚠ 配置不完整，缺少: {', '.join(missing)}{R}")
        print(f"  请先在菜单中配置，缺少配置时 API 功能可能不可用\n")

    if get_download_dir() and auto_scan and DB_PATH.exists():
        print(f"\n  {G}扫描库存更新...{R}")
        try:
            from cli.manage_cmd import scan
            scan(None)
        except Exception:
            pass

    try:
        _main_loop()
    except KeyboardInterrupt:
        print(f"\n  {G}拜拜 👋{R}")


def _main_loop():
    """主菜单循环"""
    while True:
        print(f"""
  {B}{C}████████  WECHAT 微信公众号  ████████{R}
  {'─' * 52}
  {B}主菜单{R}
  {'─' * 52}
  1.  {Y}公众号管理{R}    搜索 / 批量关注 / 取消关注 / 导入导出
  2.  {Y}同步管理{R}      同步文章链接 / 检查新文章
  3.  {Y}文章查询{R}      列表 / 最新 / 搜索 / 时间筛选 / 未下载
  4.  {Y}下载管理{R}      单篇下载 / 批量下载 / 记录 / 校验
  5.  {Y}配置管理{R}      查看 / 修改配置
  6.  {Y}数据库管理{R}    统计 / 列表 / 导入导出 / 取消关注 / 库存扫描 / 清空
  0.  {GR}退出{R}
  {'─' * 52}""")

        choice = input("  请选择 [0-6]: ").strip()

        if choice == "1":
            _menu_account()
        elif choice == "2":
            _menu_sync()
        elif choice == "3":
            _menu_article()
        elif choice == "4":
            _menu_download()
        elif choice == "5":
            _menu_config()
        elif choice == "6":
            _menu_manage()
        elif choice == "0":
            print(f"\n  {GR}拜拜 👋{R}")
            break
        else:
            print(f"\n  {RD}无效选择{R}")


# ─────── 公众号管理 ───────

def _menu_account():
    from cli import account_cmd
    while True:
        print(f"""
  {B}公众号管理{R}
  {'─' * 30}
  1. 搜索公众号
  2. 批量关注
  3. 取消关注
  4. 列出已关注
  5. 导入公众号.json
  6. 导出公众号.json
  0. 返回主菜单
""")
        choice = input("  请选择 [0-6]: ").strip()

        if choice == "1":
            keyword = input("  关键词: ").strip()
            if keyword:
                account_cmd.search(argparse.Namespace(keyword=keyword))
        elif choice == "2":
            account_cmd.add(None)
        elif choice == "3":
            fakeid = input("  fakeid: ").strip()
            if fakeid:
                account_cmd.remove(argparse.Namespace(fakeid=fakeid))
        elif choice == "4":
            account_cmd.list_accounts()
        elif choice == "5":
            file = input("  文件路径 (默认 公众号.json): ").strip() or "公众号.json"
            account_cmd.import_accounts(argparse.Namespace(file=file))
        elif choice == "6":
            file = input("  文件路径 (默认 公众号.json): ").strip() or "公众号.json"
            account_cmd.export_accounts(argparse.Namespace(file=file))
        elif choice == "0":
            break


# ─────── 同步管理 ───────

def _menu_sync():
    from cli import sync_cmd
    while True:
        print(f"""
  {B}同步管理{R}
  {'─' * 30}
  1. 同步文章链接
  2. 检查新文章
  0. 返回主菜单
""")
        choice = input("  请选择 [0-2]: ").strip()

        if choice == "1":
            print("\n  同步方式：")
            print("  1. 最新的 X 篇")
            print("  2. 给定时间段")
            print("  3. 全部同步（耗时较久）")
            sub = input("  请选择 [1-3]: ").strip()

            fakeid = input("  公众号 fakeid (留空=所有): ").strip() or None

            if sub == "1":
                count = int(input("  数量: ").strip() or "10")
                args = argparse.Namespace(fakeid=fakeid, latest=count, range=None, all=False)
            elif sub == "2":
                from_date = input("  开始日期 (YYYY-MM-DD): ").strip()
                to_date = input("  结束日期 (留空=今天): ").strip() or None
                args = argparse.Namespace(fakeid=fakeid, latest=None, range=(from_date, to_date), all=False)
            else:
                print(f"\n  {Y}⚠ 全部同步可能耗时较长{R}")
                c = input(f"  确认？({G}y{R}/{RD}N{R}): ").strip().lower()
                if c != 'y':
                    print("  已取消")
                    continue
                args = argparse.Namespace(fakeid=fakeid, latest=None, range=None, all=True)

            sync_cmd.run(args)

        elif choice == "2":
            fakeid = input("  公众号 fakeid (留空=所有): ").strip() or None
            sync_cmd.check_new(argparse.Namespace(fakeid=fakeid))
        elif choice == "0":
            break


# ─────── 文章查询 ───────

def _menu_article():
    from cli import article_cmd
    while True:
        print(f"""
  {B}文章查询{R}
  {'─' * 30}
  1. 列出已同步文章
  2. 最新 N 篇
  3. 搜索文章标题
  4. 时间范围筛选
  5. 列出未下载文章
  0. 返回主菜单
""")
        choice = input("  请选择 [0-5]: ").strip()

        if choice == "1":
            fakeid = input("  公众号 fakeid (留空=所有): ").strip() or None
            args = argparse.Namespace(fakeid=fakeid, page=1, size=20)
            article_cmd.list_articles(args)
        elif choice == "2":
            fakeid = input("  公众号 fakeid (留空=所有): ").strip() or None
            count = int(input("  数量 (默认5): ").strip() or "5")
            article_cmd.latest(argparse.Namespace(fakeid=fakeid, count=count))
        elif choice == "3":
            keyword = input("  关键词: ").strip()
            if keyword:
                fakeid = input("  公众号 fakeid (留空=全部): ").strip() or None
                article_cmd.search(argparse.Namespace(keyword=keyword, fakeid=fakeid))
        elif choice == "4":
            fakeid = input("  公众号 fakeid: ").strip()
            if fakeid:
                from_date = input("  开始日期 (YYYY-MM-DD): ").strip()
                to_date = input("  结束日期 (留空=今天): ").strip() or None
                article_cmd.range_articles(argparse.Namespace(fakeid=fakeid, date_from=from_date, date_to=to_date))
        elif choice == "5":
            fakeid = input("  公众号 fakeid (留空=所有): ").strip() or None
            article_cmd.undownloaded(argparse.Namespace(fakeid=fakeid))
        elif choice == "0":
            break


# ─────── 下载管理 ───────

def _menu_download():
    from cli import download_cmd
    while True:
        print(f"""
  {B}下载管理{R}
  {'─' * 30}
  1. 下载单篇文章
  2. 批量下载
  3. 列出下载记录
  4. 校验文件完整性
  0. 返回主菜单
""")
        choice = input("  请选择 [0-3]: ").strip()

        if choice == "1":
            url = input("  文章 URL: ").strip()
            if url:
                fmt = input("  格式 (留空=默认): ").strip() or None
                out = input("  输出文件名 (留空=自动): ").strip() or None
                download_cmd.article(argparse.Namespace(url=url, format=fmt, dir=None, out=out))
        elif choice == "2":
            fakeid = input("  公众号 fakeid (留空=所有): ").strip() or None
            print("\n  下载方式：")
            print("  1. 最新的 X 篇")
            print("  2. 给定时间段")
            print("  3. 全部下载")
            sub = input("  请选择 [1-3]: ").strip()

            common = dict(fakeid=fakeid, format=None)
            if sub == "1":
                count = int(input("  数量: ").strip() or "10")
                args = argparse.Namespace(latest=count, range=None, all=False, **common)
            elif sub == "2":
                from_date = input("  开始日期 (YYYY-MM-DD): ").strip()
                to_date = input("  结束日期 (留空=今天): ").strip() or None
                args = argparse.Namespace(latest=None, range=(from_date, to_date), all=False, **common)
            else:
                args = argparse.Namespace(latest=None, range=None, all=True, **common)

            download_cmd.batch(args)

        elif choice == "3":
            fakeid = input("  公众号 fakeid (留空=所有): ").strip() or None
            download_cmd.list_downloads(argparse.Namespace(fakeid=fakeid))
        elif choice == "4":
            fakeid = input("  公众号 fakeid (留空=所有): ").strip() or None
            download_cmd.verify(argparse.Namespace(fakeid=fakeid))
        elif choice == "0":
            break


# ─────── 配置管理 ───────

def _menu_config():
    from cli import config_cmd
    while True:
        print(f"""
  {B}配置管理{R}
  {'─' * 30}
  1. 查看配置
  2. 修改配置
  0. 返回主菜单
""")
        choice = input("  请选择 [0-2]: ").strip()

        if choice == "1":
            config_cmd.show()
        elif choice == "2":
            print("  可配置项: base_url, api_key, download_dir, default_format, auto_scan")
            key = input("  配置项: ").strip()
            value = input("  配置值: ").strip()
            if key and value:
                config_cmd.set_cmd(argparse.Namespace(key=key, value=value))
        elif choice == "0":
            break


# ─────── 数据库管理 ───────

def _menu_manage():
    from cli import manage_cmd
    while True:
        print(f"""
  {B}数据库管理{R}
  {'─' * 30}
  1. 统计信息
  2. 列出公众号所有信息
  3. 导入公众号.json
  4. 导出公众号.json
  5. 取消关注并删除数据
  6. 扫描库存更新
  7. 切换自动扫描状态
  8. 清空下载记录
  0. 返回主菜单
""")
        choice = input("  请选择 [0-8]: ").strip()

        if choice == "1":
            manage_cmd.stats()
        elif choice == "2":
            fakeid = input("  公众号 fakeid (留空=所有): ").strip() or None
            manage_cmd.list_accounts(argparse.Namespace(fakeid=fakeid))
        elif choice == "3":
            file = input("  文件路径: ").strip()
            if file:
                manage_cmd.import_accounts(argparse.Namespace(file=file))
        elif choice == "4":
            file = input("  文件路径 (默认 公众号.json): ").strip() or "公众号.json"
            manage_cmd.export_accounts(argparse.Namespace(file=file))
        elif choice == "5":
            fakeid = input("  fakeid: ").strip()
            if fakeid:
                del_files = input(f"  同时删除已下载文件? (y/{RD}N{R}): ").strip().lower() == 'y'
                manage_cmd.unfollow(argparse.Namespace(fakeid=fakeid, delete_files=del_files))
        elif choice == "6":
            manage_cmd.scan(argparse.Namespace(auto=False))
        elif choice == "7":
            manage_cmd.scan(argparse.Namespace(auto=True))
        elif choice == "8":
            yes = input(f"  确认清空所有下载记录? (y/{RD}N{R}): ").strip().lower() == 'y'
            if yes:
                manage_cmd.clear_downloads(argparse.Namespace(yes=True))
            else:
                print("  已取消")
        elif choice == "0":
            break
