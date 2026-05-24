#!/usr/bin/env python3
# coding: utf-8
"""
微信公众号文章下载工具 CLI

用法:
  python wechat.py <command> [options]

示例:
  python wechat.py config show                    # 查看配置
  python wechat.py account search 量化             # 搜索公众号
  python wechat.py sync run --all                 # 同步所有公众号文章
  python wechat.py download batch --latest 10     # 下载每个公众号最新10篇
"""
import sys
import os

# PyInstaller 打包兼容
if getattr(sys, 'frozen', False):
    _APP_DIR = os.path.dirname(sys.executable)
    _BUNDLE_DIR = getattr(sys, '_MEIPASS', _APP_DIR)
    sys.path.insert(0, _BUNDLE_DIR)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _APP_DIR)


def print_custom_help():
    """自定义帮助信息"""
    from cli.utils import read_config, B, R, C, Y, G, D, RD, GR

    # ASCII Logo
    logo = f"""  {C}██╗    ██╗███████╗ ██████╗██╗  ██╗ █████╗ ████████╗{R}
  {C}██║    ██║██╔════╝██╔════╝██║  ██║██╔══██╗╚══██╔══╝{R}
  {C}██║ █╗ ██║█████╗  ██║     ███████║███████║   ██║   {R}
  {C}██║███╗██║██╔══╝  ██║     ██╔══██║██╔══██║   ██║   {R}
  {C}╚███╔███╔╝███████╗╚██████╗██║  ██║██║  ██║   ██║   {R}
  {C} ╚══╝╚══╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   {R}"""

    tagline = f"  {B}微信公众号文章下载工具{R}  {G}·{R}  {G}CLI 版本{R}"

    line = f"{D}{'─' * 72}{R}"

    def section(title):
        return f"{B}{C}▎{R} {B}{title}{R}"

    def cmd(name, desc, width=22):
        return f"    {Y}{name:<{width}}{R}  {desc}"

    # 检查配置状态
    cfg = read_config()
    config_status = []
    if not cfg.get("base_url"):
        config_status.append(f"{RD}base_url 未设置{R}")
    if not cfg.get("api_key"):
        config_status.append(f"{RD}api_key 未设置{R}")
    if not cfg.get("download_dir"):
        config_status.append(f"{RD}download_dir 未设置{R}")
    if not cfg.get("default_format"):
        config_status.append(f"{RD}default_format 未设置{R}")

    status_line = ""
    if config_status:
        status_line = f"\n  {G}配置状态:{R} {', '.join(config_status)}\n"

    help_text = f"""
{logo}

{tagline}

{line}
{status_line}
  {B}用法{R}    {Y}wechat{R} <command> [options]

  {section("快速开始")}
{cmd("wechat config show", "查看当前配置")}
{cmd("wechat config set <key> <val>", "修改配置项")}
{cmd("wechat account search <keyword>", "搜索公众号")}
{cmd("wechat sync run --all", "同步所有公众号文章")}
{cmd("wechat download batch", "批量下载文章")}

  {section("配置管理 - config")}
{cmd("config show", "查看当前配置")}
{cmd("config set <key> <value>", "修改配置项 (base_url/api_key/download_dir/default_format)")}

  {section("公众号管理 - account")}
{cmd("account search <keyword>", "搜索公众号")}
{cmd("account add", "批量关注公众号（交互式）")}
{cmd("account remove <fakeid>", "取消关注")}
{cmd("account list", "列出已关注公众号")}
{cmd("account import <file>", "从公众号.json导入")}
{cmd("account export [file]", "导出为公众号.json")}

  {section("同步管理 - sync")}
{cmd("sync run [fakeid]", "同步文章链接，默认所有公众号")}
{cmd("  --latest <N>", "同步最新的X篇")}
{cmd("  --range <from> <to>", "同步给定时间段")}
{cmd("  --all", "全部同步（默认）")}
{cmd("sync check-new [fakeid]", "检查新文章")}

  {section("文章查询 - article")}
{cmd("article list [fakeid]", "列出已同步文章，默认所有公众号")}
{cmd("article latest [fakeid] <N>", "最新N篇")}
{cmd("article search <keyword>", "搜索文章标题")}
{cmd("article range <fakeid> <from> <to>", "时间范围筛选")}
{cmd("article undownloaded [fakeid]", "列出未下载文章")}

  {section("下载管理 - download")}
{cmd("download article <url>", "下载单篇文章")}
{cmd("download batch [fakeid]", "批量下载，默认所有公众号")}
{cmd("  --latest <N>", "下载最新的X篇")}
{cmd("  --range <from> <to>", "下载给定时间段")}
{cmd("  --all", "全部下载（默认）")}
{cmd("  --format <fmt>", "指定格式 (html/markdown/text/json)")}
{cmd("  --overwrite", "覆盖已下载的文件")}
{cmd("download list [fakeid]", "列出下载记录")}
{cmd("download verify [fakeid]", "校验文件完整性")}
{cmd("  --repair", "自动修复无效记录")}

  {section("数据库管理 - manage")}
{cmd("manage stats", "统计信息")}
{cmd("manage list [fakeid]", "列出公众号所有信息")}
{cmd("manage import <file>", "导入公众号.json")}
{cmd("manage export [file]", "导出公众号.json")}
{cmd("manage unfollow <fakeid>", "取消关注并删除数据")}
{cmd("  --delete-files", "同时删除已下载文件")}
{cmd("manage scan", "扫描库存更新")}
{cmd("manage scan --auto", "切换自动扫描状态")}
{cmd("manage clear-downloads", "清空下载记录")}
{cmd("  -y, --yes", "跳过确认")}

{line}
  {G}详细帮助{R}   wechat <command> --help
{line}
"""
    print(help_text)


def print_interactive_menu():
    """交互式菜单"""
    from cli.utils import read_config, B, R, C, Y, G, GR, RD
    from cli.utils import check_config, init_db, migrate_db, DB_PATH

    # 初始化数据库
    init_db()
    migrate_db()

    # 检查配置
    missing = check_config()
    if missing:
        print(f"\n  {RD}配置不完整，缺少: {', '.join(missing)}{R}")
        print(f"  请先使用 {Y}wechat config set <key> <value>{R} 配置")

    # 如果 download_dir 不为空，扫描库存
    cfg = read_config()
    auto_scan = cfg.get("auto_scan", True)
    if cfg.get("download_dir") and auto_scan and DB_PATH.exists():
        print(f"\n  {G}扫描库存更新...{R}")
        try:
            from cli.manage_cmd import scan
            scan(None)
        except:
            pass

    while True:
        print(f"\n  {B}{C}微信公众号文章下载工具{R}")
        print(f"  {'─' * 40}")
        print(f"  1. {Y}公众号管理{R}")
        print(f"  2. {Y}同步管理{R}")
        print(f"  3. {Y}文章查询{R}")
        print(f"  4. {Y}下载管理{R}")
        print(f"  5. {Y}配置管理{R}")
        print(f"  6. {Y}统计信息{R}")
        print(f"  0. {G}退出{R}")
        print()

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
            from cli.manage_cmd import stats
            stats()
        elif choice == "0":
            print(f"\n  拜拜 👋")
            break
        else:
            print(f"\n  {RD}无效选择{R}")


def _menu_account():
    """公众号管理菜单"""
    from cli.utils import B, R, Y
    from cli import account_cmd

    while True:
        print(f"\n  {B}公众号管理{R}")
        print(f"  {'─' * 30}")
        print(f"  1. 搜索公众号")
        print(f"  2. 批量关注")
        print(f"  3. 取消关注")
        print(f"  4. 列出已关注")
        print(f"  5. 导入公众号.json")
        print(f"  6. 导出公众号.json")
        print(f"  0. 返回")
        print()

        choice = input("  请选择 [0-6]: ").strip()

        if choice == "1":
            keyword = input("  关键词: ").strip()
            if keyword:
                import argparse
                args = argparse.Namespace(keyword=keyword)
                account_cmd.search(args)
        elif choice == "2":
            account_cmd.add(None)
        elif choice == "3":
            fakeid = input("  fakeid: ").strip()
            if fakeid:
                import argparse
                args = argparse.Namespace(fakeid=fakeid)
                account_cmd.remove(args)
        elif choice == "4":
            account_cmd.list_accounts()
        elif choice == "5":
            file = input("  文件路径 (默认 公众号.json): ").strip() or "公众号.json"
            import argparse
            args = argparse.Namespace(file=file)
            account_cmd.import_accounts(args)
        elif choice == "6":
            file = input("  文件路径 (默认 公众号.json): ").strip() or "公众号.json"
            import argparse
            args = argparse.Namespace(file=file)
            account_cmd.export_accounts(args)
        elif choice == "0":
            break


def _menu_sync():
    """同步管理菜单"""
    from cli.utils import B, R, Y
    from cli import sync_cmd

    while True:
        print(f"\n  {B}同步管理{R}")
        print(f"  {'─' * 30}")
        print(f"  1. 同步文章链接")
        print(f"  2. 检查新文章")
        print(f"  0. 返回")
        print()

        choice = input("  请选择 [0-2]: ").strip()

        if choice == "1":
            print("\n  同步方式：")
            print("  1. 最新的X篇")
            print("  2. 给定时间段")
            print("  3. 全部同步")
            sub = input("  请选择 [1-3]: ").strip()

            fakeid = input("  公众号fakeid (留空=所有): ").strip() or None
            import argparse

            if sub == "1":
                count = int(input("  数量: ").strip() or "10")
                args = argparse.Namespace(fakeid=fakeid, latest=count, range=None, all=False)
            elif sub == "2":
                from_date = input("  开始日期 (YYYY-MM-DD): ").strip()
                to_date = input("  结束日期 (留空=今天): ").strip() or None
                args = argparse.Namespace(fakeid=fakeid, latest=None, range=(from_date, to_date), all=False)
            else:
                args = argparse.Namespace(fakeid=fakeid, latest=None, range=None, all=True)

            sync_cmd.run(args)
        elif choice == "2":
            fakeid = input("  公众号fakeid (留空=所有): ").strip() or None
            import argparse
            args = argparse.Namespace(fakeid=fakeid)
            sync_cmd.check_new(args)
        elif choice == "0":
            break


def _menu_article():
    """文章查询菜单"""
    from cli.utils import B, R, Y
    from cli import article_cmd

    while True:
        print(f"\n  {B}文章查询{R}")
        print(f"  {'─' * 30}")
        print(f"  1. 列出已同步文章")
        print(f"  2. 最新N篇")
        print(f"  3. 搜索文章标题")
        print(f"  4. 时间范围筛选")
        print(f"  5. 列出未下载文章")
        print(f"  0. 返回")
        print()

        choice = input("  请选择 [0-5]: ").strip()
        import argparse

        if choice == "1":
            fakeid = input("  公众号fakeid (留空=所有): ").strip() or None
            page = int(input("  页码 (默认1): ").strip() or "1")
            args = argparse.Namespace(fakeid=fakeid, page=page, size=20)
            article_cmd.list_articles(args)
        elif choice == "2":
            fakeid = input("  公众号fakeid (留空=所有): ").strip() or None
            count = int(input("  数量 (默认5): ").strip() or "5")
            args = argparse.Namespace(fakeid=fakeid, count=count)
            article_cmd.latest(args)
        elif choice == "3":
            keyword = input("  关键词: ").strip()
            if keyword:
                fakeid = input("  公众号fakeid (留空=全部): ").strip() or None
                args = argparse.Namespace(keyword=keyword, fakeid=fakeid)
                article_cmd.search(args)
        elif choice == "4":
            fakeid = input("  公众号fakeid: ").strip()
            if fakeid:
                from_date = input("  开始日期 (YYYY-MM-DD): ").strip()
                to_date = input("  结束日期 (留空=今天): ").strip() or None
                args = argparse.Namespace(fakeid=fakeid, date_from=from_date, date_to=to_date)
                article_cmd.range_articles(args)
        elif choice == "5":
            fakeid = input("  公众号fakeid (留空=所有): ").strip() or None
            args = argparse.Namespace(fakeid=fakeid)
            article_cmd.undownloaded(args)
        elif choice == "0":
            break


def _menu_download():
    """下载管理菜单"""
    from cli.utils import B, R, Y
    from cli import download_cmd

    while True:
        print(f"\n  {B}下载管理{R}")
        print(f"  {'─' * 30}")
        print(f"  1. 下载单篇文章")
        print(f"  2. 批量下载")
        print(f"  3. 列出下载记录")
        print(f"  4. 校验文件完整性")
        print(f"  0. 返回")
        print()

        choice = input("  请选择 [0-4]: ").strip()
        import argparse

        if choice == "1":
            url = input("  文章URL: ").strip()
            if url:
                fmt = input("  格式 (留空=默认): ").strip() or None
                out = input("  输出文件名 (留空=自动): ").strip() or None
                args = argparse.Namespace(url=url, format=fmt, dir=None, out=out)
                download_cmd.article(args)
        elif choice == "2":
            fakeid = input("  公众号fakeid (留空=所有): ").strip() or None
            print("\n  下载方式：")
            print("  1. 最新的X篇")
            print("  2. 给定时间段")
            print("  3. 全部下载")
            sub = input("  请选择 [1-3]: ").strip()

            if sub == "1":
                count = int(input("  数量: ").strip() or "10")
                args = argparse.Namespace(fakeid=fakeid, latest=count, range=None, all=False, format=None)
            elif sub == "2":
                from_date = input("  开始日期 (YYYY-MM-DD): ").strip()
                to_date = input("  结束日期 (留空=今天): ").strip() or None
                args = argparse.Namespace(fakeid=fakeid, latest=None, range=(from_date, to_date), all=False, format=None)
            else:
                args = argparse.Namespace(fakeid=fakeid, latest=None, range=None, all=True, format=None)

            download_cmd.batch(args)
        elif choice == "3":
            fakeid = input("  公众号fakeid (留空=所有): ").strip() or None
            args = argparse.Namespace(fakeid=fakeid)
            download_cmd.list_downloads(args)
        elif choice == "4":
            fakeid = input("  公众号fakeid (留空=所有): ").strip() or None
            args = argparse.Namespace(fakeid=fakeid)
            download_cmd.verify(args)
        elif choice == "0":
            break


def _menu_config():
    """配置管理菜单"""
    from cli.utils import B, R, Y
    from cli import config_cmd

    while True:
        print(f"\n  {B}配置管理{R}")
        print(f"  {'─' * 30}")
        print(f"  1. 查看配置")
        print(f"  2. 修改配置")
        print(f"  0. 返回")
        print()

        choice = input("  请选择 [0-2]: ").strip()

        if choice == "1":
            config_cmd.show()
        elif choice == "2":
            print("\n  可配置项: base_url, api_key, download_dir, default_format, auto_scan")
            key = input("  配置项: ").strip()
            value = input("  配置值: ").strip()
            if key and value:
                import argparse
                args = argparse.Namespace(key=key, value=value)
                config_cmd.set_cmd(args)
        elif choice == "0":
            break


def main():
    """主入口"""
    from cli.utils import enable_ansi_colors, init_db, migrate_db

    # 启用 ANSI 颜色
    enable_ansi_colors()

    # 如果没有参数，显示自定义帮助信息
    if len(sys.argv) == 1:
        print_custom_help()
        return

    # 初始化数据库
    init_db()
    migrate_db()

    # 解析命令行参数
    import argparse

    parser = argparse.ArgumentParser(
        prog="wechat",
        description="微信公众号文章下载工具 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # ── config ──
    p_cfg = sub.add_parser("config", help="配置管理")
    cfg_sub = p_cfg.add_subparsers(dest="config_action")
    cfg_sub.add_parser("show", help="查看当前配置")
    p_cfg_set = cfg_sub.add_parser("set", help="修改配置项")
    p_cfg_set.add_argument("key", help="配置项名称")
    p_cfg_set.add_argument("value", help="配置值")
    cfg_sub.add_parser("reset", help="重置配置")

    # ── account ──
    p_acct = sub.add_parser("account", help="公众号管理")
    acct_sub = p_acct.add_subparsers(dest="account_action")
    p_search = acct_sub.add_parser("search", help="搜索公众号")
    p_search.add_argument("keyword", help="搜索关键词")
    acct_sub.add_parser("add", help="批量关注公众号")
    p_remove = acct_sub.add_parser("remove", help="取消关注")
    p_remove.add_argument("fakeid", help="公众号fakeid")
    acct_sub.add_parser("list", help="列出已关注公众号")
    p_import = acct_sub.add_parser("import", help="从公众号.json导入")
    p_import.add_argument("file", help="文件路径")
    p_export = acct_sub.add_parser("export", help="导出为公众号.json")
    p_export.add_argument("file", nargs="?", default="公众号.json", help="文件路径")

    # ── sync ──
    p_sync = sub.add_parser("sync", help="同步管理")
    sync_sub = p_sync.add_subparsers(dest="sync_action")
    p_run = sync_sub.add_parser("run", help="同步文章链接")
    p_run.add_argument("fakeid", nargs="?", default=None, help="公众号fakeid (留空=所有)")
    p_run.add_argument("--latest", type=int, help="同步最新的X篇")
    p_run.add_argument("--range", nargs=2, metavar=("FROM", "TO"), help="同步给定时间段")
    p_run.add_argument("--all", action="store_true", help="全部同步")
    p_check = sync_sub.add_parser("check-new", help="检查新文章")
    p_check.add_argument("fakeid", nargs="?", default=None, help="公众号fakeid")

    # ── article ──
    p_art = sub.add_parser("article", help="文章查询")
    art_sub = p_art.add_subparsers(dest="article_action")
    p_list = art_sub.add_parser("list", help="列出已同步文章")
    p_list.add_argument("fakeid", nargs="?", default=None, help="公众号fakeid")
    p_list.add_argument("--page", type=int, default=1, help="页码")
    p_list.add_argument("--size", type=int, default=20, help="每页数量")
    p_latest = art_sub.add_parser("latest", help="最新N篇")
    p_latest.add_argument("fakeid", nargs="?", default=None, help="公众号fakeid")
    p_latest.add_argument("count", type=int, nargs="?", default=5, help="数量")
    p_srch = art_sub.add_parser("search", help="搜索文章标题")
    p_srch.add_argument("keyword", help="搜索关键词")
    p_srch.add_argument("--fakeid", help="限定公众号")
    p_range = art_sub.add_parser("range", help="时间范围筛选")
    p_range.add_argument("fakeid", help="公众号fakeid")
    p_range.add_argument("date_from", help="开始日期 (YYYY-MM-DD)")
    p_range.add_argument("date_to", nargs="?", help="结束日期")
    p_undl = art_sub.add_parser("undownloaded", help="列出未下载文章")
    p_undl.add_argument("fakeid", nargs="?", default=None, help="公众号fakeid")

    # ── download ──
    p_dl = sub.add_parser("download", help="下载管理")
    dl_sub = p_dl.add_subparsers(dest="download_action")
    p_dl_art = dl_sub.add_parser("article", help="下载单篇文章")
    p_dl_art.add_argument("url", help="文章URL")
    p_dl_art.add_argument("--format", dest="fmt", help="格式")
    p_dl_art.add_argument("--dir", help="输出目录")
    p_dl_art.add_argument("--out", help="输出文件名")
    p_batch = dl_sub.add_parser("batch", help="批量下载")
    p_batch.add_argument("fakeid", nargs="?", default=None, help="公众号fakeid")
    p_batch.add_argument("--latest", type=int, help="下载最新的X篇")
    p_batch.add_argument("--range", nargs=2, metavar=("FROM", "TO"), help="下载给定时间段")
    p_batch.add_argument("--all", action="store_true", help="全部下载")
    p_batch.add_argument("--format", dest="fmt", help="指定格式")
    p_batch.add_argument("--overwrite", action="store_true", help="覆盖已下载的文件")
    p_dl_list = dl_sub.add_parser("list", help="列出下载记录")
    p_dl_list.add_argument("fakeid", nargs="?", default=None, help="公众号fakeid")
    p_verify = dl_sub.add_parser("verify", help="校验文件完整性")
    p_verify.add_argument("fakeid", nargs="?", default=None, help="公众号fakeid")
    p_verify.add_argument("--repair", action="store_true", help="自动修复无效记录")

    # ── manage ──
    p_mgmt = sub.add_parser("manage", help="数据库管理")
    mgmt_sub = p_mgmt.add_subparsers(dest="manage_action")
    mgmt_sub.add_parser("stats", help="统计信息")
    p_mgmt_list = mgmt_sub.add_parser("list", help="列出公众号所有信息")
    p_mgmt_list.add_argument("fakeid", nargs="?", default=None, help="公众号fakeid")
    p_mgmt_imp = mgmt_sub.add_parser("import", help="导入公众号.json")
    p_mgmt_imp.add_argument("file", help="文件路径")
    p_mgmt_exp = mgmt_sub.add_parser("export", help="导出公众号.json")
    p_mgmt_exp.add_argument("file", nargs="?", default="公众号.json", help="文件路径")
    p_unfollow = mgmt_sub.add_parser("unfollow", help="取消关注并删除数据")
    p_unfollow.add_argument("fakeid", help="公众号fakeid")
    p_unfollow.add_argument("--delete-files", action="store_true", help="同时删除已下载文件")
    p_scan = mgmt_sub.add_parser("scan", help="扫描库存更新")
    p_scan.add_argument("--auto", action="store_true", help="切换自动扫描状态")
    p_clear = mgmt_sub.add_parser("clear-downloads", help="清空下载记录")
    p_clear.add_argument("-y", "--yes", action="store_true", help="跳过确认")

    # ── ui ──
    sub.add_parser("ui", help="交互式 TUI 菜单")

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 路由
    if args.command == "config":
        from cli import config_cmd
        if args.config_action == "set":
            config_cmd.set_cmd(args)
        elif args.config_action == "reset":
            config_cmd.reset_config()
        else:
            config_cmd.show()

    elif args.command == "account":
        from cli import account_cmd
        if args.account_action == "search":
            account_cmd.search(args)
        elif args.account_action == "add":
            account_cmd.add(args)
        elif args.account_action == "remove":
            account_cmd.remove(args)
        elif args.account_action == "list":
            account_cmd.list_accounts()
        elif args.account_action == "import":
            account_cmd.import_accounts(args)
        elif args.account_action == "export":
            account_cmd.export_accounts(args)
        else:
            print("  用法: wechat account {search|add|remove|list|import|export}")

    elif args.command == "sync":
        from cli import sync_cmd
        if args.sync_action == "run":
            sync_cmd.run(args)
        elif args.sync_action == "check-new":
            sync_cmd.check_new(args)
        else:
            print("  用法: wechat sync {run|check-new}")

    elif args.command == "article":
        from cli import article_cmd
        if args.article_action == "list":
            article_cmd.list_articles(args)
        elif args.article_action == "latest":
            article_cmd.latest(args)
        elif args.article_action == "search":
            article_cmd.search(args)
        elif args.article_action == "range":
            article_cmd.range_articles(args)
        elif args.article_action == "undownloaded":
            article_cmd.undownloaded(args)
        else:
            print("  用法: wechat article {list|latest|search|range|undownloaded}")

    elif args.command == "download":
        from cli import download_cmd
        if args.download_action == "article":
            download_cmd.article(args)
        elif args.download_action == "batch":
            download_cmd.batch(args)
        elif args.download_action == "list":
            download_cmd.list_downloads(args)
        elif args.download_action == "verify":
            download_cmd.verify(args)
        else:
            print("  用法: wechat download {article|batch|list|verify}")

    elif args.command == "manage":
        from cli import manage_cmd
        if args.manage_action == "stats":
            manage_cmd.stats()
        elif args.manage_action == "list":
            manage_cmd.list_accounts(args)
        elif args.manage_action == "import":
            manage_cmd.import_accounts(args)
        elif args.manage_action == "export":
            manage_cmd.export_accounts(args)
        elif args.manage_action == "unfollow":
            manage_cmd.unfollow(args)
        elif args.manage_action == "scan":
            manage_cmd.scan(args)
        elif args.manage_action == "clear-downloads":
            manage_cmd.clear_downloads(args)
        else:
            print("  用法: wechat manage {stats|list|import|export|unfollow|scan|clear-downloads}")

    elif args.command == "ui":
        from cli.ui_cmd import tui
        tui()


if __name__ == "__main__":
    main()
