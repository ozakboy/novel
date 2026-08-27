#!/usr/bin/env python3
"""掃描倉庫根目錄的小說資料夾,產生閱讀網站用的 manifest.json。

結構約定:
  <小說名>/<級數(分卷)資料夾>/*.md   → 每個 .md 是一個章節(或合集)
  <小說名>/*.md                      → 沒有分卷時直接放章節

輸出 manifest.json:
  { "generated": "...", "novels": [ { "name", "volumes": [ { "name", "chapters":
    [ { "file", "title" } ] } ], "chapterCount" } ] }
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDED_DIRS = {".git", ".github", "scripts", "icons", "node_modules", "docs"}

_num_re = re.compile(r"\d+")


def natural_key(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def extract_title(path):
    """取章節檔第一個 '##' 標題(退而求其次 '#'),失敗就用檔名。"""
    h1 = None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for _ in range(30):
                line = f.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith("## "):
                    return line[3:].strip()
                if h1 is None and line.startswith("# "):
                    h1 = line[2:].strip()
    except OSError:
        pass
    return h1 or os.path.splitext(os.path.basename(path))[0]


def list_md(dirpath):
    try:
        names = [n for n in os.listdir(dirpath)
                 if n.lower().endswith(".md") and not n.startswith(".")
                 and n.upper() != "README.MD"]
    except OSError:
        return []
    return sorted(names, key=natural_key)


_generic_name_re = re.compile(r"^(chapter|ch|c)?[_\- ]?\d+$", re.IGNORECASE)


def build_volume(novel, volname, dirpath):
    chapters = []
    for name in list_md(dirpath):
        fpath = os.path.join(dirpath, name)
        base = os.path.splitext(name)[0]
        # 檔名本身有意義(如 第0001-0100集)就用檔名,
        # 純流水號(chapter_0001)才去抓內文標題
        if _generic_name_re.match(base):
            title = extract_title(fpath)
        else:
            title = base
        chapters.append({"file": name, "title": title})
    if not chapters:
        return None
    return {"name": volname, "chapters": chapters}


def main():
    novels = []
    for entry in sorted(os.listdir(ROOT), key=natural_key):
        path = os.path.join(ROOT, entry)
        if not os.path.isdir(path) or entry.startswith(".") or entry in EXCLUDED_DIRS:
            continue
        volumes = []
        # 小說根目錄直接放章節 → 視為「正文」卷
        direct = build_volume(entry, "正文", path)
        if direct:
            volumes.append(direct)
        for sub in sorted(os.listdir(path), key=natural_key):
            subpath = os.path.join(path, sub)
            if os.path.isdir(subpath) and not sub.startswith("."):
                vol = build_volume(entry, sub, subpath)
                if vol:
                    volumes.append(vol)
        if not volumes:
            continue
        count = sum(len(v["chapters"]) for v in volumes)
        novels.append({"name": entry, "volumes": volumes, "chapterCount": count})

    manifest = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "novels": novels,
    }
    out = os.path.join(ROOT, "manifest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
    total = sum(n["chapterCount"] for n in novels)
    print(f"manifest.json: {len(novels)} 部小說, {total} 個章節檔, "
          f"{os.path.getsize(out) // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
