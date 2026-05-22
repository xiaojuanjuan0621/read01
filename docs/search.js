let books = [];
let searchTimeout = null;
const MAX_RESULTS = 100; // 最多显示100条结果

// HTML 转义函数
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 正则表达式特殊字符转义
function escapeRegex(str) {
  if (!str) return '';
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// 文本高亮
function highlightText(text, keyword) {
  if (!keyword || !text) return escapeHtml(text);
  
  const escapedKeyword = escapeRegex(keyword);
  const regex = new RegExp(`(${escapedKeyword})`, 'gi');
  
  const escapedText = escapeHtml(text);
  return escapedText.replace(regex, '<mark>$1</mark>');
}

// 加载书籍数据
async function loadBooks() {
  console.log("🔄 开始加载书籍数据...");
  
  const resultsBox = document.getElementById("search-results");
  const searchInput = document.getElementById("search-input");
  
  try {
    console.log("📥 尝试加载 all-books.json...");
    const res = await fetch("all-books.json");
    
    if (res.ok) {
      books = await res.json();
      console.log(`✅ 已加载 ${books.length} 本书籍（来自 all-books.json）`);
      
      if (searchInput) {
        searchInput.placeholder = `搜索 ${books.length.toLocaleString()} 本书的书名、作者或分类...`;
      }
      
      if (resultsBox && (!searchInput || !searchInput.value.trim())) {
        resultsBox.innerHTML = `<div class="search-ready-status">✨ 数据库已成功加载 ${books.length.toLocaleString()} 本书，随时可以搜索！</div>`;
      }
      return;
    }
  } catch (e) {
    console.warn("⚠️ all-books.json 加载失败，尝试降级:", e);
  }
  
  try {
    console.log("📥 尝试加载 books.json...");
    const res = await fetch("books.json");
    if (res.ok) {
      books = await res.json();
      console.log(`✅ 已加载 ${books.length} 本书籍（来自 books.json）`);
      
      if (searchInput) {
        searchInput.placeholder = `搜索 ${books.length.toLocaleString()} 本书的书名、作者或分类...`;
      }
      
      if (resultsBox && (!searchInput || !searchInput.value.trim())) {
        resultsBox.innerHTML = `<div class="search-ready-status">✨ 数据库已成功加载 ${books.length.toLocaleString()} 本书，随时可以搜索！</div>`;
      }
    } else {
      throw new Error(`books.json 状态码: ${res.status}`);
    }
  } catch (e) {
    console.error("❌ 无法加载书籍数据:", e);
    if (resultsBox) {
      resultsBox.innerHTML = `<div class="search-no-results">⚠️ 无法加载书籍数据，请检查网络连接或刷新页面重试。</div>`;
    }
  }
}

// 搜索匹配逻辑
function searchBooks(keyword) {
  if (!keyword || keyword.trim() === "") {
    return [];
  }
  
  const k = keyword.toLowerCase().trim();
  const keywords = k.split(/\s+/);

  return books.filter(b => {
    const title = (b.title || "").toLowerCase();
    const author = (b.author || "").toLowerCase();
    const category = (b.category || "").toLowerCase();
    
    return keywords.every(kw => 
      title.includes(kw) ||
      author.includes(kw) ||
      category.includes(kw)
    );
  }).slice(0, MAX_RESULTS);
}

// 渲染结果
function renderResults(results, keyword) {
  const box = document.getElementById("search-results");
  box.innerHTML = "";

  if (results.length === 0) {
    box.innerHTML = `<div class="search-no-results">🔍 没有找到相关书籍，请尝试更换关键词</div>`;
    return;
  }

  const keywordLower = keyword.toLowerCase();
  
  // 渲染结果数量信息
  const countDiv = document.createElement("div");
  countDiv.className = "search-results-info";
  countDiv.innerHTML = `找到 <strong>${results.length}</strong>${results.length === MAX_RESULTS ? '+' : ''} 本书`;
  box.appendChild(countDiv);

  // 渲染书籍网格
  const gridDiv = document.createElement("div");
  gridDiv.className = "books-grid";

  results.forEach(b => {
    const bookItem = document.createElement("div");
    bookItem.className = "book-item";
    
    const highlightedTitle = highlightText(b.title || "未知", keywordLower);
    const highlightedAuthor = highlightText(b.author || "未知", keywordLower);
    const highlightedCategory = highlightText(b.category || "", keywordLower);
    
    // 安全链接处理
    let safeLink = "#";
    if (b.link) {
      try {
        const url = new URL(b.link, window.location.origin);
        if (url.protocol === 'http:' || url.protocol === 'https:') {
          safeLink = url.href;
        }
      } catch (e) {
        safeLink = escapeHtml(b.link);
      }
    }
    
    // 渲染格式徽章
    let badgesHtml = "";
    const formats = b.formats || ["epub", "mobi", "azw3"];
    formats.forEach(f => {
      badgesHtml += `<span class="badge badge-${f.toLowerCase()}">${f}</span>`;
    });
    
    if (b.category) {
      badgesHtml += `<span class="badge badge-category">${highlightedCategory}</span>`;
    }
    
    bookItem.innerHTML = `
      <div>
        <div class="book-title" title="${escapeHtml(b.title || '')}">${highlightedTitle}</div>
        <div class="book-author">👤 ${highlightedAuthor}</div>
      </div>
      <div>
        <div class="book-badges">${badgesHtml}</div>
        <a href="${safeLink}" target="_blank" rel="noopener" class="book-download-btn">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          下载资源
        </a>
      </div>
    `;
    gridDiv.appendChild(bookItem);
  });
  
  box.appendChild(gridDiv);
}

// 搜索输入回调
function onSearch(e) {
  const keyword = e.target.value.trim();
  const clearBtn = document.getElementById("search-clear-btn");
  
  if (clearBtn) {
    clearBtn.style.display = keyword ? "flex" : "none";
  }
  
  if (books.length === 0) {
    const box = document.getElementById("search-results");
    if (box) {
      box.innerHTML = `<div class="search-no-results">⏳ 正在加载书籍数据，请稍候...</div>`;
    }
    return;
  }
  
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  
  if (!keyword) {
    const box = document.getElementById("search-results");
    if (box) {
      box.innerHTML = `<div class="search-ready-status">✨ 数据库已成功加载 ${books.length.toLocaleString()} 本书，随时可以搜索！</div>`;
    }
    return;
  }
  
  searchTimeout = setTimeout(() => {
    const results = searchBooks(keyword);
    console.log(`🔍 搜索 "${keyword}" 找到 ${results.length} 条结果`);
    renderResults(results, keyword);
  }, 300);
}

// 初始化清空按钮与键盘快捷键
function initSearch() {
  const searchInput = document.getElementById("search-input");
  const clearBtn = document.getElementById("search-clear-btn");
  
  if (searchInput) {
    // 监听全局 "/" 键聚焦搜索框
    document.addEventListener("keydown", (e) => {
      if (e.key === "/" && 
          document.activeElement !== searchInput && 
          document.activeElement.tagName !== "INPUT" && 
          document.activeElement.tagName !== "TEXTAREA" &&
          !document.activeElement.isContentEditable) {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
    });
    
    if (clearBtn) {
      clearBtn.style.display = searchInput.value.trim() ? "flex" : "none";
      
      clearBtn.addEventListener("click", () => {
        searchInput.value = "";
        clearBtn.style.display = "none";
        const box = document.getElementById("search-results");
        if (box) {
          box.innerHTML = books.length > 0 
            ? `<div class="search-ready-status">✨ 数据库已成功加载 ${books.length.toLocaleString()} 本书，随时可以搜索！</div>`
            : `<div class="loading-indicator">正在加载书籍数据...</div>`;
        }
        searchInput.focus();
      });
    }
  }
}

let pendingDownloadUrl = '';

// 初始化升级弹窗交互逻辑
function initUpgradeModal() {
  const modal = document.getElementById('upgrade-modal');
  const confirmBtn = document.getElementById('modal-download-btn');
  const closeBtn = document.getElementById('modal-close-btn');

  if (!modal || !confirmBtn || !closeBtn) {
    console.warn("⚠️ 升级弹窗相关 DOM 元素未找到");
    return;
  }

  // 全局拦截下载按钮点击
  document.body.addEventListener('click', (e) => {
    const downloadBtn = e.target.closest('.book-download-btn');
    if (downloadBtn) {
      // 排除弹窗内部的下载按钮
      if (downloadBtn.id === 'modal-download-btn') return;

      e.preventDefault();
      pendingDownloadUrl = downloadBtn.getAttribute('href') || '#';
      modal.classList.add('active');
    }
  });

  // “我已支付，开始下载” 按钮点击
  confirmBtn.addEventListener('click', () => {
    if (pendingDownloadUrl && pendingDownloadUrl !== '#') {
      window.open(pendingDownloadUrl, '_blank', 'noopener');
    }
    modal.classList.remove('active');
    pendingDownloadUrl = '';
  });

  // “暂不升级” 按钮点击
  closeBtn.addEventListener('click', () => {
    modal.classList.remove('active');
    pendingDownloadUrl = '';
  });

  // 点击遮罩层背景关闭弹窗
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('active');
      pendingDownloadUrl = '';
    }
  });
}

// 页面加载完成后加载数据并初始化
(function() {
  const init = () => {
    loadBooks();
    initSearch();
    initUpgradeModal();
  };
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
