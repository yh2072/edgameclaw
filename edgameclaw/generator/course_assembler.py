# Created by Yuqi Hang (github.com/yh2072)
"""Assembles the course platform — homepage with auth, payment simulation, and game navigation.

The visual style matches the pixel-art game aesthetic from the games themselves.
"""

import json
import os
from pathlib import Path

from .assembler import THEMES, get_theme, get_theme_css, DEFAULT_THEME
from .i18n import get_course_page_strings, COURSE_PAGE_STRINGS, LOCALE_NAMES, DEFAULT_LOCALE


def assemble_course_platform(manifest: dict, output_dir: str, locale: str = DEFAULT_LOCALE) -> str:
    """Generate the course platform index.html with auth, payment, and lesson navigation.

    Args:
        manifest: Course manifest dict from course_pipeline.
        output_dir: Base output directory for the course.
        locale: Language locale for UI strings (default: zh).

    Returns:
        Path to the generated index.html.
    """
    course = manifest["course"]
    games = manifest["games"]

    first_theme = games[0].get("theme", DEFAULT_THEME) if games else DEFAULT_THEME
    css = get_theme_css(first_theme)
    cp = get_course_page_strings(locale)

    import os as _os
    course_id = _os.path.basename(output_dir)
    games_html = _build_games_cards(games, output_dir, course_id=course_id, locale=locale)
    objectives_html = _build_objectives_list(course.get("learning_objectives", []))
    cover_script_tags, cover_render_calls = _build_cover_scripts(games)

    # Truncate long descriptions for the course page UI
    description = course.get("description", "")
    if len(description) > 200:
        # Cut at the last sentence boundary before 200 chars
        cut = description[:200].rfind("。")
        if cut < 50:
            cut = description[:200].rfind(".")
        if cut < 50:
            cut = 197
        description = description[:cut + 1] + "…"

    subtitle = course.get("subtitle", "")
    if len(subtitle) > 80:
        cut = subtitle[:80].rfind("·")
        if cut < 20:
            cut = 77
        subtitle = subtitle[:cut].rstrip() + " …"

    # Inject course_id into manifest so COURSE_ID is available in the page JS
    manifest_with_id = dict(manifest)
    manifest_with_id["course"] = dict(manifest["course"], id=course_id)

    html = COURSE_TEMPLATE
    html = html.replace("{{COURSE_TITLE}}", course.get("title", "EdGame Course"))
    html = html.replace("{{COURSE_SUBTITLE}}", subtitle)
    html = html.replace("{{COURSE_DESCRIPTION}}", description)
    html = html.replace("{{COURSE_SUBJECT}}", course.get("subject", ""))
    html = html.replace("{{COURSE_LEVEL}}", course.get("level", ""))
    html = html.replace("{{COURSE_TIME}}", course.get("estimated_time", ""))
    html = html.replace("{{TOTAL_LESSONS}}", str(len(games)))
    html = html.replace("{{OBJECTIVES_HTML}}", objectives_html)
    html = html.replace("{{GAMES_CARDS_HTML}}", games_html)
    html = html.replace("{{MANIFEST_JSON}}", json.dumps(manifest_with_id, ensure_ascii=False))
    html = html.replace("{{COVER_SCRIPT_TAGS}}", cover_script_tags)
    html = html.replace("{{COVER_RENDER_CALLS}}", cover_render_calls)

    for key, val in css.items():
        html = html.replace("{{T." + key + "}}", val)

    for key, val in cp.items():
        html = html.replace("{{U." + key + "}}", val)

    course_page_strings_json = json.dumps(COURSE_PAGE_STRINGS, ensure_ascii=False)
    locale_names_json = json.dumps(LOCALE_NAMES, ensure_ascii=False)
    lang_switcher_html = "".join(
        f'<button type="button" class="course-lang-opt" data-lang="{code}" title="{name}">{name}</button>'
        for code, name in LOCALE_NAMES.items()
    )
    html = html.replace("{{COURSE_PAGE_STRINGS_JSON}}", course_page_strings_json)
    html = html.replace("{{LOCALE_NAMES_JSON}}", locale_names_json)
    html = html.replace("{{LANG_SWITCHER_HTML}}", lang_switcher_html)

    output_path = Path(output_dir) / "index.html"
    output_path.write_text(html, encoding="utf-8")

    return str(output_path)


def _build_games_cards(games: list[dict], output_dir: str, course_id: str = "", locale: str = "zh") -> str:
    from .i18n import get_course_page_strings
    cp = get_course_page_strings(locale)
    cards = []
    for i, game in enumerate(games):
        theme_name = game.get("theme", DEFAULT_THEME)
        css = get_theme_css(theme_name)
        status_class = "available" if game["status"] == "success" else "locked"
        chunk_id = game.get("chunk_id", f"chunk-{i + 1}")
        # Use player URL so game loads from package (no raw HTML exposed)
        href = f"/play.html?course={course_id}&game={chunk_id}" if course_id and status_class == "available" else ""

        objectives_items = "".join(
            f'<span class="tag">{obj}</span>' for obj in game.get("learning_objectives", [])[:3]
        )

        btn_text = cp["btnStart"] if status_class == "available" else cp["btnLocked"]
        btn_i18n_key = "btnStart" if status_class == "available" else "btnLocked"

        ch_label = f"第{i+1}章" if locale == "zh" else f"CH.{i+1}"

        # Truncate long lesson titles and subtitles
        lesson_title = game.get("title", "")
        if len(lesson_title) > 30:
            lesson_title = lesson_title[:28] + "…"
        lesson_sub = game.get("subtitle", "")
        if len(lesson_sub) > 50:
            lesson_sub = lesson_sub[:48] + "…"

        # Cover art canvas — rendered by cover.js loaded at page bottom
        cover_html = (
            f'<canvas class="lesson-cover" id="cover-{chunk_id}" '
            f'width="128" height="96" '
            f'style="border-color:{css["accent"]}"></canvas>'
            if game.get("cover_js_src")
            else f'<div class="lesson-cover-fallback" style="border-color:{css["accent"]};color:{css["accent"]}">{_get_lesson_emoji(i)}</div>'
        )

        cards.append(f"""
        <div class="lesson-card {status_class}" data-lesson="{i}"
             style="--ca:{css['accent']};--ch:{css['highlight']};--cb:{css['border']};--cbg:{css['cardBg']};--cglow:{css['glowAccent']}">
          {cover_html}
          <div class="lesson-num">{ch_label}</div>
          <div class="lesson-body">
            <div class="lesson-title">{lesson_title}</div>
            <div class="lesson-sub">{lesson_sub}</div>
            <div class="lesson-tags">{objectives_items}</div>
          </div>
          <div class="lesson-right">
            <button class="play-btn" data-href="{href}" data-i18n="{btn_i18n_key}" style="border-color:{css['accent']};color:{css['highlight']}"
                    onclick="launchGame(this,{i})" {"disabled" if status_class == "locked" else ""}>
              {btn_text}
            </button>
            <div class="lesson-progress" id="progress-{i}">
              <div class="progress-fill" style="background:{css['accent']}"></div>
            </div>
          </div>
        </div>
        """)
    return "\n".join(cards)


def _build_cover_scripts(games: list[dict]) -> str:
    """Build script tags and canvas render calls for all game covers."""
    script_tags = []
    render_calls = []
    for game in games:
        src = game.get("cover_js_src")
        chunk_id = game.get("chunk_id", "")
        if src and chunk_id:
            script_tags.append(f'<script src="{src}"></script>')
            render_calls.append(
                f"  renderCover('{chunk_id}');"
            )
    return "\n".join(script_tags), "\n".join(render_calls)


def _build_objectives_list(objectives: list[str]) -> str:
    return "".join(f'<li>{obj}</li>' for obj in objectives)


def _get_lesson_emoji(index: int) -> str:
    icons = ["✦", "◈", "✿", "⚡", "◆", "★", "♦", "⊕"]
    return icons[index % len(icons)]


COURSE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="{{U.lang}}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="mobile-web-app-capable" content="yes">
<title>{{COURSE_TITLE}} — {{COURSE_SUBTITLE}}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.12);border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,0.25)}
*{scrollbar-width:thin;scrollbar-color:rgba(255,255,255,0.12) transparent}

html{min-height:100dvh;-webkit-text-size-adjust:100%}
body{
  background:{{T.bg}};color:{{T.text}};
  font-family:'PixelZH','Courier New',monospace;
  min-height:100vh;min-height:100dvh;overflow-x:hidden;
}

/* ── Header ── */
.header{
  position:fixed;top:0;left:0;right:0;z-index:100;
  background:rgba(8, 8, 11, 0.35);backdrop-filter:blur(32px) saturate(1.4);-webkit-backdrop-filter:blur(32px) saturate(1.4);
  border-bottom:2px solid {{T.border}};padding:0 24px;
  box-shadow:0 4px 30px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.03);
}
.header-inner{
  max-width:960px;margin:0 auto;height:52px;
  display:flex;align-items:center;justify-content:space-between;
}
.brand{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:700;color:{{T.highlight}};letter-spacing:2px}
.brand-icon{width:28px;height:28px;background:{{T.accent}};border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px}
.header-nav{display:flex;align-items:center;gap:8px;position:relative}
.hbtn{
  padding:6px 14px;font-family:inherit;font-size:11px;
  border-radius:10px;cursor:pointer;transition:all 0.15s;letter-spacing:1px;
}
.hbtn-ghost{background:transparent;border:1px solid {{T.border}};color:{{T.muted}}}
.hbtn-ghost:hover{border-color:{{T.accent}};color:{{T.highlight}}}
.hbtn-fill{background:rgba(136, 206, 2, 0.15);border:2px solid {{T.accent}};color:{{T.highlight}};backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px)}
.hbtn-fill:hover{background:rgba(136, 206, 2, 0.25);box-shadow:0 0 12px {{T.glowAccent}}}
.course-lang-switcher .course-lang-opt{padding:4px 10px;font-size:11px;border:1px solid {{T.border}};border-radius:8px;background:transparent;color:{{T.muted}};cursor:pointer;font-family:inherit;transition:all .15s}
.course-lang-switcher .course-lang-opt:hover,.course-lang-switcher .course-lang-opt.active{border-color:{{T.accent}};color:{{T.highlight}};background:rgba(136,206,2,0.08)}

/* ── Hero ── */
.hero{
  padding:100px 24px 48px;text-align:center;position:relative;z-index:10;
  background:radial-gradient(ellipse at 50% 0%, {{T.glow}} 0%, transparent 50%);
}
.hero-badge{
  display:inline-block;padding:4px 14px;
  background:rgba(17, 13, 32, 0.18);border:1px solid {{T.border}};border-radius:12px;
  font-size:11px;color:{{T.accent}};letter-spacing:2px;margin-bottom:16px;
  backdrop-filter:blur(16px) saturate(1.3);-webkit-backdrop-filter:blur(16px) saturate(1.3);
}
.hero h1{
  font-size:28px;font-weight:700;letter-spacing:3px;color:{{T.highlight}};
  text-shadow:0 0 30px {{T.glow}};margin-bottom:12px;line-height:1.3;
}
.hero-sub{font-size:13px;color:{{T.muted}};max-width:520px;margin:0 auto 24px;line-height:1.7}
.hero-stats{display:flex;gap:24px;justify-content:center;flex-wrap:wrap;margin-bottom:24px}
.stat{text-align:center;padding:12px 16px;background:rgba(17, 13, 32, 0.18);border:1px solid {{T.border}};border-radius:12px;min-width:100px;backdrop-filter:blur(24px) saturate(1.3);-webkit-backdrop-filter:blur(24px) saturate(1.3);box-shadow:0 2px 24px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.04)}
.stat-val{font-size:20px;font-weight:700;color:{{T.accent}}}
.stat-lbl{font-size:10px;color:{{T.muted}};margin-top:2px;letter-spacing:1px}
.hero-actions{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
.hero-btn{
  padding:12px 28px;font-family:inherit;font-size:13px;font-weight:700;
  border-radius:16px;cursor:pointer;letter-spacing:1px;transition:all 0.15s;
}
.hero-btn-primary{
  background:rgba(136, 206, 2, 0.2);color:{{T.highlight}};border:2px solid {{T.accent}};
  box-shadow:0 0 20px {{T.glowAccent}};backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
}
.hero-btn-primary:hover{background:rgba(136, 206, 2, 0.3);transform:translateY(-2px);box-shadow:0 0 30px {{T.glowAccent}}}
.hero-btn-secondary{background:transparent;color:{{T.muted}};border:1px solid {{T.border}}}
.hero-btn-secondary:hover{border-color:{{T.accent}};color:{{T.highlight}}}
/* ── Sections ── */
.section{max-width:800px;margin:0 auto;padding:40px 24px;position:relative;z-index:10}
.section-title{font-size:18px;font-weight:700;color:{{T.highlight}};letter-spacing:2px;margin-bottom:6px}
.section-desc{color:{{T.muted}};font-size:12px;margin-bottom:24px}

/* ── Objectives ── */
.obj-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.obj-card{
  padding:14px;background:rgba(17, 13, 32, 0.18);border:1px solid {{T.border}};border-radius:12px;
  display:flex;align-items:flex-start;gap:10px;transition:all 0.2s;
  backdrop-filter:blur(24px) saturate(1.3);-webkit-backdrop-filter:blur(24px) saturate(1.3);
  box-shadow:0 2px 24px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.04);
}
.obj-card:hover{border-color:{{T.accent}};transform:translateY(-2px)}
.obj-icon{
  width:28px;height:28px;min-width:28px;background:{{T.accent}};border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;
}
.obj-text{font-size:12px;line-height:1.5;color:{{T.muted}}}

/* ── Lesson Cards ── */
.lessons{display:flex;flex-direction:column;gap:12px}
.lesson-cover{
  width:80px;height:60px;min-width:80px;border-radius:8px;
  border:2px solid;image-rendering:pixelated;image-rendering:crisp-edges;
  background:rgba(0,0,0,0.3);
}
.lesson-cover-fallback{
  width:80px;height:60px;min-width:80px;border-radius:8px;
  border:2px solid;display:flex;align-items:center;justify-content:center;
  font-size:24px;background:rgba(0,0,0,0.3);
}
.lesson-card{
  background:rgba(17, 13, 32, 0.18);border:2px solid {{T.border}};border-radius:14px;
  padding:14px 16px;display:flex;align-items:center;gap:12px;
  transition:all 0.2s;position:relative;overflow:hidden;
  backdrop-filter:blur(24px) saturate(1.3);-webkit-backdrop-filter:blur(24px) saturate(1.3);
  box-shadow:0 2px 24px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.04);
}
.lesson-card::before{
  content:'';position:absolute;left:0;top:0;bottom:0;width:3px;
  background:var(--ca);border-radius:3px 0 0 3px;
}
.lesson-card:hover{border-color:var(--ca);transform:translateX(4px);box-shadow:0 0 20px var(--cglow)}
.lesson-card.locked{opacity:0.45;filter:grayscale(0.3)}
.lesson-card.completed::before{background:{{T.success}}}
.lesson-card.completed{border-color:{{T.success}}}
.lesson-num{
  font-size:10px;color:var(--ca);font-weight:700;letter-spacing:2px;
  writing-mode:vertical-lr;transform:rotate(180deg);min-width:14px;text-align:center;
}
.lesson-body{flex:1;min-width:0}
.lesson-title{font-size:14px;font-weight:700;color:{{T.text}};letter-spacing:1px;margin-bottom:2px}
.lesson-sub{font-size:11px;color:{{T.muted}};margin-bottom:6px}
.lesson-tags{display:flex;flex-wrap:wrap;gap:4px}
.tag{font-size:10px;color:{{T.muted}};padding:2px 8px;background:{{T.bg}};border-radius:6px}
.lesson-right{display:flex;flex-direction:column;align-items:flex-end;gap:8px}
.play-btn{
  padding:8px 20px;font-family:inherit;font-size:11px;font-weight:700;
  border:2px solid;border-radius:12px;cursor:pointer;letter-spacing:2px;
  background:transparent;transition:all 0.15s;white-space:nowrap;
}
.play-btn:hover:not(:disabled){background:{{T.buttonBg}};box-shadow:0 0 12px var(--cglow);transform:scale(1.05)}
.play-btn:disabled{cursor:not-allowed;opacity:0.4}
.lesson-progress{width:80px;height:3px;background:{{T.bg}};border-radius:2px;overflow:hidden}
.progress-fill{height:100%;width:0%;border-radius:2px;transition:width 0.5s}

/* ── Footer ── */
.footer{text-align:center;padding:32px 24px;border-top:2px solid {{T.border}};color:{{T.muted}};font-size:11px;letter-spacing:1px;position:relative;z-index:10}
.footer span{color:{{T.accent}}}

@media(max-width:640px){
  .hero h1{font-size:20px}
  .hero-stats{gap:12px}
  .lesson-card{flex-direction:row;align-items:center;gap:10px;flex-wrap:wrap}
  .lesson-cover,.lesson-cover-fallback{width:60px;height:45px;min-width:60px}
  .lesson-num{writing-mode:horizontal-tb;transform:none}
  .lesson-right{align-items:flex-start;width:100%}
  .lesson-progress{width:100%}
  .header{padding:0 12px}
  .section{padding:32px 12px}
}
</style>
</head>
<body>

<canvas id="grain-noise" style="position:fixed;inset:0;width:100%;height:100%;z-index:2;pointer-events:none;mix-blend-mode:soft-light;opacity:0.55" aria-hidden="true"></canvas>

<header class="header">
  <div class="header-inner">
    <a class="brand" href="/courses/" style="text-decoration:none;color:inherit">🎮 EdGameClaw</a>
    <div class="header-nav">
      <div class="course-lang-switcher" style="display:flex;gap:4px;margin-right:8px;flex-wrap:wrap">{{LANG_SWITCHER_HTML}}</div>
      <a href="/courses/" class="hbtn hbtn-ghost" style="text-decoration:none;font-size:13px" data-i18n="allCourses">{{U.allCourses}}</a>
    </div>
  </div>
</header>

<!-- Hero -->
<section class="hero">
  <div class="hero-badge">{{U.badge}}</div>
  <h1>{{COURSE_TITLE}}</h1>
  <p class="hero-sub">{{COURSE_DESCRIPTION}}</p>
  <div class="hero-stats">
    <div class="stat"><div class="stat-val">{{TOTAL_LESSONS}}</div><div class="stat-lbl">{{U.statGames}}</div></div>
    <div class="stat"><div class="stat-val">{{COURSE_TIME}}</div><div class="stat-lbl">{{U.statTime}}</div></div>
    <div class="stat"><div class="stat-val">{{COURSE_LEVEL}}</div><div class="stat-lbl">{{U.statLevel}}</div></div>
    <div class="stat"><div class="stat-val" id="completion-pct">0%</div><div class="stat-lbl">{{U.statDone}}</div></div>
  </div>
  <div class="hero-actions">
    <button class="hero-btn hero-btn-primary" onclick="startLearning()">{{U.startLearning}}</button>
    <button class="hero-btn hero-btn-secondary" onclick="authUI.showPricing()">{{U.subscribe}}</button>
  </div>
</section>

<!-- Objectives -->
<section class="section">
  <div class="section-title" data-i18n="objectivesTitle">{{U.objectivesTitle}}</div>
  <div class="section-desc" data-i18n="objectivesDesc">{{U.objectivesDesc}}</div>
  <div class="obj-grid" id="obj-grid"></div>
</section>

<!-- Lessons -->
<section class="section">
  <div class="section-title" data-i18n="lessonsTitle">{{U.lessonsTitle}}</div>
  <div class="section-desc" data-i18n="lessonsDesc">{{U.lessonsDesc}}</div>
  <div class="lessons" id="lessons-grid">
    {{GAMES_CARDS_HTML}}
  </div>
</section>

<footer class="footer">
  <p data-i18n="footerBuilt">{{U.footerBuilt}}</p>
  <p style="margin-top:6px">{{COURSE_SUBJECT}} · {{COURSE_LEVEL}} · {{TOTAL_LESSONS}} <span data-i18n="footerLessons">{{U.footerLessons}}</span></p>
</footer>

<!-- Course access gate overlay (shown when user has no access and no share token) -->
<div id="af-course-gate" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(10,8,16,0.92);backdrop-filter:blur(20px);z-index:200;align-items:center;justify-content:center;flex-direction:column;padding:24px;text-align:center">
  <div style="max-width:400px;background:rgba(40,15,35,0.95);border:2px solid #5a3050;border-radius:20px;padding:36px 32px;box-shadow:0 0 40px rgba(255,120,180,0.15)">
    <div style="font-size:36px;margin-bottom:12px">🔒</div>
    <h2 id="af-gate-title" style="color:#ffc0d0;font-size:20px;letter-spacing:2px;margin-bottom:10px;font-family:'PixelZH','Courier New',monospace"></h2>
    <p id="af-gate-msg" style="color:#c080a0;font-size:13px;line-height:1.6;margin-bottom:24px;font-family:'PixelZH','Courier New',monospace"></p>
    <button id="af-gate-btn" style="padding:12px 32px;background:rgba(136,206,2,0.2);color:#ffc0d0;border:2px solid #ff6a9a;border-radius:16px;font-family:'PixelZH','Courier New',monospace;font-size:13px;cursor:pointer;width:100%;transition:all 0.15s"></button>
    <a href="/courses/" style="display:block;margin-top:14px;color:#8050a0;font-size:11px;font-family:'PixelZH','Courier New',monospace;text-decoration:none;letter-spacing:1px">← 返回课程列表</a>
  </div>
</div>

{{COVER_SCRIPT_TAGS}}
<script>
const MANIFEST = {{MANIFEST_JSON}};
const OBJECTIVES = MANIFEST.course.learning_objectives || [];
const COURSE_ID = MANIFEST.course.id || '';
const COURSE_PAGE_STRINGS = {{COURSE_PAGE_STRINGS_JSON}};
const LOCALE_NAMES = {{LOCALE_NAMES_JSON}};
let courseProgress = JSON.parse(localStorage.getItem('edgame_progress') || '{}');
let currentCourseLang = (function(){ var p = new URLSearchParams(location.search); var l = p.get('lang') || localStorage.getItem('edgame_lang'); return (l && COURSE_PAGE_STRINGS[l]) ? l : 'zh'; })();

function applyCourseLocale(lang) {
  if (!COURSE_PAGE_STRINGS[lang]) return;
  currentCourseLang = lang;
  try { localStorage.setItem('edgame_lang', lang); } catch(e) {}
  document.documentElement.lang = (lang === 'zh' ? 'zh-CN' : lang);
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var key = el.getAttribute('data-i18n');
    if (COURSE_PAGE_STRINGS[lang][key] != null) el.textContent = COURSE_PAGE_STRINGS[lang][key];
  });
  document.querySelectorAll('.course-lang-opt').forEach(function(b) {
    b.classList.toggle('active', b.getAttribute('data-lang') === lang);
  });
}
document.querySelectorAll('.course-lang-opt').forEach(function(btn) {
  btn.addEventListener('click', function() { applyCourseLocale(btn.getAttribute('data-lang')); });
});
applyCourseLocale(currentCourseLang);

// Handle share token from URL before auth is ready
(function() {
  var sp = new URLSearchParams(location.search);
  var st = sp.get('share');
  if (st && COURSE_ID) sessionStorage.setItem('edgame_share_' + COURSE_ID, st);
})();

function init() {
  renderObjectives();
  updateProgress();
  authUI.renderUserMenu(document.getElementById('af-user-menu-container'));
  auth.onAuthChange(function(user) {
    var btns = document.getElementById('af-auth-buttons');
    if (btns) btns.style.display = user ? 'none' : 'flex';
    var dashLink = document.getElementById('af-dashboard-link');
    if (dashLink) dashLink.style.display = user ? '' : 'none';
    if (user) localStorage.setItem('edgame_user_name', auth.getDisplayName());
  });
  window.addEventListener('storage', e => {
    if (e.key === 'edgame_progress') { courseProgress = JSON.parse(e.newValue || '{}'); updateProgress(); }
  });
  window.addEventListener('focus', () => {
    courseProgress = JSON.parse(localStorage.getItem('edgame_progress') || '{}');
    updateProgress();
  });
  if (COURSE_ID) _checkCourseAccess();
}

// Page-level access gate: blocks the course page for non-owners without a share token
async function _checkCourseAccess() {
  await auth.ready();
  var result = await auth.canPlayGame(COURSE_ID, 'chunk-1');
  if (result.allowed) return;
  var gate = document.getElementById('af-course-gate');
  var gateTitle = document.getElementById('af-gate-title');
  var gateMsg = document.getElementById('af-gate-msg');
  var gateBtn = document.getElementById('af-gate-btn');
  if (!gate) return;
  gate.style.display = 'flex';
  // Re-hide gate if user successfully logs in / purchases
  auth.onAuthChange(async function(user) {
    if (!user) return;
    var r2 = await auth.canPlayGame(COURSE_ID, 'chunk-1');
    if (r2.allowed) gate.style.display = 'none';
  });
  if (result.reason === 'credit_required') {
    if (gateTitle) gateTitle.textContent = '解锁此课程';
    if (gateMsg) gateMsg.textContent = '这是创作者发布的课程，消耗积分即可解锁全部内容。';
    if (gateBtn) {
      gateBtn.textContent = '消耗 ' + (result.creditRequired || 0) + ' 积分解锁';
      gateBtn.onclick = async function() {
        var r = await auth.payCreditsForCourse(COURSE_ID);
        if (r.success) { location.reload(); }
        else { authUI.showToast(r.error || '支付失败'); }
      };
    }
  } else {
    if (gateTitle) gateTitle.textContent = '登录后访问';
    if (gateMsg) gateMsg.textContent = '请登录或注册后访问此课程，或通过分享链接预览第一个游戏。';
    if (gateBtn) {
      gateBtn.textContent = '登录 / 注册';
      // Do NOT hide gate here — keep it behind the modal so closing modal without login re-exposes the gate
      gateBtn.onclick = function() { authUI.showAuth('login'); };
    }
  }
}

function renderObjectives() {
  document.getElementById('obj-grid').innerHTML = OBJECTIVES.map((o, i) =>
    `<div class="obj-card"><div class="obj-icon">${i+1}</div><div class="obj-text">${o}</div></div>`
  ).join('');
}

async function launchGame(btn, idx) {
  var g = MANIFEST.games[idx]; if (!g || g.status !== 'success') return;
  var chunkId = g.chunk_id || ('chunk-' + idx);
  var result = await auth.canPlayGame(COURSE_ID, chunkId);
  if (!result.allowed) {
    if (result.reason === 'credit_required') {
      authUI.showPaywall('credit_required', COURSE_ID, chunkId, result);
    } else {
      authUI.showPaywall('login_required');
    }
    return;
  }
  await auth.recordGamePlay(COURSE_ID, chunkId);
  var user = auth.getUser();
  if (user) localStorage.setItem('edgame_user_name', auth.getDisplayName());
  var href = btn.dataset.href;
  if (href && currentCourseLang && currentCourseLang !== 'zh') {
    href += (href.indexOf('?') >= 0 ? '&' : '?') + 'lang=' + encodeURIComponent(currentCourseLang);
  }
  if (href) window.location.href = href;
}

function startLearning() {
  var b = document.querySelector('.lesson-card.available .play-btn'); if (b) b.click();
}

function updateProgress() {
  var games = MANIFEST.games, done = 0;
  games.forEach(function(g, i) {
    var p = courseProgress[g.chunk_id];
    var bar = document.querySelector('#progress-' + i + ' .progress-fill');
    var card = document.querySelector('.lesson-card[data-lesson="' + i + '"]');
    if (p && p.completed) { done++; if (bar) bar.style.width = '100%'; if (card) card.classList.add('completed'); }
    else if (p && p.progress) { if (bar) bar.style.width = (p.progress * 100) + '%'; }
  });
  var pct = games.length > 0 ? Math.round((done / games.length) * 100) : 0;
  document.getElementById('completion-pct').textContent = pct + '%';
}

function renderCover(chunkId) {
  var fn = window._EDGAME_COVERS && window._EDGAME_COVERS[chunkId];
  var canvas = document.getElementById('cover-' + chunkId);
  if (fn && canvas) {
    try { fn(canvas.getContext('2d'), canvas.width, canvas.height); } catch(e) {}
  }
}

function gpx(g, x, y, c) { g.fillStyle = c; g.fillRect(x, y, 1, 1); }
function grect(g, x, y, w, h, c) { g.fillStyle = c; g.fillRect(x, y, w, h); }

init();
{{COVER_RENDER_CALLS}}

(function(){var c=document.getElementById('grain-noise');if(!c)return;var gl=c.getContext('webgl',{alpha:true});if(!gl)return;var dpr=Math.min(window.devicePixelRatio||1,2);c.width=window.innerWidth*dpr;c.height=window.innerHeight*dpr;gl.viewport(0,0,c.width,c.height);var vs=gl.createShader(gl.VERTEX_SHADER);gl.shaderSource(vs,'attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}');gl.compileShader(vs);var fs=gl.createShader(gl.FRAGMENT_SHADER);gl.shaderSource(fs,'precision lowp float;uniform vec2 u_res;float rand(vec2 co){return fract(sin(dot(co,vec2(12.9898,78.233)))*43758.5453);}void main(){vec2 st=gl_FragCoord.xy/u_res;float n=rand(st*u_res);gl_FragColor=vec4(vec3(n),0.38);}');gl.compileShader(fs);var prog=gl.createProgram();gl.attachShader(prog,vs);gl.attachShader(prog,fs);gl.linkProgram(prog);gl.useProgram(prog);var buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);var pos=gl.getAttribLocation(prog,'p');gl.enableVertexAttribArray(pos);gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);var uRes=gl.getUniformLocation(prog,'u_res');gl.uniform2f(uRes,c.width,c.height);gl.drawArrays(gl.TRIANGLES,0,6);window.addEventListener('resize',function(){c.width=window.innerWidth*dpr;c.height=window.innerHeight*dpr;gl.viewport(0,0,c.width,c.height);gl.uniform2f(uRes,c.width,c.height);gl.drawArrays(gl.TRIANGLES,0,6)});})();
</script>
</body>
</html>"""
