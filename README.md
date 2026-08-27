# novel — 小說書架

用 GitHub Pages 架設的個人小說閱讀網站,支援 PWA(可安裝到手機主畫面、離線閱讀已看過的章節)。

## 資料夾結構約定

```
<小說名>/                 ← 每個資料夾是一部小說
  <級數/分卷資料夾>/       ← 例如 第0001-1000集、合集版本
    *.md                  ← 每個 Markdown 檔是一個章節(或合集)
```

- 檔名是純流水號(如 `chapter_0001.md`)時,章節標題取自檔內第一個 `##` 標題。
- 檔名本身有意義(如 `第0001-0100集.md`)時,直接用檔名當標題。

## 啟用 GitHub Pages(只需設定一次)

到 repo 的 **Settings → Pages → Build and deployment → Source** 選擇 **GitHub Actions**。

之後每次 push 到 `main`,`.github/workflows/pages.yml` 會自動:

1. 執行 `scripts/build_manifest.py` 重建書目 `manifest.json`
2. 部署整個網站到 GitHub Pages

網址會是 `https://<帳號>.github.io/novel/`。

> 也可以改用「Deploy from a branch」模式(main / root),此時新增小說後要記得手動跑
> `python3 scripts/build_manifest.py` 並把 `manifest.json` 一起 commit。

## 新增小說

把小說資料夾(依上面的結構)放進 repo 根目錄,push 到 `main` 即可,網站書架會自動出現。

## 網站功能

- 書架 → 分卷(級數)→ 章節列表 → 閱讀器
- 章節標題搜尋
- 記住每本書的閱讀進度(章節 + 捲動位置),首頁一鍵「繼續閱讀」
- 字級 / 行距 / 亮・米黃・暗 三種主題
- PWA:可安裝到手機主畫面,讀過的章節離線也能看

## 本機預覽

```bash
python3 scripts/build_manifest.py
python3 -m http.server 8000
# 開 http://localhost:8000
```

## 其他檔案

- `scraper.py` / `monitor.sh`:小說抓取工具
- `scripts/make_icons.py`:重新產生 PWA 圖示
