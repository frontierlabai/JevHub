const isEnglish = document.documentElement.lang === 'en';
const state = { data: null, category: 'all', query: '', shown: 9, papersExpanded: false };
const labels = isEnglish ? { official: 'Official', research: 'Independent research', resources: 'Resources', tools: 'Tools', applications: 'Apps / integrations' } : { official: '官方项目', research: '独立研究', resources: '资源合集', tools: '开发工具', applications: '应用 / 集成' };
const $ = (selector) => document.querySelector(selector);
const visitCounter = $('#site-visit-counter');
if (visitCounter) {
  const showVisitFailure = () => {
    visitCounter.hidden = true;
    $('#visits-unavailable').hidden = false;
  };
  visitCounter.addEventListener('error', showVisitFailure);
  if (visitCounter.complete && !visitCounter.naturalWidth) showVisitFailure();
}
const formatNumber = (value) => new Intl.NumberFormat('zh-CN').format(value || 0);
const formatDate = (value) => value ? new Date(value).toLocaleDateString(isEnglish ? 'en-US' : 'zh-CN', { month: 'short', day: 'numeric' }) : '—';
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));

function renderStats(data) {
  $('#repo-count').textContent = formatNumber(data.repositories.length);
  $('#star-count').textContent = formatNumber(data.repositories.reduce((sum, item) => sum + item.stars, 0));
  $('#updated-at').textContent = formatDate(data.generated_at);
}

function renderBrief(data) {
  const brief = data.daily_brief;
  if (!brief) return;
  const rows = (brief.repositories || []).slice(0, 3);
  const names = rows.map((item) => `<a href="${escapeHTML(item.url)}" target="_blank" rel="noreferrer">${escapeHTML(item.name)}</a>`).join(isEnglish ? ', ' : '、');
  $('#brief-text').innerHTML = rows.length ? (isEnglish ? `This refresh found ${brief.count} new project(s): ${names}${brief.count > rows.length ? `, plus ${brief.count - rows.length} more` : ''}.` : `本次刷新发现 ${brief.count} 个新项目：${names}${brief.count > rows.length ? `，以及另外 ${brief.count - rows.length} 个项目` : ''}。`) : (isEnglish ? 'No new projects were found in this refresh.' : '本次刷新没有发现新增项目。');
  const projects = brief.repositories || [];
  const toggle = $('#brief-toggle');
  const panel = $('#brief-projects');
  panel.innerHTML = projects.map((item) => `<article class="brief-project"><div><a href="${escapeHTML(item.url)}" target="_blank" rel="noreferrer">${escapeHTML(item.name)}</a><span class="stars">☆ ${formatNumber(item.stars)}</span></div><p>${escapeHTML(isEnglish ? (item.description_en || item.description) : item.description)}</p></article>`).join('');
  toggle.hidden = !projects.length;
  toggle.onclick = () => {
    const expanded = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(expanded));
    const label = isEnglish ? (expanded ? 'Hide new projects' : 'Show new projects') : (expanded ? '收起新增项目' : '展开新增项目');
    toggle.setAttribute('aria-label', label);
    toggle.title = label;
    panel.hidden = !expanded;
  };
}

function renderFilters(data) {
  const counts = data.repositories.reduce((map, item) => { map[item.category] = (map[item.category] || 0) + 1; return map; }, {});
  const filters = [['all', isEnglish ? 'All' : '全部', data.repositories.length], ...Object.entries(labels).map(([key, name]) => [key, name, counts[key] || 0])];
  $('#filters').innerHTML = filters.map(([key, name, count]) => `<button class="filter ${state.category === key ? 'active' : ''}" data-category="${escapeHTML(key)}" aria-pressed="${state.category === key}">${escapeHTML(name)} <span>${count}</span></button>`).join('');
  $('#filters').querySelectorAll('.filter').forEach((button) => button.addEventListener('click', () => { state.category = button.dataset.category; state.shown = 9; renderFilters(data); renderProjects(data); }));
}

function filteredProjects(data) {
  return data.repositories.filter((item) => {
    const matchesCategory = state.category === 'all' || item.category === state.category;
    const haystack = `${item.name} ${item.description} ${item.description_en} ${labels[item.category] || ''}`.toLowerCase();
    return matchesCategory && haystack.includes(state.query.toLowerCase());
  });
}

function renderProjects(data) {
  const projects = filteredProjects(data);
  const visible = projects.slice(0, state.shown);
  $('#projects-grid').innerHTML = visible.length ? visible.map((item) => `<article class="project-card" data-category="${escapeHTML(item.category)}"><div class="project-meta"><span class="category">${escapeHTML(labels[item.category] || item.category)}</span><span class="stars">★ ${formatNumber(item.stars)}</span></div><div class="card-title"><a href="${escapeHTML(item.url)}" target="_blank" rel="noreferrer"><span class="repo-owner">${escapeHTML(item.name.split("/")[0])} /</span>${escapeHTML(item.name.split("/").slice(1).join("/") || item.name)}</a></div><p class="description">${escapeHTML((isEnglish ? item.description_en : item.description) || (isEnglish ? 'Open the repository for details.' : '打开仓库查看详情。'))}</p><div class="card-foot">${escapeHTML(item.language || '—')} · ${isEnglish ? 'Updated' : '更新于'} ${formatDate(item.pushed_at)}</div></article>`).join('') : `<p class="empty">${isEnglish ? 'No matching projects. Try another search or category.' : '没有匹配的项目，请尝试其他关键词或分类。'}</p>`;
  $('#project-results').textContent = isEnglish ? `Showing ${visible.length} of ${projects.length} projects` : `显示 ${visible.length} / ${projects.length} 个项目`;
  const all = $('#show-all-projects');
  all.hidden = projects.length <= state.shown;
  all.textContent = isEnglish ? `Show all ${projects.length} projects` : `显示全部 ${projects.length} 个项目`;
  all.onclick = () => { state.shown = projects.length; renderProjects(data); };
  const more = $('#load-more'); more.hidden = projects.length <= state.shown; more.onclick = () => { state.shown += 9; renderProjects(data); };
}

function renderPapers(data) {
  const rows = data.arxiv || [];
  $('#papers-list').innerHTML = rows.length ? rows.map((row, index) => {
    const authors = (row.authors || []).join(', ') || (isEnglish ? 'Unknown authors' : '作者未提供');
    const date = row.published_at ? new Date(row.published_at).toLocaleDateString(isEnglish ? 'en-US' : 'zh-CN', { year: 'numeric', month: 'short', day: 'numeric' }) : '—';
    return `<article class="paper" ${index >= 4 && !state.papersExpanded ? 'hidden' : ''}><div class="paper-meta"><span class="paper-label">arXiv · ${isEnglish ? 'Preprint' : '预印本'}</span><time datetime="${escapeHTML(row.published_at || '')}">${escapeHTML(date)}</time></div><a href="${escapeHTML(row.url)}" target="_blank" rel="noreferrer">${escapeHTML(row.title)}</a><p>${escapeHTML(authors)}</p>${row.summary ? `<details><summary>${isEnglish ? 'Read abstract' : '查看摘要'}</summary><p>${escapeHTML(row.summary)}</p></details>` : ''}</article>`;
  }).join('') : `<p class="empty">${isEnglish ? 'No recent arXiv papers are available.' : '暂无符合时间范围的 arXiv 论文。'}</p>`;
  const more = $('#papers-more');
  more.hidden = rows.length <= 4;
  more.setAttribute('aria-expanded', String(state.papersExpanded));
  more.textContent = state.papersExpanded ? (isEnglish ? 'Show fewer papers' : '收起论文') : (isEnglish ? `Show all ${rows.length} papers` : `展开全部 ${rows.length} 篇论文`);
  more.onclick = () => { state.papersExpanded = !state.papersExpanded; renderPapers(data); };
}

function renderRadar(data) {
  const definitions = [['hacker_news', 'Hacker News'], ['reddit', 'Reddit'], ['huggingface', 'Hugging Face'], ['news', isEnglish ? 'News / articles' : '新闻 / 文章']];
  $('#radar-grid').innerHTML = definitions.map(([key, title]) => {
    const rows = data[key] || [];
    const source = data.sources?.[key];
    const available = source?.state === 'ok';
    const status = rows.length
      ? `${rows.length} ${isEnglish ? 'discoveries' : '条相关发现'} · ${available ? (isEnglish ? 'Updated' : '已更新') : (isEnglish ? 'Cached' : '缓存')}`
      : available ? (isEnglish ? 'No matching results in this refresh' : '本次未检索到相关结果')
        : (isEnglish ? 'Automatic collection unavailable' : '自动抓取暂不可用');
    const renderRow = (row) => {
      const metadata = [row.publisher, row.published_at ? formatDate(row.published_at) : '', row.score != null ? `${formatNumber(row.score)} ${isEnglish ? 'points' : '分'}` : '', row.comments != null ? `${formatNumber(row.comments)} ${isEnglish ? 'comments' : '条评论'}` : '', row.likes != null ? `${formatNumber(row.likes)} likes` : '', row.downloads != null ? `${formatNumber(row.downloads)} ${isEnglish ? 'downloads' : '次下载'}` : ''].filter(Boolean).join(' · ');
      return `<div class="radar-entry"><a href="${escapeHTML(row.url)}" target="_blank" rel="noreferrer">${escapeHTML(row.title)}</a>${metadata ? `<p>${escapeHTML(metadata)}</p>` : ''}${row.summary ? `<p>${escapeHTML(row.summary)}</p>` : ''}</div>`;
    };
    let content = rows.slice(0, 3).map(renderRow).join('');
    if (rows.length > 3) content += `<details class="radar-more"><summary>${isEnglish ? `View all ${rows.length} items` : `查看全部 ${rows.length} 条`}</summary>${rows.slice(3).map(renderRow).join('')}</details>`;
    if (key === 'reddit') {
      if (!rows.length) {
        const curated = (data.curated_resources || []).filter((row) => {
          try { return /^(www\.)?reddit\.com$/.test(new URL(row.url).hostname); } catch { return false; }
        });
        if (curated.length) content += `<p class="radar-note">${isEnglish ? 'Curated discussions · not live results' : '精选讨论 · 非本次自动抓取'}</p>` + curated.map((row) => `<a href="${escapeHTML(row.url)}" target="_blank" rel="noreferrer">${escapeHTML(isEnglish ? (row.title_en || row.title) : row.title)}</a>`).join('');
      }
      content += `<a href="https://www.reddit.com/search/?q=Jev%20TypeSafe&amp;sort=new" target="_blank" rel="noreferrer">${isEnglish ? 'Search Reddit discussions' : '在 Reddit 搜索更多讨论'} ↗</a>`;
    }
    return `<article class="radar-card"><h3>${escapeHTML(title)}</h3><p>${status}</p>${content}</article>`;
  }).join('');
}

function renderResources(data) {
  $('#resources-count').textContent = isEnglish ? `${(data.curated_resources || []).length} resources` : `共 ${(data.curated_resources || []).length} 条资源`;
  $('#resources-list').innerHTML = (data.curated_resources || []).map((item) => `<article class="resource"><div><a href="${escapeHTML(item.url)}" target="_blank" rel="noreferrer">${escapeHTML(isEnglish ? (item.title_en || item.title) : item.title)}</a><p>${escapeHTML(isEnglish ? (item.description_en || item.description) : item.description)}</p></div><span class="resource-arrow">↗</span></article>`).join('');
}

async function init() {
  try {
    const localSite = window.location.pathname.includes('/site/');
    const dataRoot = localSite ? (isEnglish ? '../../data' : '../data') : (isEnglish ? '../data' : 'data');
    const response = await fetch(`${dataRoot}/latest.json`);
    if (!response.ok) throw new Error('data unavailable');
    state.data = await response.json();
    if (!state.data.daily_brief && state.data.generated_at) {
      const date = new Date(`${state.data.generated_at.slice(0, 10)}T00:00:00Z`);
      date.setUTCDate(date.getUTCDate() - 1);
      const history = await fetch(`${dataRoot}/history/${date.toISOString().slice(0, 10)}.json`);
      if (history.ok) {
        const snapshot = await history.json();
        const ids = new Set((snapshot.repositories || []).map((item) => String(item.id)));
        const rows = state.data.repositories.filter((item) => !ids.has(String(item.id)));
        state.data.daily_brief = { count: rows.length, repositories: rows };
      }
    }
    renderStats(state.data); renderBrief(state.data); renderFilters(state.data); renderProjects(state.data); renderPapers(state.data); renderRadar(state.data); renderResources(state.data);
    $('#search').addEventListener('input', (event) => { state.query = event.target.value.trim(); state.shown = 9; renderProjects(state.data); });
  } catch (error) {
    $('#load-more').hidden = true;
    $('#show-all-projects').hidden = true;
    const message = `<div class="empty">${isEnglish ? 'Data could not be loaded.' : '数据暂时加载失败。'} <button type="button" class="retry-data">${isEnglish ? 'Retry' : '重新加载'}</button></div>`;
    ['#projects-grid', '#papers-list', '#radar-grid', '#resources-list'].forEach((selector) => { $(selector).innerHTML = message; });
    document.querySelectorAll('.retry-data').forEach((button) => button.addEventListener('click', () => location.reload()));
  }
}
init();

// Keep the navigation tied to the section being read, including on mobile.
const sectionLinks = [...document.querySelectorAll('nav a[href^="#"]')];
const updateSectionNavigation = () => {
  const boundary = Math.min(180, window.innerHeight / 3);
  let current = null;
  sectionLinks.forEach((link) => {
    const section = document.querySelector(link.getAttribute('href'));
    if (section && section.getBoundingClientRect().top <= boundary &&
        (!current || section.offsetTop > current.section.offsetTop)) current = { link, section };
  });
  sectionLinks.forEach((link) => {
    if (current?.link === link) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
};
let navigationFrame = false;
window.addEventListener('scroll', () => {
  if (navigationFrame) return;
  navigationFrame = true;
  requestAnimationFrame(() => { updateSectionNavigation(); navigationFrame = false; });
}, { passive: true });
window.addEventListener('resize', updateSectionNavigation);
updateSectionNavigation();
