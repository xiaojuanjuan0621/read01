import json
import re
from collections import defaultdict
from pathlib import Path

# 路径定义
ROOT = Path(__file__).parent.parent
ALL_BOOKS_FILE = ROOT / "docs" / "all-books.json"
STATS_FILE = ROOT / "docs" / "parse-stats.json"
OUTPUT_HTML = ROOT / "docs" / "index.html"
OUTPUT_JSON = ROOT / "docs" / "books.json"


def load_books():
    """从 all-books.json 加载真实数据"""
    if ALL_BOOKS_FILE.exists():
        try:
            with open(ALL_BOOKS_FILE, "r", encoding="utf-8") as f:
                books = json.load(f)
                print(f"✅ 从 all-books.json 加载了 {len(books)} 本书籍")
                return books
        except Exception as e:
            print(f"❌ 加载 all-books.json 失败: {e}")
            print(f"💡 提示：请先运行 'python scripts/parse_md_to_json.py' 生成 all-books.json")
            return []
    
    print("⚠️  未找到 all-books.json 文件")
    print(f"💡 提示：请先运行 'python scripts/parse_md_to_json.py' 生成 all-books.json")
    return []


def load_stats():
    """加载统计信息"""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载统计信息失败: {e}")
    return None


def group_books(books):
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    categories, languages, levels = set(), set(), set()

    for b in books:
        c = b["category"]
        l = b["language"]
        lv = b["level"]

        categories.add(c)
        languages.add(l)
        levels.add(lv)

        grouped[c][l][lv].append(b)

    return grouped, categories, languages, levels


def render_overview(total_books, total_categories, languages, levels):
    # 格式化数字
    books_display = f"{total_books:,}" if total_books > 1000 else str(total_books)
    cats_display = f"{total_categories:,}" if total_categories > 1000 else str(total_categories)
    
    # 语言显示
    lang_display = " / ".join(sorted(languages)) if languages else "中文 / 英文"
    
    return f"""<div class="overview-stats">
<div class="stat-item">
  <div class="stat-icon">📘</div>
  <div class="stat-info">
    <span>总书籍数</span>
    <strong id="total-books">{books_display}</strong>
  </div>
</div>
<div class="stat-item">
  <div class="stat-icon">📂</div>
  <div class="stat-info">
    <span>分类数量</span>
    <strong id="total-categories">{cats_display}</strong>
  </div>
</div>
<div class="stat-item">
  <div class="stat-icon">🌍</div>
  <div class="stat-info">
    <span>支持语言</span>
    <strong>{lang_display}</strong>
  </div>
</div>
<div class="stat-item">
  <div class="stat-icon">📥</div>
  <div class="stat-info">
    <span>支持格式</span>
    <strong>EPUB / MOBI / AZW3</strong>
  </div>
</div>
</div>
"""


def render_search_ui():
    return """<div class="search-section">
  <div class="search-container">
    <div class="search-input-wrapper">
      <span class="search-icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </span>
      <input
        type="text"
        id="search-input"
        placeholder="搜索 书名 / 作者 / 分类（按 / 键快速聚焦）"
        oninput="onSearch(event)"
        aria-label="搜索书籍"
        autocomplete="off"
      />
      <button id="search-clear-btn" class="search-clear-btn" aria-label="清空搜索" style="display: none;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
    <div class="search-hint">
      <span class="hint-icon">💡</span>
      <span>支持多关键词搜索（以空格分隔），如：“文学 鲁迅”</span>
    </div>
  </div>
</div>

<div id="search-results" role="region" aria-live="polite" aria-label="搜索结果">
  <div class="loading-indicator">正在加载书籍数据...</div>
</div>

<script src="search.js"></script>
"""


def render_content(grouped, stats=None):
    lines = []
    
    # 计算每个分类的书籍数量
    category_counts = {}
    for category, languages in grouped.items():
        count = sum(len(books) for lang_dict in languages.values() for books in lang_dict.values())
        category_counts[category] = count
    
    # 按书籍数量排序，优先显示热门分类
    sorted_categories = sorted(category_counts.keys(), key=lambda x: category_counts[x], reverse=True)
    
    # 优先显示用户指定的热门分类
    priority_categories = ["文学", "沟通", "励志", "经典", "历史", "科普", "管理", "社会", "推理", "经济", "哲学", "传记"]
    
    # 重新排序：优先分类在前，然后按数量排序
    priority_set = set(priority_categories)
    priority_list = [cat for cat in priority_categories if cat in sorted_categories]
    other_list = [cat for cat in sorted_categories if cat not in priority_set]
    sorted_categories = priority_list + other_list
    
    # 限制显示的分类数量（避免页面过长）
    max_categories = 20
    if len(sorted_categories) > max_categories:
        lines.append(f"<p class=\"note-text\">💡 注：共 {len(category_counts)} 个分类，以下显示前 {max_categories} 个热门分类的书籍。使用搜索功能可查找所有书籍。</p>\n\n")
        sorted_categories = sorted_categories[:max_categories]

    for category in sorted_categories:
        lines.append(f"<div class=\"category-section\">\n")
        lines.append(f"## 📂 {category}\n")

        for language in sorted(grouped[category].keys()):
            lines.append(f"### 🌍 Language: {language}\n")

            for level in sorted(grouped[category][language].keys()):
                lines.append(f"#### ⭐ Level: {level}\n")

                books_list = grouped[category][language][level]
                # 每个分类-语言-级别组合最多显示10本书
                max_books_per_section = 10
                if len(books_list) > max_books_per_section:
                    books_list = books_list[:max_books_per_section]
                    lines.append(f"<p class=\"note-text\">*（共 {len(grouped[category][language][level])} 本，显示前 {max_books_per_section} 本）*</p>\n")

                lines.append('<div class="books-grid">\n')
                for b in books_list:
                    author = b.get('author', '未知')
                    badges_html = ""
                    for f in b.get("formats", ["epub", "mobi", "azw3"]):
                        badges_html += f'<span class="badge badge-{f.lower()}">{f}</span>'
                    
                    lines.append(
                        f'<div class="book-item">\n'
                        f'  <div>\n'
                        f'    <div class="book-title" title="{b["title"]}">{b["title"]}</div>\n'
                        f'    <div class="book-author">👤 {author}</div>\n'
                        f'  </div>\n'
                        f'  <div>\n'
                        f'    <div class="book-badges">{badges_html}</div>\n'
                        f'    <a href="{b["link"]}" target="_blank" rel="noopener" class="book-download-btn">\n'
                        f'      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">\n'
                        f'        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>\n'
                        f'        <polyline points="7 10 12 15 17 10"></polyline>\n'
                        f'        <line x1="12" y1="15" x2="12" y2="3"></line>\n'
                        f'      </svg>\n'
                        f'      下载资源\n'
                        f'    </a>\n'
                        f'  </div>\n'
                        f'</div>\n'
                    )
                lines.append('</div>\n')
                lines.append("")
        
        lines.append("</div>\n\n")

    if len(sorted_categories) < len(grouped.keys()):
        lines.append(f"\n<hr>\n\n<p class=\"note-text\">💡 还有 {len(grouped.keys()) - len(sorted_categories)} 个分类未显示，请使用搜索功能查找。</p>\n")

    return "\n".join(lines)


def markdown_to_html(md_content):
    """简单的 Markdown 转 HTML 转换"""
    lines = md_content.split('\n')
    result_lines = []
    in_list = False
    in_paragraph = False
    paragraph_lines = []
    in_html_block = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检测 HTML 块开始/结束
        if '<div' in stripped or '<script' in stripped:
            in_html_block = True
        if '</div>' in stripped or '</script>' in stripped:
            in_html_block = False
        
        # HTML 块内的内容直接保留
        if in_html_block or ('<' in stripped and '>' in stripped and not stripped.startswith('#')):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(line)
            i += 1
            continue
        
        # 空行
        if not stripped:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append('')
            i += 1
            continue
        
        # 标题
        if stripped.startswith('#### '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<h4>{stripped[5:]}</h4>')
        elif stripped.startswith('### '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<h3>{stripped[4:]}</h3>')
        elif stripped.startswith('## '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<h2>{stripped[3:]}</h2>')
        elif stripped.startswith('# '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<h1>{stripped[2:]}</h1>')
        # 水平线
        elif stripped == '---':
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append('<hr>')
        # 引用
        elif stripped.startswith('> '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<blockquote>{stripped[2:]}</blockquote>')
        # 列表项
        elif stripped.startswith('- '):
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            content = stripped[2:]
            # 处理内联格式
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', content)
            result_lines.append(f'<li>{content}</li>')
        # 普通段落
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            # 处理内联格式
            processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            processed_line = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', processed_line)
            paragraph_lines.append(processed_line)
            in_paragraph = True
        
        i += 1
    
    # 处理结尾
    if in_list:
        result_lines.append('</ul>')
    if in_paragraph:
        result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
    
    return '\n'.join(result_lines)


def generate_html(md_content):
    """生成完整的 HTML 页面"""
    html_body = markdown_to_html(md_content)
    
    # 尝试加载统计信息并生成更新脚本
    stats_info = ""
    try:
        stats_file = ROOT / "docs" / "parse-stats.json"
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                stats_info = f"""
<script>
// 更新统计信息（从 parse-stats.json）
(function() {{
    const stats = {json.dumps(stats, ensure_ascii=False)};
    const totalBooksEl = document.getElementById('total-books');
    const totalCatsEl = document.getElementById('total-categories');
    if (totalBooksEl && stats.total_books) {{
        totalBooksEl.textContent = stats.total_books.toLocaleString();
    }}
    if (totalCatsEl && stats.categories_count) {{
        totalCatsEl.textContent = stats.categories_count.toLocaleString();
    }}
}})();
</script>"""
    except Exception as e:
        print(f"⚠️  生成统计信息脚本失败: {e}")
    
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="电子书下载宝库 - 汇聚24,000+本电子书，涵盖文学、历史、科普、管理、技术等各个领域。支持epub、mobi、azw3格式，完全免费。">
    <meta name="keywords" content="电子书下载,免费电子书,epub下载,mobi下载,azw3下载,电子书资源,文学电子书,历史电子书">
    <meta name="author" content="ebook-treasure-chest">
    <meta name="robots" content="index, follow">
    
    <!-- Open Graph -->
    <meta property="og:title" content="📚 电子书下载宝库 - Ebook Treasure Chest">
    <meta property="og:description" content="汇聚24,000+本电子书，涵盖文学、历史、科普、管理、技术等各个领域">
    <meta property="og:type" content="website">
    
    <!-- Preload critical resources -->
    <link rel="preload" href="all-books.json" as="fetch" crossorigin>
    <link rel="preload" href="search.js" as="script">
    
    <title>📚 电子书下载宝库 - Ebook Treasure Chest</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            --font-heading: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            
            /* Light Theme Colors */
            --bg-app: #f6f8fa;
            --bg-card: #ffffff;
            --bg-header: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            --bg-header-accent: rgba(255, 255, 255, 0.1);
            --border-color: #e5e7eb;
            --text-primary: #1f2937;
            --text-secondary: #4b5563;
            --text-muted: #9ca3af;
            --accent-color: #4f46e5;
            --accent-gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            --accent-hover: #4338ca;
            --success-color: #10b981;
            --download-btn-bg: #4f46e5;
            --download-btn-text: #ffffff;
            --download-btn-hover: #4338ca;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
            --card-glow: rgba(79, 70, 229, 0.05);
            
            --badge-epub-bg: #e0f2fe;
            --badge-epub-text: #0369a1;
            --badge-mobi-bg: #fef3c7;
            --badge-mobi-text: #b45309;
            --badge-azw3-bg: #d1fae5;
            --badge-azw3-text: #065f46;
        }}
        
        [data-theme="dark"] {{
            /* Dark Theme Colors */
            --bg-app: #090d16;
            --bg-card: #111827;
            --bg-header: linear-gradient(135deg, #1e1b4b 0%, #311042 100%);
            --bg-header-accent: rgba(255, 255, 255, 0.03);
            --border-color: #1f2937;
            --text-primary: #f9fafb;
            --text-secondary: #e5e7eb;
            --text-muted: #9ca3af;
            --accent-color: #818cf8;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            --accent-hover: #4f46e5;
            --success-color: #34d399;
            --download-btn-bg: #6366f1;
            --download-btn-text: #ffffff;
            --download-btn-hover: #4f46e5;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
            --card-glow: rgba(99, 102, 241, 0.15);
            
            --badge-epub-bg: rgba(3, 105, 161, 0.2);
            --badge-epub-text: #38bdf8;
            --badge-mobi-bg: rgba(180, 83, 9, 0.2);
            --badge-mobi-text: #fbbf24;
            --badge-azw3-bg: rgba(6, 95, 70, 0.2);
            --badge-azw3-text: #34d399;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: var(--font-sans);
            background-color: var(--bg-app);
            color: var(--text-secondary);
            line-height: 1.6;
            transition: background-color 0.3s ease, color 0.3s ease;
            min-height: 100vh;
            padding-bottom: 0;
        }}
        
        .main-wrapper {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        @media (max-width: 768px) {{
            .main-wrapper {{
                padding: 0 15px;
            }}
        }}
        
        .app-header {{
            background: var(--bg-header);
            color: #ffffff;
            padding: 50px 20px;
            border-radius: 0 0 24px 24px;
            margin-bottom: 30px;
            box-shadow: var(--shadow-lg);
            position: relative;
            overflow: hidden;
        }}
        
        .app-header::before,
        .app-header::after {{
            content: '';
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.08);
            filter: blur(40px);
            pointer-events: none;
        }}
        
        .app-header::before {{
            width: 300px;
            height: 300px;
            top: -100px;
            right: -50px;
        }}
        
        .app-header::after {{
            width: 200px;
            height: 200px;
            bottom: -80px;
            left: -50px;
        }}
        
        .header-container {{
            max-width: 1200px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }}
        
        .brand {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 12px;
        }}
        
        .logo-emoji {{
            font-size: 2.8rem;
            animation: float 4s ease-in-out infinite;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-8px); }}
        }}
        
        .logo-text {{
            font-size: 2.5rem;
            font-weight: 800;
            font-family: var(--font-heading);
            letter-spacing: -1px;
            background: linear-gradient(to right, #ffffff, #e2e8f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .subtitle {{
            font-size: 1.1rem;
            color: rgba(255, 255, 255, 0.85);
            max-width: 600px;
            line-height: 1.5;
        }}
        
        .theme-toggle-btn {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: var(--bg-header-accent);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #ffffff;
            cursor: pointer;
            padding: 10px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.25s ease;
            z-index: 10;
        }}
        
        .theme-toggle-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.05);
        }}
        
        .theme-toggle-btn svg {{
            width: 20px;
            height: 20px;
        }}
        
        [data-theme="dark"] .sun-icon {{ display: block; }}
        [data-theme="dark"] .moon-icon {{ display: none; }}
        .sun-icon {{ display: none; }}
        .moon-icon {{ display: block; }}
        
        h2 {{
            font-size: 1.6rem;
            margin: 35px 0 20px 0;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border-color);
            color: var(--text-primary);
            font-weight: 700;
            font-family: var(--font-heading);
            position: relative;
        }}
        
        h2::before {{
            content: "";
            position: absolute;
            left: 0;
            bottom: -2px;
            width: 60px;
            height: 2px;
            background: var(--accent-gradient);
            border-radius: 1px;
        }}
        
        h3 {{
            font-size: 1.15rem;
            margin: 25px 0 12px 0;
            color: var(--accent-color);
            font-weight: 600;
            font-family: var(--font-heading);
        }}
        
        h4 {{
            font-size: 0.95rem;
            margin: 15px 0 10px 0;
            color: var(--text-muted);
            font-weight: 500;
            font-family: var(--font-sans);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        a {{
            color: var(--accent-color);
            text-decoration: none;
            transition: all 0.2s ease;
            font-weight: 500;
        }}
        
        a:hover {{
            color: var(--accent-hover);
            text-decoration: underline;
        }}
        
        blockquote {{
            padding: 16px 20px;
            color: var(--text-secondary);
            border-left: 4px solid var(--accent-color);
            margin: 20px 0;
            background: var(--bg-card);
            border-radius: 8px;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
            border-left-width: 4px;
        }}
        
        hr {{
            height: 1px;
            margin: 40px 0;
            background: linear-gradient(90deg, transparent, var(--border-color), transparent);
            border: 0;
        }}
        
        .search-section {{
            margin: 30px 0;
        }}
        
        .search-container {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 24px;
            border-radius: 20px;
            box-shadow: var(--shadow-md);
        }}
        
        .search-input-wrapper {{
            position: relative;
            display: flex;
            align-items: center;
        }}
        
        .search-icon {{
            position: absolute;
            left: 20px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            width: 20px;
            height: 20px;
        }}
        
        .search-icon svg {{
            width: 100%;
            height: 100%;
        }}
        
        input[type="text"] {{
            width: 100%;
            padding: 16px 50px 16px 55px;
            font-size: 1.05rem;
            border: 2px solid var(--border-color);
            border-radius: 12px;
            background-color: var(--bg-app);
            color: var(--text-primary);
            font-family: var(--font-sans);
            transition: all 0.3s ease;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
        }}
        
        input[type="text"]:focus {{
            outline: none;
            border-color: var(--accent-color);
            background-color: var(--bg-card);
            box-shadow: 0 0 0 4px var(--card-glow);
        }}
        
        input[type="text"]::placeholder {{
            color: var(--text-muted);
        }}
        
        .search-clear-btn {{
            position: absolute;
            right: 20px;
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            padding: 4px;
            border-radius: 50%;
            transition: all 0.2s ease;
        }}
        
        .search-clear-btn:hover {{
            background-color: var(--border-color);
            color: var(--text-primary);
        }}
        
        .search-clear-btn svg {{
            width: 18px;
            height: 18px;
        }}
        
        .search-hint {{
            margin-top: 12px;
            color: var(--text-secondary);
            font-size: 0.88rem;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: var(--bg-app);
            border-radius: 8px;
        }}
        
        #search-results {{
            margin-top: 24px;
            min-height: 50px;
        }}
        
        .loading-indicator,
        .search-ready-status {{
            text-align: center;
            padding: 30px;
            border-radius: 16px;
            font-size: 1.05rem;
            font-weight: 500;
        }}
        
        .loading-indicator {{
            background: var(--bg-app);
            color: var(--text-secondary);
            border: 1px dashed var(--border-color);
        }}
        
        .loading-indicator::before {{
            content: "⏳ ";
            animation: pulse 1.5s ease-in-out infinite;
        }}
        
        .search-ready-status {{
            background: rgba(16, 185, 129, 0.08);
            color: var(--success-color);
            border: 1px solid rgba(16, 185, 129, 0.15);
        }}
        
        .search-results-info {{
            padding: 10px 16px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: var(--shadow-sm);
        }}
        
        .search-results-info strong {{
            color: var(--accent-color);
            font-weight: 600;
        }}
        
        .search-no-results {{
            text-align: center;
            padding: 40px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            color: var(--text-muted);
            font-size: 1rem;
            box-shadow: var(--shadow-md);
        }}
        
        #search-results mark {{
            background: rgba(245, 158, 11, 0.15);
            color: #d97706;
            padding: 1px 4px;
            border-radius: 4px;
            font-weight: 600;
        }}
        
        [data-theme="dark"] #search-results mark {{
            background: rgba(245, 158, 11, 0.3);
            color: #fbbf24;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        ul {{
            padding-left: 20px;
            margin: 16px 0;
        }}
        
        li {{
            margin: 8px 0;
            color: var(--text-secondary);
        }}
        
        p {{
            margin: 16px 0;
            color: var(--text-secondary);
        }}
        
        .overview-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .stat-item {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: var(--shadow-md);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .stat-item:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
            border-color: var(--accent-color);
            box-shadow: 0 10px 20px -5px var(--card-glow);
        }}
        
        .stat-icon {{
            font-size: 2rem;
            background: var(--bg-header-accent);
            width: 54px;
            height: 54px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .stat-info {{
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        
        .stat-info span {{
            font-size: 0.82rem;
            color: var(--text-muted);
            font-weight: 500;
        }}
        
        .stat-info strong {{
            font-size: 1.45rem;
            color: var(--text-primary);
            font-weight: 700;
            font-family: var(--font-heading);
        }}
        
        @media (max-width: 600px) {{
            .overview-stats {{
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }}
            .stat-item {{
                padding: 14px;
                gap: 10px;
                border-radius: 12px;
            }}
            .stat-icon {{
                width: 42px;
                height: 42px;
                font-size: 1.5rem;
            }}
            .stat-info strong {{
                font-size: 1.2rem;
            }}
        }}
        
        .category-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 24px;
            margin: 24px 0;
            border-radius: 20px;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
        }}
        
        .category-section:hover {{
            box-shadow: var(--shadow-lg);
            border-color: var(--accent-color);
        }}
        
        .books-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
            margin: 16px 0;
        }}
        
        .book-item {{
            background: var(--bg-app);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        
        .book-item::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--accent-gradient);
            opacity: 0.8;
        }}
        
        .book-item:hover {{
            transform: translateY(-4px);
            background: var(--bg-card);
            border-color: var(--accent-color);
            box-shadow: 0 8px 16px -4px var(--card-glow);
        }}
        
        .book-title {{
            font-size: 1.05rem;
            color: var(--text-primary);
            font-weight: 600;
            line-height: 1.45;
            margin-bottom: 8px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            height: 3.1rem;
        }}
        
        .book-author {{
            font-size: 0.88rem;
            color: var(--text-secondary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .book-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 16px;
        }}
        
        .badge {{
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 5px;
            text-transform: uppercase;
        }}
        
        .badge-epub {{
            background: var(--badge-epub-bg);
            color: var(--badge-epub-text);
        }}
        
        .badge-mobi {{
            background: var(--badge-mobi-bg);
            color: var(--badge-mobi-text);
        }}
        
        .badge-azw3 {{
            background: var(--badge-azw3-bg);
            color: var(--badge-azw3-text);
        }}
        
        .badge-category {{
            background: var(--bg-header-accent);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }}
        
        .book-download-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            padding: 9px 14px;
            background: var(--accent-gradient);
            color: #ffffff !important;
            font-size: 0.88rem;
            font-weight: 600;
            border-radius: 10px;
            text-align: center;
            transition: all 0.25s ease;
            box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.15);
        }}
        
        .book-download-btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 12px -1px rgba(99, 102, 241, 0.25);
            opacity: 0.95;
            text-decoration: none !important;
        }}
        
        .book-download-btn svg {{
            width: 15px;
            height: 15px;
        }}
        
        .note-text {{
            padding: 10px 14px;
            background: var(--bg-card);
            border-left: 4px solid var(--accent-color);
            border-radius: 8px;
            color: var(--text-secondary);
            font-size: 0.88rem;
            margin: 16px 0;
            border: 1px solid var(--border-color);
            border-left-width: 4px;
            box-shadow: var(--shadow-sm);
        }}
        
        .app-footer {{
            background: var(--bg-card);
            border-top: 1px solid var(--border-color);
            padding: 30px 20px;
            margin-top: 50px;
            text-align: center;
            border-radius: 24px 24px 0 0;
            box-shadow: 0 -4px 10px rgba(0,0,0,0.01);
        }}
        
        .footer-container {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
        }}
        
        .footer-brand {{
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: var(--font-heading);
        }}
        
        .footer-links a {{
            color: var(--accent-color);
            font-weight: 500;
            margin: 0 10px;
        }}
        
        .footer-copyright {{
            font-size: 0.82rem;
            color: var(--text-muted);
        }}
        
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--bg-app);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}
        
        code {{
            background: var(--bg-app);
            color: var(--accent-color);
            padding: 2px 5px;
            border-radius: 4px;
            font-family: SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace;
            font-size: 0.88rem;
            border: 1px solid var(--border-color);
        }}
        
        strong {{
            color: var(--text-primary);
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <header class="app-header">
        <div class="header-container">
            <div class="brand">
                <span class="logo-emoji">📚</span>
                <h1 class="logo-text">Ebook Treasure Chest</h1>
            </div>
            <p class="subtitle">汇聚微信读书、帆书、喜马拉雅等大部分优质电子书下载，支持 epub/mobi/azw3 格式，完全免费</p>
            
            <button id="theme-toggle" class="theme-toggle-btn" aria-label="切换主题">
                <svg class="sun-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="5"></circle>
                    <line x1="12" y1="1" x2="12" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="23"></line>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                    <line x1="1" y1="12" x2="3" y2="12"></line>
                    <line x1="21" y1="12" x2="23" y2="12"></line>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                </svg>
                <svg class="moon-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
            </button>
        </div>
    </header>

    <div class="main-wrapper">
        <main>
            {content}
        </main>
    </div>

    <footer class="app-footer">
        <div class="footer-container">
            <p class="footer-brand">📚 电子书下载宝库</p>
            <p class="footer-links">
                <a href="https://github.com/jbiaojerry/ebook-treasure-chest" target="_blank" rel="noopener">GitHub 仓库</a> |
                <a href="README.md" target="_blank">使用说明</a>
            </p>
            <p class="footer-copyright">&copy; 2026 Ebook Treasure Chest. All rights reserved.</p>
        </div>
    </footer>

    {stats_script}
    
    <script>
        // 主题切换脚本
        (function() {{
            const themeToggleBtn = document.getElementById('theme-toggle');
            const savedTheme = localStorage.getItem('theme');
            let currentTheme = 'dark'; // 默认深色
            
            if (savedTheme) {{
                currentTheme = savedTheme;
            }} else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {{
                currentTheme = 'light';
            }}
            
            document.documentElement.setAttribute('data-theme', currentTheme);
            
            if (themeToggleBtn) {{
                themeToggleBtn.addEventListener('click', () => {{
                    const theme = document.documentElement.getAttribute('data-theme');
                    const newTheme = theme === 'dark' ? 'light' : 'dark';
                    document.documentElement.setAttribute('data-theme', newTheme);
                    localStorage.setItem('theme', newTheme);
                }});
            }}
        }})();
    </script>
</body>
</html>"""
    
    return html_template.format(content=html_body, stats_script=stats_info)


def main():
    books = load_books()
    stats = load_stats()
    
    # 如果有统计信息，使用统计信息中的数据
    if stats:
        total_books = stats.get("total_books", len(books))
        total_categories = stats.get("categories_count", len(set(b.get("category", "") for b in books)))
    else:
        total_books = len(books)
        total_categories = len(set(b.get("category", "") for b in books))
    
    grouped, categories, languages, levels = group_books(books)
    
    # 使用统计信息中的分类数量（如果可用）
    if stats and "categories_count" in stats:
        categories_count = stats["categories_count"]
    else:
        categories_count = len(categories)

    md_parts = []
    md_parts.append(render_overview(total_books, categories_count, languages, levels))
    md_parts.append("\n---\n")
    md_parts.append(render_search_ui())
    md_parts.append("\n---\n")
    md_parts.append(render_content(grouped, stats))

    md_content = "\n".join(md_parts)
    
    OUTPUT_HTML.parent.mkdir(exist_ok=True)

    # 写 index.html（GitHub Pages 优先查找）
    html_content = generate_html(md_content)
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")

    # 写 books.json（给前端搜索用，作为 metadata 数据的备份）
    OUTPUT_JSON.write_text(
        json.dumps(books, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("✅ index.html & books.json generated")
    
    # 检查 all-books.json
    if ALL_BOOKS_FILE.exists():
        print(f"ℹ️  检测到 all-books.json ({ALL_BOOKS_FILE.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print("⚠️  警告：未找到 all-books.json")
        print("💡 提示：运行 'python scripts/parse_md_to_json.py' 生成 all-books.json")


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()
