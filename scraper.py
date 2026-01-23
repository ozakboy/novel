#!/usr/bin/env python3
"""
帝霸小說爬蟲腳本
從 t.hjwzw.com 爬取小說內容並保存為 markdown 文件
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import re

# 嘗試導入 opencc 進行簡繁轉換
try:
    from opencc import OpenCC
    cc = OpenCC('s2t')  # 簡體轉繁體
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False
    print("提示: 未安裝 opencc-python-reimplemented，將不進行簡繁轉換")
    print("安裝方式: pip install opencc-python-reimplemented")

BASE_URL = "https://t.hjwzw.com"
NOVEL_ID = "35148"
OUTPUT_DIR = "帝霸"

# 請求頭，模擬瀏覽器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
}


def convert_to_traditional(text):
    """將簡體中文轉換為繁體中文"""
    if HAS_OPENCC:
        return cc.convert(text)
    return text


def get_chapter_list(start=0, end=100):
    """獲取章節列表"""
    url = f"{BASE_URL}/ChapterList/{NOVEL_ID}/{start}_{end}"
    print(f"正在獲取章節列表: {url}")

    response = requests.get(url, headers=HEADERS)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    chapters = []
    # 查找所有章節連結
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if '/Read/' in href:
            chapter_name = link.get_text(strip=True)
            chapter_url = BASE_URL + href if href.startswith('/') else href
            chapters.append({
                'name': chapter_name,
                'url': chapter_url
            })

    return chapters


# 需要過濾的網站導航文字
FILTER_LINES = [
    '設置', '書頁', '字體大小', '最小', '較小', '標準', '較大', '最大',
    '是否粗體', '粗體', '正常', '閱讀風格', '粉紅世家', '懷舊紙張',
    '明黃清俊', '淡藍海洋', '白雪天地', '灰色世界', '黑夜模式',
    '開啟', '關閉', '上一章', '下一章', '目錄', '目录', '返回',
    '设置', '书页', '字体大小'
]

# 需要過濾的正則表達式
FILTER_PATTERNS = [
    r'請牢記域名.*',
    r'請記住本站域名.*',
    r'黃金屋.*',
    r'今天.*更.*章.*',
    r'投.*票.*支持.*',
    r'新書需要.*',
    r'感謝讀者.*',
    r'關於更新說明.*',
    r'情節開始展開.*',
]


def clean_content(content, chapter_title):
    """清理內容，移除網站導航和廣告文字"""
    lines = content.split('\n')
    cleaned_lines = []

    # 標記是否已經找到正文開始位置
    found_content_start = False
    title_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳過過濾列表中的行
        if line in FILTER_LINES:
            continue

        # 跳過匹配正則的行
        skip = False
        for pattern in FILTER_PATTERNS:
            if re.search(pattern, line):
                skip = True
                break
        if skip:
            continue

        # 跳過重複的章節標題（保留第一個）
        if chapter_title and chapter_title.replace(' ', '') in line.replace(' ', ''):
            title_count += 1
            if title_count > 1:
                continue
            found_content_start = True

        # 只有找到正文開始後才添加內容
        if found_content_start or (line.startswith('"') or line.startswith('「') or len(line) > 20):
            found_content_start = True
            cleaned_lines.append(line)

    return '\n\n'.join(cleaned_lines)


def get_chapter_content(url):
    """獲取單個章節的完整內容"""
    print(f"  正在爬取: {url}")

    response = requests.get(url, headers=HEADERS)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # 嘗試多種方式找到內容區域
    content = None

    # 方法1: 找 id="AllySite" 或 class="content"
    content_div = soup.find('div', id='AllySite') or soup.find('div', class_='content')

    # 方法2: 找包含大量文字的 div
    if not content_div:
        for div in soup.find_all('div'):
            text = div.get_text()
            if len(text) > 500:  # 假設正文至少500字
                content_div = div
                break

    if content_div:
        # 移除腳本和樣式
        for script in content_div.find_all(['script', 'style']):
            script.decompose()

        # 獲取文字內容，保留段落
        paragraphs = []
        for elem in content_div.stripped_strings:
            text = elem.strip()
            if text and len(text) > 1:
                paragraphs.append(text)

        content = '\n\n'.join(paragraphs)

    # 如果還是找不到，嘗試直接獲取 body 內的文字
    if not content or len(content) < 100:
        body = soup.find('body')
        if body:
            # 移除不需要的元素
            for elem in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                elem.decompose()

            text = body.get_text(separator='\n')
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            content = '\n\n'.join(lines)

    return content


def save_chapter(chapter_num, title, content, output_dir):
    """保存章節為 markdown 文件"""
    # 轉換為繁體
    title = convert_to_traditional(title)
    content = convert_to_traditional(content)

    # 清理內容
    content = clean_content(content, title)

    filename = f"chapter_{chapter_num:04d}.md"
    filepath = os.path.join(output_dir, filename)

    markdown_content = f"""# 第 {chapter_num} 篇

## {title}

{content}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"  已保存: {filename}")


def get_all_chapters():
    """獲取所有章節列表"""
    all_chapters = []

    # 章節分頁列表 (每100章一頁)
    page_ranges = [
        (0, 100), (100, 200), (200, 300), (300, 400), (400, 500),
        (500, 600), (600, 700), (700, 800), (800, 900), (900, 1000),
        (1000, 1100), (1100, 1200), (1200, 1300), (1300, 1400), (1400, 1500),
        (1500, 1600), (1600, 1700), (1700, 1800), (1800, 1900), (1900, 2000),
        (2000, 2100), (2100, 2200), (2200, 2300), (2300, 2400), (2400, 2500),
        (2500, 2600), (2600, 2700), (2700, 2800), (2800, 2900), (2900, 3000),
        (3000, 3100), (3100, 3200), (3200, 3300), (3300, 3400), (3400, 3500),
        (3500, 3600), (3600, 3700), (3700, 3800), (3800, 3900), (3900, 4000),
        (4000, 4100), (4100, 4200), (4200, 4300), (4300, 4400), (4400, 4500),
        (4500, 4600), (4600, 4700), (4700, 4800), (4800, 4900), (4900, 5000),
        (5000, 5100), (5100, 5200), (5200, 5300), (5300, 5400), (5400, 5500),
        (5500, 5600), (5600, 5700), (5700, 5800), (5800, 5900), (5900, 6000),
        (6000, 6100), (6100, 6200), (6200, 6300), (6300, 6400), (6400, 6500),
        (6500, 6600), (6600, 6700), (6700, 6800), (6800, 6900), (6900, 7000),
        (7000, 7100), (7100, 7200), (7200, 7228),
    ]

    for start, end in page_ranges:
        chapters = get_chapter_list(start, end)
        if chapters:
            all_chapters.extend(chapters)
            print(f"  已獲取 {start}-{end} 章節列表，共 {len(chapters)} 章")
        time.sleep(0.5)  # 延遲避免請求過快

    return all_chapters


def main():
    """主函數"""
    # 創建輸出目錄
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 設定要爬取的章節範圍
    START_CHAPTER = 11     # 從第幾篇開始 (0-based，11表示從第12章開始，因為0-10已有)
    END_CHAPTER = 7300     # 爬取到第幾篇 (不包含)

    print(f"開始爬取《帝霸》小說，章節 {START_CHAPTER} 到最新")
    print(f"輸出目錄: {OUTPUT_DIR}/")
    print("-" * 50)

    # 獲取所有章節列表
    print("正在獲取所有章節列表...")
    chapters = get_all_chapters()

    if not chapters:
        print("錯誤: 無法獲取章節列表")
        return

    print(f"\n總共找到 {len(chapters)} 個章節")
    print("-" * 50)

    # 爬取指定範圍的章節
    total = min(END_CHAPTER, len(chapters))
    for i in range(START_CHAPTER, total):
        chapter = chapters[i]

        # 檢查文件是否已存在
        filename = f"chapter_{i:04d}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            print(f"[{i}/{total-1}] {chapter['name']} - 已存在，跳過")
            continue

        print(f"\n[{i}/{total-1}] {chapter['name']}")

        try:
            content = get_chapter_content(chapter['url'])

            if content and len(content) > 100:
                save_chapter(i, chapter['name'], content, OUTPUT_DIR)
            else:
                print(f"  警告: 內容過短或為空，跳過")

            # 延遲，避免請求過快
            time.sleep(0.8)

        except Exception as e:
            print(f"  錯誤: {e}")
            continue

        # 每100章輸出一次進度
        if (i + 1) % 100 == 0:
            print(f"\n*** 已完成 {i + 1} 章 ***\n")

    print("\n" + "=" * 50)
    print("爬取完成！")
    print(f"文件保存在: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
