#!/usr/bin/env python3
# coding: utf-8
"""
配置管理命令
"""
import json
from .utils import read_config, write_config, B, R, C, Y, G, GR


def show(args=None):
    """查看当前配置"""
    cfg = read_config()
    if not cfg:
        print(f"\n  {G}配置文件为空或不存在{R}")
        return

    print(f"\n  {B}{C}当前配置{R}")
    print(f"  {'─' * 50}")

    items = [
        ("base_url", "网站地址"),
        ("api_key", "API 密钥"),
        ("download_dir", "下载目录"),
        ("default_format", "默认格式"),
        ("dir_structure", "目录结构"),
        ("auto_scan", "自动扫描"),
    ]

    for key, label in items:
        val = cfg.get(key, "")
        if key == "api_key" and val:
            val = val[:8] + "..." if len(val) > 8 else val
        if key == "dir_structure":
            val = val or "account"
            desc = {"account": "按公众号", "date": "按日期", "flat": "平铺"}
            val = f"{val} ({desc.get(val, '')})"
        status = f"{GR}{val}{R}" if val else f"{G}(未设置){R}"
        print(f"  {Y}{label:12s}{R}  {status}")

    print()


def set_cmd(args):
    """修改配置项"""
    key = args.key
    value = args.value

    valid_keys = [
        "base_url", "api_key", "download_dir", "default_format",
        "dir_structure", "auto_scan"
    ]
    if key not in valid_keys:
        print(f"\n  无效的配置项: {key}")
        print(f"  有效配置项: {', '.join(valid_keys)}")
        return

    cfg = read_config()

    if key == "default_format":
        valid_fmts = ["html", "markdown", "text", "json"]
        fmts = [f.strip() for f in value.split(",")]
        invalid = [f for f in fmts if f not in valid_fmts]
        if invalid:
            print(f"\n  无效的格式: {', '.join(invalid)}")
            print(f"  有效格式: {', '.join(valid_fmts)}")
            return
        value = ",".join(fmts)

    if key == "dir_structure":
        valid_structures = ["account", "date", "flat"]
        if value not in valid_structures:
            print(f"\n  无效的目录结构: {value}")
            print(f"  有效结构: {', '.join(valid_structures)}")
            print(f"  account - 按公众号分目录 (下载目录/公众号名/文件)")
            print(f"  date    - 按日期分目录 (下载目录/日期/公众号名/文件)")
            print(f"  flat    - 平铺 (下载目录/文件)")
            return

    if key == "auto_scan":
        value = value.lower() in ("1", "true", "yes", "on")

    cfg[key] = value
    write_config(cfg)
    print(f"\n  {key} 已更新为: {value}")


def reset_config(args=None):
    """重置配置"""
    from .utils import confirm
    if not confirm("确认重置所有配置？"):
        return

    # 保留当前的default_format和dir_structure作为默认值
    old_cfg = read_config()
    new_cfg = {
        "default_format": "markdown,html,text",
        "dir_structure": "account",
    }
    # 保留用户设置的其他值
    for key in ["base_url", "api_key", "download_dir", "auto_scan"]:
        if old_cfg.get(key):
            new_cfg[key] = old_cfg[key]

    write_config(new_cfg)
    print("\n  配置已重置（保留了基本设置）")
