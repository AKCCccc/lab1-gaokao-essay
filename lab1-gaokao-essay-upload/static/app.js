const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const SAMPLES = [
  {
    label: "本手、妙手、俗手",
    title: "本手、妙手、俗手",
    genre: "议论文",
    material:
      "“本手、妙手、俗手”是围棋的三个术语。本手是指合乎棋理的正规下法；妙手是指出人意料的精妙下法；俗手是指貌似合理，而从全局看通常会受损的下法。对于初学者而言，应该从本手开始，本手的功夫扎实了，棋力才会提高。一些初学者热衷于追求妙手，而忽视更为常用的本手。本手是基础，妙手是创造。一般来说，对本手理解深刻，才可能出现妙手；否则，难免下出俗手，水平也不易提升。以上材料对我们颇具启示意义。请结合材料写一篇文章，体现你的感悟与思考。",
  },
  {
    label: "绿水青山图",
    title: "绿水青山图",
    genre: "散文",
    material: "请以“绿水青山图”为题，写一篇议论性散文，表达你对人与自然关系的思考。",
  },
  {
    label: "乐观，便是希望",
    title: "乐观，便是希望",
    genre: "议论文",
    material: "生活并不会总是万里晴空，总会有风霜雨雪时。请以“乐观，便是希望”为题，写一篇文章。",
  },
  {
    label: "没有人是一座孤岛",
    title: "没有人是一座孤岛",
    genre: "议论文",
    material: "有人感叹，现代社会人与人之间的距离越来越远。请以“没有人是一座孤岛”为题，写一篇文章，谈谈你的思考。",
  },
  {
    label: "可为与有为",
    title: "可为与有为",
    genre: "议论文",
    material: "请以“可为与有为”为题，写一篇文章，体现你的感悟与思考。",
  },
];

const HISTORY_KEY = "wenxin_essay_history_v1";
const EMPTY_COPY = {
  essay: {
    title: "好文章，从审题开始",
    text: "输入题目，点击「生成满分作文」。AI 会先立骨架，再填血肉。",
  },
  outline: {
    title: "先立骨架，再填血肉",
    text: "点击左侧「生成写作大纲」，先看 AI 如何审题、立意、搭结构。",
  },
  review: {
    title: "让 AI 按评分标准阅卷",
    text: "生成作文后点击「AI 阅卷」，查看分项得分、亮点与升格示范。",
  },
};

const state = {
  outline: "",
  outlineSig: "",
  essay: "",
  review: "",
  activeTab: "essay",
  busy: null,
  controller: null,
  demo: false,
  renderRaf: null,
};

const titleEl = $("#title");
const materialEl = $("#material");
const genreEl = $("#genre");
const wordCountEl = $("#wordCount");
const styleEl = $("#style");
const modeEl = $("#mode");
const extraEl = $("#extra");
const modeHint = $("#modeHint");
const outlineBtn = $("#outlineBtn");
const generateBtn = $("#generateBtn");
const generateLabel = $("#generateLabel");
const reviewBtn = $("#reviewBtn");
const copyBtn = $("#copyBtn");
const downloadBtn = $("#downloadBtn");
const wordBadge = $("#wordBadge");
const emptyState = $("#emptyState");
const essayView = $("#essayView");
const outlineView = $("#outlineView");
const reviewView = $("#reviewView");
const statusBar = $("#statusBar");
const statusText = $("#statusText");
const historyList = $("#historyList");
const toastEl = $("#toast");

function escapeName(name) {
  return String(name || "高考作文").replace(/[\\/:*?"<>|]/g, "_").slice(0, 40);
}

function countWords(text) {
  return (text || "").replace(/\s/g, "").length;
}

function formSignature() {
  return JSON.stringify([
    titleEl.value.trim(),
    materialEl.value.trim(),
    genreEl.value,
    wordCountEl.value,
    styleEl.value,
    modeEl.value,
    extraEl.value.trim(),
  ]);
}

function payload() {
  const title = titleEl.value.trim();
  if (!title) {
    throw new Error("请先填写作文题目。");
  }
  return {
    title,
    material: materialEl.value.trim(),
    genre: genreEl.value,
    word_count: Number(wordCountEl.value),
    style: styleEl.value,
    extra: extraEl.value.trim(),
    mode: modeEl.value,
    outline: state.outlineSig === formSignature() ? state.outline : "",
  };
}

function toast(message, duration = 2600) {
  toastEl.textContent = message;
  toastEl.classList.add("show");
  window.clearTimeout(toastEl._timer);
  toastEl._timer = window.setTimeout(() => toastEl.classList.remove("show"), duration);
}

function setStatus(text, type = "loading") {
  statusBar.classList.remove("hidden", "error", "done");
  if (type === "error") statusBar.classList.add("error");
  if (type === "done") statusBar.classList.add("done");
  statusBar.classList.toggle("hidden", false);
  statusText.textContent = text;
}

function hideStatus() {
  statusBar.classList.add("hidden");
}

function syncButtons() {
  const busy = state.busy;
  outlineBtn.disabled = busy !== null;
  generateBtn.disabled = busy !== null && busy !== "essay";
  generateLabel.textContent = busy === "essay" ? "停止生成" : "生成满分作文";
  generateBtn.classList.toggle("is-stopping", busy === "essay");
  reviewBtn.disabled = busy !== null || !state.essay;
  copyBtn.disabled = !activeContent();
  downloadBtn.disabled = !activeContent();
  refreshBadge();
  document.body.setAttribute("aria-busy", busy === null ? "false" : "true");
}

function activeContent() {
  if (state.activeTab === "essay") return state.essay;
  if (state.activeTab === "outline") return state.outline;
  if (state.activeTab === "review") return state.review;
  return "";
}

function refreshEmptyState() {
  const hasContent =
    state.activeTab === "essay"
      ? Boolean(state.essay) || state.busy === "essay"
      : state.activeTab === "outline"
        ? Boolean(state.outline)
        : Boolean(state.review);

  emptyState.classList.toggle("hidden", hasContent);
  essayView.classList.toggle("hidden", state.activeTab !== "essay" || !hasContent);
  outlineView.classList.toggle("hidden", state.activeTab !== "outline" || !hasContent);
  reviewView.classList.toggle("hidden", state.activeTab !== "review" || !hasContent);

  if (!hasContent) {
    const copy = EMPTY_COPY[state.activeTab] || EMPTY_COPY.essay;
    const h = emptyState.querySelector("h3");
    const p = emptyState.querySelector("p");
    if (h) h.textContent = copy.title;
    if (p) p.textContent = copy.text;
  }
}

function refreshBadge() {
  const count = countWords(state.essay);
  wordBadge.textContent = state.busy === "essay" ? `${count} 字 · 生成中` : `${count} 字`;
}

function renderEssay(text) {
  essayView.textContent = "";
  const blocks = String(text || "")
    .replace(/\r/g, "")
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!blocks.length) return;

  const nearBottom =
    essayView.scrollHeight - essayView.scrollTop - essayView.clientHeight < 100;

  const title = document.createElement("h3");
  title.textContent = blocks[0];
  essayView.appendChild(title);

  for (let i = 1; i < blocks.length; i += 1) {
    const p = document.createElement("p");
    p.textContent = blocks[i];
    essayView.appendChild(p);
  }

  if (nearBottom) {
    essayView.scrollTop = essayView.scrollHeight;
  }
}

function scheduleEssayRender() {
  refreshBadge();
  if (state.renderRaf) return;
  state.renderRaf = window.requestAnimationFrame(() => {
    state.renderRaf = null;
    renderEssay(state.essay);
  });
}

function renderOutline() {
  outlineView.textContent = state.outline;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return map[char];
  });
}

function renderMarkdown(text) {
  const inline = (value) =>
    value
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");

  const lines = escapeHtml(text).split(/\r?\n/);
  let html = "";
  let inList = false;

  const closeList = () => {
    if (inList) {
      html += "</ul>";
      inList = false;
    }
  };

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      closeList();
      return;
    }

    const heading = trimmed.match(/^#{1,6}\s+(.*)$/);
    if (heading) {
      closeList();
      html += `<h4>${inline(heading[1])}</h4>`;
      return;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      if (!inList) {
        html += "<ul>";
        inList = true;
      }
      html += `<li>${inline(trimmed.replace(/^[-*]\s+/, ""))}</li>`;
      return;
    }

    if (/^>\s?/.test(trimmed)) {
      closeList();
      html += `<blockquote>${inline(trimmed.replace(/^>\s?/, ""))}</blockquote>`;
      return;
    }

    closeList();
    html += `<p>${inline(trimmed)}</p>`;
  });

  closeList();
  return html;
}

function renderReview() {
  if (!state.review) {
    reviewView.textContent = "";
    return;
  }
  reviewView.innerHTML = renderMarkdown(state.review);
}

function setTab(tab, options = {}) {
  state.activeTab = tab;
  $$(".tab").forEach((btn) => {
    const active = btn.dataset.tab === tab;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-selected", active ? "true" : "false");
  });
  refreshEmptyState();
  syncButtons();

  if (tab === "review" && !options.silent && !state.review && state.essay && state.busy === null) {
    runReview();
  }
}

function loadHistory() {
  try {
    const raw = window.localStorage.getItem(HISTORY_KEY);
    const list = raw ? JSON.parse(raw) : [];
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
}

function persistHistory(list) {
  try {
    window.localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, 8)));
  } catch {
    /* 本地存储不可用时静默忽略 */
  }
}

function renderHistory() {
  const list = loadHistory();
  historyList.textContent = "";
  if (!list.length) {
    const li = document.createElement("li");
    li.className = "history-empty";
    li.textContent = "还没有历史记录，生成后会保存在本机。";
    historyList.appendChild(li);
    return;
  }

  list.forEach((item) => {
    const li = document.createElement("li");
    li.className = "history-item";
    li.title = "点击载入这次生成";

    const title = document.createElement("span");
    title.className = "h-title";
    title.textContent = item.title || "未命名作文";

    const time = document.createElement("span");
    time.className = "h-time";
    time.textContent = item.time || "";

    li.appendChild(title);
    li.appendChild(time);
    li.addEventListener("click", () => {
      state.essay = item.essay || "";
      state.outline = item.outline || "";
      state.review = item.review || "";
      state.outlineSig = "";
      titleEl.value = item.title || "";
      genreEl.value = item.genre || "议论文";
      setTab("essay", { silent: true });
      renderEssay(state.essay);
      renderOutline();
      renderReview();
      refreshBadge();
      syncButtons();
      $("#workspace").scrollIntoView({ behavior: "smooth", block: "start" });
      toast("已载入历史作文");
    });

    historyList.appendChild(li);
  });
}

function saveHistory() {
  if (!state.essay || countWords(state.essay) < 80) return;
  const list = loadHistory().filter((item) => item.essay !== state.essay);
  const now = new Date();
  const time = now.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
  list.unshift({
    id: Date.now(),
    title: titleEl.value.trim() || "未命名作文",
    genre: genreEl.value,
    essay: state.essay,
    outline: state.outline,
    review: state.review,
    time,
  });
  persistHistory(list);
  renderHistory();
}

function renderChips() {
  const wrap = $("#titleChips");
  wrap.textContent = "";
  SAMPLES.forEach((sample) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.textContent = sample.label;
    btn.addEventListener("click", () => {
      titleEl.value = sample.title;
      materialEl.value = sample.material;
      genreEl.value = sample.genre;
      state.outline = "";
      state.outlineSig = "";
      renderOutline();
      toast(`已填入示例：${sample.label}`);
    });
    wrap.appendChild(btn);
  });
}

async function postJSON(path, body, signal) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    let message = `请求失败（HTTP ${response.status}）`;
    try {
      const data = await response.json();
      if (data && data.detail) message = typeof data.detail === "string" ? data.detail : message;
    } catch {
      /* 忽略非 JSON 错误体 */
    }
    throw new Error(message);
  }
  return response;
}

async function generateOutline() {
  if (state.busy) return;
  let body;
  try {
    body = payload();
  } catch (error) {
    toast(error.message);
    titleEl.focus();
    return;
  }

  state.busy = "outline";
  syncButtons();
  setTab("outline", { silent: true });
  setStatus("正在审题、立意、搭建结构…");

  try {
    const response = await postJSON("/api/outline", body);
    const data = await response.json();
    state.outline = data.outline || "";
    state.outlineSig = formSignature();
    renderOutline();
    setTab("outline", { silent: true });
    setStatus("大纲已生成，可继续生成正文。", "done");
    if (data.demo) toast("当前为演示模式：内容为内置示例。");
  } catch (error) {
    setStatus(error.message, "error");
    toast(error.message, 4000);
  } finally {
    state.busy = null;
    syncButtons();
  }
}

function handleStreamEvent(data) {
  if (data.type === "start") {
    setStatus(data.demo ? "演示模式 · 正在生成正文…" : "正在依纲成文…");
    return;
  }

  if (data.type === "delta") {
    state.essay += data.content || "";
    scheduleEssayRender();
    return;
  }

  if (data.type === "done") {
    renderEssay(state.essay);
    refreshBadge();
    setStatus(
      data.demo
        ? `演示模式完成 · 共 ${data.word_count} 字`
        : `生成完成 · 共 ${data.word_count} 字`,
      "done",
    );
    return;
  }

  if (data.type === "error") {
    setStatus(data.message || "生成失败，请重试。", "error");
    toast(data.message || "生成失败，请重试。", 5000);
  }
}

async function generateEssay() {
  if (state.busy === "essay") {
    state.controller?.abort();
    return;
  }
  if (state.busy) return;

  let body;
  try {
    body = payload();
  } catch (error) {
    toast(error.message);
    titleEl.focus();
    return;
  }

  state.essay = "";
  state.review = "";
  state.activeTab = "essay";
  state.busy = "essay";
  state.controller = new AbortController();
  renderEssay("");
  renderReview();
  renderOutline();
  refreshBadge();
  setTab("essay", { silent: true });
  syncButtons();
  setStatus(body.mode === "fast" ? "正在审题并直接成文…" : "正在审题立纲，随后成文…");

  try {
    const response = await postJSON("/api/essay", body, state.controller.signal);
    if (!response.body) throw new Error("浏览器不支持流式读取。");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let index = buffer.indexOf("\n\n");
      while (index !== -1) {
        const raw = buffer.slice(0, index);
        buffer = buffer.slice(index + 2);
        const line = raw.split("\n").find((item) => item.startsWith("data:"));
        if (line) {
          try {
            handleStreamEvent(JSON.parse(line.slice(5).trim()));
          } catch {
            /* 忽略无法解析的事件 */
          }
        }
        index = buffer.indexOf("\n\n");
      }
    }

    renderEssay(state.essay);
    refreshBadge();
    if (state.essay) {
      setStatus(`生成完成 · 共 ${countWords(state.essay)} 字`, "done");
      saveHistory();
    }
  } catch (error) {
    if (error.name === "AbortError") {
      setStatus("已停止生成，保留当前内容。", "done");
      renderEssay(state.essay);
      refreshBadge();
      saveHistory();
    } else {
      setStatus(error.message || "生成失败，请重试。", "error");
      toast(error.message || "生成失败，请重试。", 5000);
    }
  } finally {
    state.busy = null;
    state.controller = null;
    syncButtons();
  }
}

async function runReview() {
  if (state.busy || !state.essay) {
    if (!state.essay) toast("请先生成一篇作文，再让 AI 阅卷。");
    return;
  }

  state.activeTab = "review";
  setTab("review", { silent: true });
  state.busy = "review";
  state.review = "";
  renderReview();
  syncButtons();
  setStatus("阅卷中：按评分标准逐项打分…");

  try {
    const response = await postJSON("/api/review", {
      title: titleEl.value.trim(),
      essay: state.essay,
    });
    const data = await response.json();
    state.review = data.review || "";
    renderReview();
    refreshEmptyState();
    setStatus("阅卷完成，可对照建议修改。", "done");
    saveHistory();
    if (data.demo) toast("当前为演示模式：点评为内置示例。");
  } catch (error) {
    setStatus(error.message, "error");
    toast(error.message, 4000);
  } finally {
    state.busy = null;
    syncButtons();
  }
}

function downloadCurrent() {
  const content = activeContent();
  if (!content) {
    toast("当前没有可下载的内容。");
    return;
  }

  const label =
    state.activeTab === "essay" ? "" : state.activeTab === "outline" ? "写作大纲" : "AI阅卷点评";
  const title = titleEl.value.trim() || "高考作文";
  const text = label ? `${title}\n【${label}】\n\n${content}` : content;
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${escapeName(title)}-${label || "作文"}.txt`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  toast("已下载为 txt 文件");
}

async function copyCurrent() {
  const content = activeContent();
  if (!content) {
    toast("当前没有可复制的内容。");
    return;
  }
  try {
    await navigator.clipboard.writeText(content);
    toast("已复制到剪贴板");
  } catch {
    const area = document.createElement("textarea");
    area.value = content;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    toast("已复制到剪贴板");
  }
}

function bindEvents() {
  outlineBtn.addEventListener("click", generateOutline);
  generateBtn.addEventListener("click", generateEssay);
  reviewBtn.addEventListener("click", runReview);
  copyBtn.addEventListener("click", copyCurrent);
  downloadBtn.addEventListener("click", downloadCurrent);

  $$(".tab").forEach((btn) => {
    btn.addEventListener("click", () => setTab(btn.dataset.tab));
  });

  $("#clearHistory").addEventListener("click", () => {
    if (!loadHistory().length) return;
    persistHistory([]);
    renderHistory();
    toast("历史记录已清空");
  });

  modeEl.addEventListener("change", () => {
    modeHint.textContent =
      modeEl.value === "fast"
        ? "快速模式跳过显式大纲，适合快速试写；追求稳定高分建议使用标准模式。"
        : "标准模式会先审题立纲，再依据大纲成文，质量更稳定。";
  });

  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      generateEssay();
    }
  });

  [titleEl, materialEl, extraEl].forEach((el) => {
    el.addEventListener("input", () => {
      if (state.outline && state.outlineSig !== formSignature()) {
        state.outline = "";
        state.outlineSig = "";
        renderOutline();
      }
      syncButtons();
    });
  });
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    state.demo = Boolean(data.demo_mode);
    if (state.demo) {
      modeHint.textContent = "未检测到可用 API Key：当前使用内置演示内容，配置 .env 后即可调用真实模型。";
    } else {
      modeHint.textContent = `当前模型：${data.model} · 标准模式会先审题立纲，再依据大纲成文。`;
    }
  } catch {
    modeHint.textContent = "无法连接后端服务，请确认 uvicorn 已启动。";
  }
}

function init() {
  renderChips();
  renderHistory();
  bindEvents();
  refreshEmptyState();
  refreshBadge();
  syncButtons();
  checkHealth();
}

init();
