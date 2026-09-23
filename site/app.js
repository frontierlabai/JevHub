const state = { data: null, category: 'all', query: '', shown: 9 };
const labels = { official: '官方项目', research: '独立研究', resources: '资源合集', tools: '开发工具', applications: '应用 / 集成' };
const $ = (selector) => document.querySelector(selector);
const formatNumber = (value) => new Intl.NumberFormat('zh-CN').format(value || 0);
const formatDate = (value) => value ? new Date(value).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }) : '—';
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));

function renderStats(data) {
  $('#repo-count').textContent = formatNumber(data.repositories.length);
  $('#star-count').textContent = formatNumber(data.repositories.reduce((sum, item) => sum + item.stars, 0));
  $('#updated-at').textContent = formatDate(data.generated_at);
}

function renderBrief(data) {
  const brief = data.daily_brief;
  if (!brief) return;
  const rows = brief.repositories || [];
  const names = rows.map((item) => `<a href="${escapeHTML(item.url)}" target="_blank" rel="noreferrer">${escapeHTML(item.name)}</a>`).join('、');
  $('#brief-text').innerHTML = rows.length ? `本次刷新发现 ${brief.count} 个新项目：${names}${brief.count > rows.length ? `，以及另外 ${brief.count - rows.length} 个项目` : ''}。` : '本次刷新没有发现新增项目。';
}

function renderFilters(data) {
  const counts = data.repositories.reduce((map, item) => { map[item.category] = (map[item.category] || 0) + 1; return map; }, {});
  const filters = [['all', '全部', data.repositories.length], ...Object.entries(labels).map(([key, name]) => [key, name, counts[key] || 0])];
  $('#filters').innerHTML = filters.map(([key, name, count]) => `<button class="filter ${state.category === key ? 'active' : ''}" data-category="${escapeHTML(key)}" role="tab">${escapeHTML(name)} <span>${count}</span></button>`).join('');
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
  $('#projects-grid').innerHTML = visible.length ? visible.map((item, index) => `<article class="project-card"><span class="rank">${String(index + 1).padStart(2, '0')} / ${escapeHTML(labels[item.category] || 'PROJECT')}</span><div class="card-title"><a href="${escapeHTML(item.url)}" target="_blank" rel="noreferrer">${escapeHTML(item.name)}</a><span class="stars">★ ${formatNumber(item.stars)}</span></div><span class="category">${escapeHTML(labels[item.category] || item.category)}</span><p class="description">${escapeHTML(item.description || '暂无简介；打开仓库查看详情。')}</p><div class="card-foot">${escapeHTML(item.language || '—')} · updated ${formatDate(item.pushed_at)}</div></article>`).join('') : '<p class="empty">没有找到匹配的项目。试试别的关键词。</p>';
  const more = $('#load-more'); more.hidden = projects.length <= state.shown; more.onclick = () => { state.shown += 9; renderProjects(data); };
}

function renderRadar(data) {
  const definitions = [['hacker_news', 'Hacker News', 'points', 'comments'], ['reddit', 'Reddit', 'score', 'comments'], ['huggingface', 'Hugging Face', 'likes', 'downloads']];
  const cards = definitions.map(([key, title, metric, second]) => { const rows = data[key] || []; return `<article class="radar-card"><h3>${escapeHTML(title)}</h3><p>${rows.length ? `${rows.length} 条相关发现 · ${data.sources?.[key]?.state === 'ok' ? '已更新' : '缓存'}` : '暂无可展示结果'}</p>${rows.slice(0, 3).map((row) => `<a href="${escapeHTML(row.url)}" target="_blank" rel="noreferrer">${escapeHTML(row.title)}</a>`).join('')}</article>`; });
  $('#radar-grid').innerHTML = cards.join('');
}

function renderResources(data) {
  $('#resources-list').innerHTML = (data.curated_resources || []).slice(0, 6).map((item) => `<article class="resource"><div><a href="${escapeHTML(item.url)}" target="_blank" rel="noreferrer">${escapeHTML(item.title)}</a><p>${escapeHTML(item.description)}</p></div><span class="resource-arrow">↗</span></article>`).join('');
}

async function init() {
  try {
    const response = await fetch('../data/latest.json');
    if (!response.ok) throw new Error('data unavailable');
    state.data = await response.json();
    renderStats(state.data); renderBrief(state.data); renderFilters(state.data); renderProjects(state.data); renderRadar(state.data); renderResources(state.data);
    $('#search').addEventListener('input', (event) => { state.query = event.target.value.trim(); state.shown = 9; renderProjects(state.data); });
  } catch (error) {
    $('#projects-grid').innerHTML = '<p class="empty">数据暂时无法加载。请通过本地服务器打开此页面，或查看 README。</p>';
  }
}
init();
