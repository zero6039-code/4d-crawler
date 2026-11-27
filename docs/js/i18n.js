(function () {
  const sw = document.getElementById("lang-switch");
  const btn = document.getElementById("lang-btn");
  const menu = document.getElementById("lang-menu");
  if (!sw || !btn || !menu) return;

  const packs = {};
  const targets = [];
  document.querySelectorAll("[data-i18n]").forEach(function (el) {
    const keys = el.getAttribute("data-i18n").split("|");
    let i = 0;
    Array.prototype.forEach.call(el.childNodes, function (n) {
      if (n.nodeType === 3 && n.nodeValue.trim() && keys[i]) {
        targets.push({ node: n, original: n.nodeValue, key: keys[i] });
        i++;
      }
    });
  });

  window.i18n = function (key) {
    const lang = document.documentElement.dataset.lang || "en";
    const dict = packs[lang] || packs.en;
    return (dict && dict[key]) || key;
  };

  function syncTheme() {
    const body = getComputedStyle(document.body);
    const root = getComputedStyle(document.documentElement);
    const bg = body.backgroundColor !== "rgba(0, 0, 0, 0)" ? body.backgroundColor : (root.backgroundColor || "#fff");
    menu.style.background = bg;
    menu.style.color = body.color || root.color;
  }

  function closeMenu() {
    sw.classList.remove("open");
    btn.setAttribute("aria-expanded", "false");
  }

  async function apply(lang) {
    if (!packs[lang]) {
      const res = await fetch("i18n/" + lang + ".json?v=2");
      if (!res.ok) throw new Error("i18n " + lang);
      packs[lang] = await res.json();
    }
    const dict = packs[lang];
    targets.forEach(function (t) {
      t.node.nodeValue = dict[t.key] || t.original;
    });
    document.dispatchEvent(new CustomEvent("i18nchange", { detail: lang }));
  }

  function select(lang) {
    document.documentElement.dataset.lang = lang;
    try { localStorage.setItem("my4d-lang", lang); } catch (e) {}
    apply(lang).catch(function (err) { console.warn("i18n load failed", err); });
    closeMenu();
  }

  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    syncTheme();
    const open = sw.classList.toggle("open");
    btn.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", function (e) {
    if (!sw.contains(e.target)) closeMenu();
  });
  sw.querySelectorAll("[data-lang]").forEach(function (item) {
    item.addEventListener("click", function () { select(item.dataset.lang); });
  });

  let saved = "en";
  try { saved = localStorage.getItem("my4d-lang") || "en"; } catch (e) {}
  document.documentElement.dataset.lang = saved;
  apply(saved).catch(function () {});
})();
