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

    filename = f"chapter_{chapter_num:03d}.md"
    filepath = os.path.join(output_dir, filename)

    markdown_content = f"""# 第 {chapter_num} 篇

## {title}

{content}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"  已保存: {filename}")


def main():
    """主函數"""
    # 創建輸出目錄
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 設定要爬取的章節範圍
    START_CHAPTER = 0   # 從第幾篇開始 (0-based)
    END_CHAPTER = 11    # 爬取到第幾篇 (不包含)

    print(f"開始爬取《帝霸》小說，章節 {START_CHAPTER} 到 {END_CHAPTER-1}")
    print(f"輸出目錄: {OUTPUT_DIR}/")
    print("-" * 50)

    # 獲取章節列表
    chapters = get_chapter_list(0, 100)

    if not chapters:
        print("錯誤: 無法獲取章節列表")
        return

    print(f"找到 {len(chapters)} 個章節")
    print("-" * 50)

    # 爬取指定範圍的章節
    for i in range(START_CHAPTER, min(END_CHAPTER, len(chapters))):
        chapter = chapters[i]
        print(f"\n[{i}/{END_CHAPTER-1}] {chapter['name']}")

        try:
            content = get_chapter_content(chapter['url'])

            if content and len(content) > 100:
                save_chapter(i, chapter['name'], content, OUTPUT_DIR)
            else:
                print(f"  警告: 內容過短或為空，跳過")

            # 延遲，避免請求過快
            time.sleep(1)

        except Exception as e:
            print(f"  錯誤: {e}")
            continue

    print("\n" + "=" * 50)
    print("爬取完成！")
    print(f"文件保存在: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
