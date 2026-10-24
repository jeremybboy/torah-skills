const chapterEl = document.querySelector("#chapter");
const homeEl = document.querySelector("#home");
const chapterNavEl = document.querySelector("#chapter-nav");
let chapters = {};
let mediaCollections = {};

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
  text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" loading="lazy">');
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

    const image = line.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (image) {
      closeLists(state, html);
      html.push(`<figure class="chapter-figure"><img src="${escapeHtml(image[2])}" alt="${escapeHtml(image[1])}" loading="lazy"></figure>`);
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
  document.querySelectorAll("[data-chapter]").forEach((link) => {
    link.classList.toggle("active", link.dataset.chapter === slug);
  });
}

function renderChapterNav(items) {
  chapterNavEl.innerHTML = items
    .map((chapter) => `<a href="#${escapeHtml(chapter.slug)}" data-chapter="${escapeHtml(chapter.slug)}">${escapeHtml(chapter.title)}</a>`)
    .join("");
}

function isValidYouTubeId(value) {
  return /^[A-Za-z0-9_-]{11}$/.test(value);
}

function mediaCard(video, index) {
  const language = video.language === "fr" ? "Français" : "English";
  const watchUrl = `https://www.youtube.com/watch?v=${encodeURIComponent(video.youtubeId)}`;
  const thumbnailUrl = `https://i.ytimg.com/vi/${encodeURIComponent(video.youtubeId)}/hqdefault.jpg`;

  return `
    <article class="media-card">
      <button class="media-thumbnail" type="button" data-video-index="${index}" aria-label="Play ${escapeHtml(video.title)}">
        <img src="${thumbnailUrl}" alt="" loading="lazy">
        <span class="media-play-icon" aria-hidden="true">▶</span>
      </button>
      <div class="media-card-body">
        <div class="media-meta"><span>${language}</span><span>${escapeHtml(video.format)}</span></div>
        <h3>${escapeHtml(video.title)}</h3>
        <p class="media-channel">${escapeHtml(video.channel)}</p>
        <p>${escapeHtml(video.relation)}</p>
        <div class="media-actions">
          <button class="media-play-button" type="button" data-video-index="${index}">Play here</button>
          <a href="${watchUrl}" target="_blank" rel="noreferrer">Open on YouTube</a>
        </div>
      </div>
    </article>`;
}

function renderMediaExplorer(chapterSlug) {
  const currentCollection = mediaCollections[chapterSlug];
  if (!currentCollection) return;

  const comparisonCollection = mediaCollections[currentCollection.compareWith];
  const collectionList = [currentCollection, comparisonCollection].filter(Boolean);
  let activeCollection = currentCollection;
  let activeLanguage = "all";

  chapterEl.insertAdjacentHTML(
    "beforeend",
    `<section class="media-explorer" aria-labelledby="media-explorer-title">
      <div class="media-explorer-heading">
        <p class="media-kicker">Explore in other formats</p>
        <h2 id="media-explorer-title">Watch, compare, and return to the text</h2>
        <p>Six human-review candidates: three French and three English. The player opens inside this page; YouTube remains available as a fallback.</p>
      </div>
      <div class="media-collection-tabs" role="group" aria-label="Parashah media collection"></div>
      <div class="media-collection-summary" aria-live="polite"></div>
      <div class="media-language-filters" role="group" aria-label="Video language"></div>
      <div class="media-stage" hidden></div>
      <div class="media-grid"></div>
      <p class="media-editorial-note">Editorial test only. External teaching is labeled by format and does not replace the source chain or imply endorsement of every claim.</p>
    </section>`,
  );

  const explorer = chapterEl.querySelector(".media-explorer");
  const tabsEl = explorer.querySelector(".media-collection-tabs");
  const summaryEl = explorer.querySelector(".media-collection-summary");
  const filtersEl = explorer.querySelector(".media-language-filters");
  const stageEl = explorer.querySelector(".media-stage");
  const gridEl = explorer.querySelector(".media-grid");

  function closePlayer() {
    stageEl.hidden = true;
    stageEl.innerHTML = "";
  }

  function playVideo(video) {
    if (!isValidYouTubeId(video.youtubeId)) return;
    const watchUrl = `https://www.youtube.com/watch?v=${encodeURIComponent(video.youtubeId)}`;
    stageEl.innerHTML = `
      <div class="media-player-frame">
        <iframe
          src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(video.youtubeId)}?rel=0"
          title="${escapeHtml(video.title)}"
          loading="lazy"
          referrerpolicy="strict-origin-when-cross-origin"
          allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowfullscreen></iframe>
      </div>
      <div class="media-stage-caption">
        <div><strong>${escapeHtml(video.title)}</strong><span>${escapeHtml(video.channel)}</span></div>
        <a href="${watchUrl}" target="_blank" rel="noreferrer">Open on YouTube</a>
        <button type="button" class="media-close-player">Close player</button>
      </div>`;
    stageEl.hidden = false;
    stageEl.querySelector(".media-close-player").addEventListener("click", closePlayer);
    stageEl.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function paint() {
    tabsEl.innerHTML = collectionList
      .map(
        (collection) => `<button type="button" data-collection="${escapeHtml(collection.slug)}" aria-pressed="${collection.slug === activeCollection.slug}">${escapeHtml(collection.title)}</button>`,
      )
      .join("");
    summaryEl.innerHTML = `<strong>${escapeHtml(activeCollection.title)}</strong><span>${escapeHtml(activeCollection.summary)}</span>`;
    filtersEl.innerHTML = [
      ["all", "All 6"],
      ["fr", "Français"],
      ["en", "English"],
    ]
      .map(
        ([value, label]) => `<button type="button" data-language="${value}" aria-pressed="${value === activeLanguage}">${label}</button>`,
      )
      .join("");

    const videos = activeCollection.videos.filter(
      (video) => activeLanguage === "all" || video.language === activeLanguage,
    );
    gridEl.innerHTML = videos.map(mediaCard).join("");

    tabsEl.querySelectorAll("[data-collection]").forEach((button) => {
      button.addEventListener("click", () => {
        activeCollection = mediaCollections[button.dataset.collection];
        activeLanguage = "all";
        closePlayer();
        paint();
      });
    });
    filtersEl.querySelectorAll("[data-language]").forEach((button) => {
      button.addEventListener("click", () => {
        activeLanguage = button.dataset.language;
        closePlayer();
        paint();
      });
    });
    gridEl.querySelectorAll("[data-video-index]").forEach((button) => {
      button.addEventListener("click", () => playVideo(videos[Number(button.dataset.videoIndex)]));
    });
  }

  paint();
}

async function loadChapterIndex() {
  const response = await fetch("chapters/index.json");
  if (!response.ok) throw new Error("Could not load chapters/index.json");
  const items = await response.json();
  chapters = Object.fromEntries(items.map((chapter) => [chapter.slug, chapter]));
  renderChapterNav(items);
}

async function loadMediaIndex() {
  const response = await fetch("media/collections.json");
  if (!response.ok) throw new Error("Could not load media/collections.json");
  const data = await response.json();
  mediaCollections = Object.fromEntries(
    data.collections.map((collection) => [collection.slug, collection]),
  );
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
    renderMediaExplorer(slug);
    document.title = `${chapter.title} | Torah Skills`;
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

Promise.all([loadChapterIndex(), loadMediaIndex()])
  .then(handleRoute)
  .catch((error) => {
    chapterNavEl.innerHTML = "";
    homeEl.hidden = true;
    chapterEl.hidden = false;
    chapterEl.innerHTML = `<p class="load-error">${escapeHtml(error.message)}. If you opened this from the filesystem, run a local web server or publish through GitHub Pages.</p>`;
  });
