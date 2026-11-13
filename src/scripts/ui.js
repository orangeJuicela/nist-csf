const base = document.body.dataset.base || "/";
const typeLabel = {
  function: "功能",
  category: "類別",
  subcategory: "子類別",
};

function normalize(value) {
  return String(value || "")
    .toLowerCase()
    .replaceAll("’", "'")
    .replaceAll("—", "-")
    .replaceAll("–", "-");
}

function searchItems(items, raw) {
  const query = normalize(raw).trim();
  if (!query) return [];
  const tokens = query.split(/\s+/);
  const scored = [];
  for (const item of items) {
    const fields = [
      normalize(item.id),
      normalize(item.name),
      normalize(item.navLabelZhTW),
      normalize(item.outcome),
      normalize(item.explanationZhTW),
    ];
    const blob = fields.join("\n");
    if (!tokens.every((token) => blob.includes(token))) continue;
    const id = fields[0];
    let score = 0;
    if (id === query) score += 120;
    else if (id.startsWith(query)) score += 80;
    else if (id.includes(query)) score += 45;
    if (fields[2].includes(query)) score += 25;
    if (fields[4].includes(query)) score += 12;
    scored.push({ item, score });
  }
  scored.sort((a, b) => b.score - a.score || a.item.id.localeCompare(b.item.id));
  return scored.slice(0, 30).map((entry) => entry.item);
}

let indexPromise;
function loadIndex() {
  if (!indexPromise) {
    indexPromise = fetch(`${base}search-index.json`).then((response) => {
      if (!response.ok) throw new Error("search index");
      return response.json();
    });
  }
  return indexPromise;
}

function renderResults(list, items) {
  list.replaceChildren();
  for (const item of items) {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = item.href;
    link.dataset.fn = item.functionId;
    const id = document.createElement("span");
    id.className = "hit-id";
    id.textContent = item.id;
    const title = document.createElement("span");
    title.className = "hit-title";
    const kind = typeLabel[item.elementType] || "";
    const label = item.navLabelZhTW || item.name || item.outcome || "";
    title.textContent = label ? `${kind} ${label}` : kind;
    const snip = document.createElement("span");
    snip.className = "hit-snip";
    snip.textContent = item.explanationZhTW;
    link.append(id, title, snip);
    li.append(link);
    list.append(li);
  }
}

function bindSearch(root, itemsLoaded) {
  const input = root.querySelector("[data-search-input]");
  const status = root.querySelector("[data-search-status]");
  const list = root.querySelector("[data-search-results]");
  if (!input || !status || !list) return;

  const run = async () => {
    const query = input.value.trim();
    if (root.hasAttribute("data-search-autoload")) {
      const url = new URL(location.href);
      if (query) url.searchParams.set("q", query);
      else url.searchParams.delete("q");
      history.replaceState(null, "", url);
    }
    if (!query) {
      status.textContent = "輸入 ID、英文成果或中文說明。例如 GV.OC-03、存取控制、backup。";
      list.replaceChildren();
      return;
    }
    try {
      const items = await itemsLoaded;
      const hits = searchItems(items, query);
      status.textContent = hits.length ? `${hits.length} 筆結果` : "沒有符合的項目";
      renderResults(list, hits);
    } catch {
      status.textContent = "搜尋索引載入失敗。請改用目錄。";
    }
  };

  input.addEventListener("input", run);
  if (root.hasAttribute("data-search-autoload")) {
    const initial = new URLSearchParams(location.search).get("q");
    if (initial) input.value = initial;
  }
  run();
}

function setupToc() {
  document.body.classList.add("js");
  const toc = document.querySelector(".toc");
  const toggle = document.querySelector("[data-toc-toggle]");
  const backdrop = document.querySelector(".backdrop");
  const close = () => {
    document.body.classList.remove("toc-open");
    toggle?.setAttribute("aria-expanded", "false");
  };
  toggle?.addEventListener("click", () => {
    const open = !document.body.classList.contains("toc-open");
    document.body.classList.toggle("toc-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
  backdrop?.addEventListener("click", close);
  toc?.querySelectorAll("a").forEach((link) => link.addEventListener("click", close));
}

function setupSearch() {
  const dialog = document.querySelector("#search-dialog");
  const openButton = document.querySelector("[data-open-search]");
  const loaded = loadIndex();
  document.querySelectorAll("[data-search]").forEach((root) => bindSearch(root, loaded));
  openButton?.addEventListener("click", () => {
    dialog?.showModal();
    dialog?.querySelector("[data-search-input]")?.focus();
  });
  dialog?.querySelector("[data-search-close]")?.addEventListener("click", () => dialog.close());
  document.addEventListener("keydown", (event) => {
    const target = event.target;
    const typing = target instanceof HTMLElement && (target.closest("input, textarea") || target.isContentEditable);
    if (event.key === "/" && !typing && dialog && !dialog.open) {
      event.preventDefault();
      dialog.showModal();
      dialog.querySelector("[data-search-input]")?.focus();
    }
    if (event.key === "Escape") document.body.classList.remove("toc-open");
  });
}

setupToc();
setupSearch();
