const chapters = {
  devarim: {
    title: "Devarim",
    path: "chapters/devarim.md"
  },
  vaetchanan: {
    title: "Vaetchanan",
    path: "chapters/vaetchanan.md"
  }
};

const chapterEl = document.querySelector("#chapter");
const homeEl = document.querySelector("#home");
const navLinks = [...document.querySelectorAll("[data-chapter]")];

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderInline(value) {
  let text = escapeHtml(value);
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return text;
}

function closeLists(state, html) {
  if (state.list === "ul") html.push("</ul>");
  if (state.list === "ol") html.push("</ol>");
  state.list = null;
}

function markdownToHtml(markdown) {
  const html = [];
  const state = { list: null };
  const lines = markdown.split(/\r?\n/);

  for (const raw of lines) {
    const line = raw.trim();

    if (!line) {
      closeLists(state, html);
      continue;
    }

    if (/^-{3,}$/.test(line)) {
      closeLists(state, html);
      html.push("<hr>");
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      closeLists(state, html);
      const level = heading[1].length;
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      continue;
    }

    const ordered = line.match(/^\d+\.\s+(.+)$/);
    if (ordered) {
      if (state.list !== "ol") {
        closeLists(state, html);
        html.push("<ol>");
        state.list = "ol";
      }
      html.push(`<li>${renderInline(ordered[1])}</li>`);
      continue;
    }

    const unordered = line.match(/^[-*]\s+(.+)$/);
    if (unordered) {
      if (state.list !== "ul") {
        closeLists(state, html);
        html.push("<ul>");
        state.list = "ul";
      }
      html.push(`<li>${renderInline(unordered[1])}</li>`);
      continue;
    }

    closeLists(state, html);
    html.push(`<p>${renderInline(line)}</p>`);
  }

  closeLists(state, html);
  return html.join("\n");
}

function setActive(slug) {
  navLinks.forEach((link) => {
    link.classList.toggle("active", link.dataset.chapter === slug);
  });
}

async function loadChapter(slug) {
  const chapter = chapters[slug];
  if (!chapter) {
    chapterEl.hidden = true;
    homeEl.hidden = false;
    setActive(null);
    return;
  }

  homeEl.hidden = true;
  chapterEl.hidden = false;
  setActive(slug);
  chapterEl.innerHTML = "<p>Loading chapter...</p>";

  try {
    const response = await fetch(chapter.path);
    if (!response.ok) throw new Error(`Could not load ${chapter.path}`);
    const markdown = await response.text();
    chapterEl.innerHTML = markdownToHtml(markdown);
    document.title = `${chapter.title} | Torah Study Companion`;
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (error) {
    chapterEl.innerHTML = `<p class="load-error">${escapeHtml(error.message)}. If you opened this from the filesystem, run a local web server or publish through GitHub Pages.</p>`;
  }
}

function handleRoute() {
  const slug = window.location.hash.replace("#", "");
  loadChapter(slug);
}

window.addEventListener("hashchange", handleRoute);
handleRoute();

