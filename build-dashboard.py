#!/usr/bin/env python3
"""
취업준비 대시보드 빌더

이 폴더를 스캔해서 dashboard.html 을 다시 씁니다.

    python3 build-dashboard.py

옵션
    --base PATH    링크에 쓸 절대경로 기준. 다른 머신에서 돌릴 때만 필요.
    --vault NAME   Obsidian 보관함 이름. 기본값은 이 폴더 이름.
    --page-size N  경험 원자 카드 한 페이지 개수 (기본 9)
    --links SCHEME obsidian(기본) | vscode | file

읽는 것
    me/experiences/*.md        경험 원자 (프론트매터 title/description/tags)
    applications/*/meta.md     지원 건 상태 (company/role/track/stage/stage_note/deadline/next_action)
    applications/*/**.md       경험 원자 참조 횟수 집계용

표준 라이브러리만 씁니다. 설치할 것 없음.
"""

import html
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

BUNDLE = Path(__file__).resolve().parent
OUT = BUNDLE / "dashboard.html"


def _arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


# 링크에 쓸 절대경로 기준. 보통은 이 스크립트가 있는 폴더 그대로.
LINK_BASE = Path(_arg("--base", str(BUNDLE)))
LINK_SCHEME = _arg("--links", "obsidian")
# macOS는 한글 파일명을 NFD(자모 분해)로 저장한다. NFC로 만든 경로는
# Obsidian이 보관함을 찾지 못하므로("Unable to find a vault") macOS에서만 NFD로 맞춘다.
# Windows·Linux는 NFC 그대로 둔다.
_FS_FORM = "NFD" if sys.platform == "darwin" else "NFC"


def fs_norm(s):
    """링크에 쓸 문자열을 이 OS의 파일명 정규화 형태로 맞춘다."""
    return unicodedata.normalize(_FS_FORM, s)


VAULT = fs_norm(_arg("--vault", LINK_BASE.name))

STAGES = ["관심", "서류작성", "지원완료", "필기·과제", "면접", "결과대기"]
TERMINAL = {"합격": "good", "불합격": "critical"}
# 예전 이름 → 현재 이름. 기존 meta.md를 고치지 않아도 되게 한다.
STAGE_ALIASES = {"코테·과제": "필기·과제", "코테": "필기·과제", "과제": "필기·과제"}
UNKNOWN_STAGES = []   # STAGES/TERMINAL에 없는 값을 쓴 지원 건. 빌드 끝에 경고로 출력.
PAGE_SIZE = int(_arg("--page-size", "9"))   # 경험 원자 카드 한 페이지 개수
TAG_VISIBLE = 12
NAV = [("summary", "요약"), ("apps", "지원 현황"),
       ("exps", "경험 원자"), ("links", "바로가기")]
DUE_PRESETS = [("all", "전체"), ("7", "7일 내"), ("30", "30일 내"), ("past", "마감 지남")]


# ── 프론트매터 파싱 (YAML 최소 부분집합) ────────────────────────────────

def parse_frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}, ""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block, body = text[3:end], text[end + 4:]
    meta = {}
    last_key = None
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # 들여쓴 "- 항목" 줄: 바로 위 키의 여러 줄 목록 (Obsidian 속성 편집기가 이 형식으로 저장한다)
        #   tags:
        #     - 백엔드
        #     - 협업
        if line.startswith(" ") or line.startswith("\t"):
            item = line.strip()
            if last_key and item.startswith("- ") and isinstance(meta.get(last_key), list):
                meta[last_key].append(item[2:].strip().strip("'\""))
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            meta[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        elif val == "":
            meta[key] = []          # 값이 비어 있으면 다음 줄부터 "- 항목" 목록일 수 있다
        else:
            meta[key] = val.strip("'\"")
        last_key = key
    # 목록이 아니었던 빈 값은 빈 문자열로 되돌린다
    for k, v in meta.items():
        if v == [] and k not in ("tags",):
            meta[k] = ""
    return meta, body


def norm(s):
    """문서 안 링크(NFC)와 macOS 파일명(NFD)을 같은 형태로 맞춘다."""
    return unicodedata.normalize("NFC", s)


# ── 수집 ────────────────────────────────────────────────────────────────

def collect_experiences():
    d = BUNDLE / "me" / "experiences"
    if not d.is_dir():
        return []
    items = []
    for p in sorted(d.glob("*.md")):
        if p.name in ("index.md", "log.md", "_template.md"):
            continue
        meta, _ = parse_frontmatter(p)
        tags = meta.get("tags", [])
        items.append({
            "path": p,
            "stem": norm(p.stem),
            "title": meta.get("title") or norm(p.stem),
            "description": meta.get("description", ""),
            "tags": [norm(t) for t in tags] if isinstance(tags, list) else [],
            "sample": p.name.startswith("_sample"),
            "mtime": p.stat().st_mtime,
            "uses": 0,
        })
    return items


def collect_applications():
    d = BUNDLE / "applications"
    if not d.is_dir():
        return []
    apps = []
    for folder in sorted(x for x in d.iterdir() if x.is_dir() and x.name != "_template"):
        meta, _ = parse_frontmatter(folder / "meta.md")
        if not meta:
            continue
        stage = meta.get("stage") or "관심"
        stage = STAGE_ALIASES.get(stage, stage)
        if stage not in STAGES and stage not in TERMINAL:
            UNKNOWN_STAGES.append((folder.name, stage))
        apps.append({
            "folder": folder,
            "company": meta.get("company") or norm(folder.name),
            "role": meta.get("role", ""),
            "track": meta.get("track", ""),
            "stage": stage,
            "stage_note": meta.get("stage_note", ""),
            "deadline": meta.get("deadline", ""),
            "next_action": meta.get("next_action", ""),
            "sample": folder.name.startswith("_sample"),
        })
    return apps


def count_usage(experiences, apps):
    for app in apps:
        blob = ""
        for p in app["folder"].rglob("*.md"):
            try:
                blob += norm(p.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                pass
        for exp in experiences:
            if exp["stem"] and exp["stem"] in blob:
                exp["uses"] += 1
    experiences.sort(key=lambda e: (-e["uses"], -e["mtime"]))


# ── 링크 ────────────────────────────────────────────────────────────────

def link_path(path):
    try:
        return LINK_BASE / path.resolve().relative_to(BUNDLE)
    except ValueError:
        return path.resolve()


def doc_link(path):
    """대시보드를 여는 머신 기준의 편집기 링크."""
    target = link_path(path)
    # URL용 절대경로: 항상 슬래시 구분자, 항상 "/"로 시작 (Windows는 "/C:/..." 형태)
    abs_posix = target.as_posix()
    if not abs_posix.startswith("/"):
        abs_posix = "/" + abs_posix
    if LINK_SCHEME == "vscode":
        return "vscode://file" + quote(fs_norm(abs_posix), safe="/:")
    if LINK_SCHEME == "file":
        return "file://" + quote(fs_norm(abs_posix), safe="/:")
    # obsidian: 절대경로 매칭 대신 vault + 보관함 상대경로를 쓴다.
    try:
        rel = path.resolve().relative_to(BUNDLE).as_posix()
    except ValueError:
        rel = path.name
    return ("obsidian://open?vault=" + quote(VAULT, safe="")
            + "&file=" + quote(fs_norm(rel), safe=""))


def days_left(deadline):
    try:
        return (datetime.strptime(deadline, "%Y-%m-%d").date() - date.today()).days
    except (ValueError, TypeError):
        return None


def e(s):
    return html.escape(str(s or ""))


# ── HTML ────────────────────────────────────────────────────────────────

CSS = """
:root {
  color-scheme: light;
  --plane:#f9f9f7; --surface:#fcfcfb;
  --ink:#0b0b0b; --ink-2:#52514e; --ink-muted:#898781;
  --line:rgba(11,11,11,0.10); --rule:#e1e0d9;
  --good:#0ca30c; --warning:#fab219; --critical:#d03b3b;
  --s1:#86b6ef; --s2:#5598e7; --s3:#3987e5; --s4:#2a78d6; --s5:#256abf; --s6:#1c5cab;
  --accent:#2a78d6; --accent-soft:#e8f1fd;
  --nav-h:50px;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --plane:#0d0d0d; --surface:#1a1a19;
    --ink:#ffffff; --ink-2:#c3c2b7; --ink-muted:#898781;
    --line:rgba(255,255,255,0.10); --rule:#2c2c2a;
    --s1:#cde2fb; --s2:#b7d3f6; --s3:#9ec5f4; --s4:#86b6ef; --s5:#5598e7; --s6:#3987e5;
    --accent:#3987e5; --accent-soft:rgba(57,135,229,0.18);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --plane:#0d0d0d; --surface:#1a1a19;
  --ink:#ffffff; --ink-2:#c3c2b7; --ink-muted:#898781;
  --line:rgba(255,255,255,0.10); --rule:#2c2c2a;
  --s1:#cde2fb; --s2:#b7d3f6; --s3:#9ec5f4; --s4:#86b6ef; --s5:#5598e7; --s6:#3987e5;
  --accent:#3987e5; --accent-soft:rgba(57,135,229,0.18);
}
* { box-sizing:border-box; }
/* 작성자 스타일의 display 가 UA의 [hidden] 을 이기므로 명시적으로 눌러준다.
   이게 없으면 .exp{display:flex} 카드가 필터링돼도 그대로 보인다. */
[hidden] { display:none !important; }
html { scroll-behavior:smooth; }
@media (prefers-reduced-motion:reduce) { html { scroll-behavior:auto; } }
body {
  margin:0; background:var(--plane); color:var(--ink);
  font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap { max-width:1080px; margin:0 auto; padding:0 24px; }
a { color:inherit; }
h1 { font-size:22px; font-weight:700; margin:0; letter-spacing:-0.015em; }
.sub { color:var(--ink-2); font-size:13px; margin:7px 0 0; }
.card { background:var(--surface); border:1px solid var(--line); border-radius:12px; }
code { font-family:var(--mono); font-size:0.88em; }
:focus-visible { outline:2px solid var(--accent); outline-offset:3px; border-radius:3px; }

/* 머리말 */
.masthead { background:var(--surface); border-bottom:1px solid var(--rule); }
.masthead .wrap { padding-top:30px; padding-bottom:22px; }

/* GNB */
.gnb { position:sticky; top:0; z-index:50; background:var(--surface);
       border-bottom:1px solid var(--rule); }
.gnb .wrap { display:flex; align-items:center; gap:10px; }
.navlinks { display:flex; gap:2px; flex:1; min-width:0; overflow-x:auto; scrollbar-width:none; }
.navlinks::-webkit-scrollbar { display:none; }
.gnb a { flex:none; height:var(--nav-h); display:flex; align-items:center; gap:8px;
         padding:0 14px; text-decoration:none; color:var(--ink-2); font-size:13.5px;
         font-weight:500; white-space:nowrap; border-bottom:2px solid transparent;
         margin-bottom:-1px; }
.gnb a:hover { color:var(--ink); }
.gnb a.on { color:var(--accent); border-bottom-color:var(--accent); font-weight:600; }
.idx { font-family:var(--mono); font-size:10.5px; font-weight:600; letter-spacing:0.06em;
       color:var(--ink-muted); background:var(--plane); border:1px solid var(--line);
       border-radius:3px; padding:1px 5px; }
.gnb a.on .idx { color:var(--accent); border-color:var(--accent); }
.themebtn { flex:none; background:var(--plane); border:1px solid var(--line);
            border-radius:7px; color:var(--ink-2); padding:5px 10px; font:inherit;
            font-size:12px; cursor:pointer; }
.themebtn:hover { color:var(--ink); }

/* 섹션 */
main .wrap { padding-bottom:56px; }
section { padding:40px 0; scroll-margin-top:var(--nav-h); }
section + section { border-top:1px solid var(--rule); }
.sec-head { margin-bottom:22px; }
.sec-tag { font-family:var(--mono); font-size:10.5px; font-weight:600; letter-spacing:0.12em;
           text-transform:uppercase; color:var(--accent); }
.sec-head h2 { font-size:21px; font-weight:700; letter-spacing:-0.018em; margin:7px 0 0; }
.sec-head p { color:var(--ink-2); font-size:13.5px; margin:7px 0 0; max-width:64ch; }

/* 스탯 타일 */
.tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
.tile { padding:16px 18px; }
.tile .label { font-size:12px; color:var(--ink-2); }
.tile .value { font-size:30px; font-weight:600; line-height:1.15; margin-top:6px;
               letter-spacing:-0.02em; }
.tile .note { font-size:12px; color:var(--ink-muted); margin-top:2px; }

/* 필터 (표·카드 위 한 줄) */
.filters { display:flex; flex-wrap:wrap; align-items:center; gap:8px 14px; margin-bottom:14px; }
.fgroup { display:flex; flex-wrap:wrap; gap:4px; align-items:center; }
.flabel { font-family:var(--mono); font-size:10px; font-weight:600; letter-spacing:0.09em;
          text-transform:uppercase; color:var(--ink-muted); margin-right:3px; }
.fbtn { background:var(--surface); border:1px solid var(--line); border-radius:999px;
        padding:4px 11px; font:inherit; font-size:12.5px; color:var(--ink-2);
        cursor:pointer; white-space:nowrap; }
.fbtn:hover { color:var(--ink); }
.fbtn[aria-pressed="true"] { background:var(--accent-soft); border-color:var(--accent);
                             color:var(--accent); font-weight:600; }
.fbtn.ghost { color:var(--ink-muted); border-style:dashed; }
.fbtn .n { font-variant-numeric:tabular-nums; opacity:0.7; margin-left:5px; font-size:11px; }
.fsearch { background:var(--surface); border:1px solid var(--line); border-radius:8px;
           padding:5px 10px; font:inherit; font-size:12.5px; color:var(--ink); min-width:150px; }
.fsearch::placeholder { color:var(--ink-muted); }
.fcount { font-size:12px; color:var(--ink-muted); font-variant-numeric:tabular-nums;
          margin-left:auto; }
.fnone { padding:20px 18px; color:var(--ink-muted); font-size:13px; }

/* 표 */
.tablecard { overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:560px; }
thead th { font-size:11px; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;
           color:var(--ink-muted); text-align:left; padding:14px 14px 9px; }
tbody tr { border-top:1px solid var(--rule); }
tbody td { padding:13px 14px; vertical-align:top; }
tbody td.num { font-variant-numeric:tabular-nums; white-space:nowrap; }
.co { font-weight:600; }
.role { color:var(--ink-2); font-size:13px; }

/* 칩 */
.chip { display:inline-flex; align-items:center; gap:5px; font-size:12px; white-space:nowrap; }
.dot { width:8px; height:8px; border-radius:50%; flex:none; }
.tag { display:inline-block; font-size:11px; color:var(--ink-2); border:1px solid var(--line);
       border-radius:999px; padding:1px 8px; margin:0 4px 4px 0; }
.chip.unk { border:1px dashed var(--critical); color:var(--critical); }
.note { display:block; font-size:11px; color:var(--ink-muted); margin-top:3px; }
.track { font-size:11px; color:var(--ink-2); border:1px solid var(--line);
         border-radius:4px; padding:1px 6px; }
.warn { color:#8a5a00; } .crit { color:var(--critical); } .ok { color:var(--good); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .warn { color:var(--warning); } }
:root[data-theme="dark"] .warn { color:var(--warning); }

/* 경험 원자 카드 */
.exps { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:12px; }
.exp { padding:16px 18px; display:flex; flex-direction:column; gap:8px; }
.exp .top { display:flex; align-items:baseline; justify-content:space-between; gap:10px; }
.exp .name { font-weight:600; font-size:15px; text-decoration:none; letter-spacing:-0.01em; }
.exp .name:hover { color:var(--accent); }
.exp .desc { color:var(--ink-2); font-size:13px; margin:0; }
.uses { font-size:11px; color:var(--ink-muted); font-variant-numeric:tabular-nums;
        white-space:nowrap; }
/* 페이지네이션 */
.pager { display:flex; gap:4px; align-items:center; flex-wrap:wrap; margin-top:14px; }
.pbtn { background:var(--surface); border:1px solid var(--line); border-radius:7px;
        min-width:32px; height:30px; padding:0 9px; font:inherit; font-size:12.5px;
        color:var(--ink-2); cursor:pointer; font-variant-numeric:tabular-nums; }
.pbtn:hover:not(:disabled) { color:var(--ink); }
.pbtn[aria-current="true"] { background:var(--accent-soft); border-color:var(--accent);
                             color:var(--accent); font-weight:600; }
.pbtn:disabled { opacity:0.4; cursor:default; }
.pinfo { font-size:12px; color:var(--ink-muted); margin-left:8px;
         font-variant-numeric:tabular-nums; }

/* 바로가기 */
.links { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }
.links div { padding:14px 18px; }
.links h3 { font-size:12px; margin:0 0 8px; color:var(--ink-muted); font-weight:600;
            letter-spacing:0.03em; text-transform:uppercase; }
.links ul { margin:0; padding:0; list-style:none; }
.links li { margin:5px 0; }
.links a { text-decoration:none; font-size:13px; }
.links a:hover { color:var(--accent); }

.empty { padding:22px 18px; color:var(--ink-muted); font-size:13px; }
.sample { font-size:10px; border:1px solid var(--line); border-radius:3px; padding:0 4px;
          color:var(--ink-muted); margin-left:6px; vertical-align:1px; }
footer { border-top:1px solid var(--rule); background:var(--surface);
         color:var(--ink-muted); font-size:12px; }
footer .wrap { padding-top:18px; padding-bottom:40px; }
footer code { background:var(--plane); border:1px solid var(--line); border-radius:4px;
              padding:1px 5px; font-size:11px; }

@media (max-width:640px) {
  .gnb a { padding:0 11px; font-size:12.5px; }
  section { padding:30px 0; }
  .sec-head h2 { font-size:18px; }
  .fcount { margin-left:0; }
}
@media print {
  .gnb, .themebtn, .filters { display:none; }
  section { padding:18px 0; break-inside:auto; }
  .card { break-inside:avoid; }
}
"""

JS = """
// GNB 스크롤 연동
(function () {
  var links = [].slice.call(document.querySelectorAll('.gnb a'));
  var secs = links.map(function (a) { return document.querySelector(a.getAttribute('href')); });
  function sync() {
    var navH = parseInt(getComputedStyle(document.documentElement)
      .getPropertyValue('--nav-h')) || 50;
    var line = window.scrollY + navH + 24, idx = 0;
    for (var i = 0; i < secs.length; i++) {
      if (secs[i] && secs[i].offsetTop <= line) idx = i;
    }
    if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) {
      idx = links.length - 1;
    }
    links.forEach(function (a, i) { a.classList.toggle('on', i === idx); });
    var on = links[idx];
    if (on && on.parentNode.scrollWidth > on.parentNode.clientWidth) {
      var pl = on.parentNode, l = on.offsetLeft, r = l + on.offsetWidth;
      if (l < pl.scrollLeft) pl.scrollLeft = l - 12;
      else if (r > pl.scrollLeft + pl.clientWidth) pl.scrollLeft = r - pl.clientWidth + 12;
    }
  }
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { sync(); ticking = false; });
  }, { passive: true });
  window.addEventListener('resize', sync, { passive: true });
  sync();
})();

// 테마 토글
(function () {
  var root = document.documentElement, btn = document.getElementById('theme');
  function get() { try { return localStorage.getItem('jp-theme'); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem('jp-theme', v); } catch (e) {} }
  var saved = get();
  if (saved) root.setAttribute('data-theme', saved);
  btn.addEventListener('click', function () {
    var dark = root.getAttribute('data-theme') === 'dark' ||
      (!root.getAttribute('data-theme') &&
        window.matchMedia('(prefers-color-scheme: dark)').matches);
    var next = dark ? 'light' : 'dark';
    root.setAttribute('data-theme', next); set(next);
  });
})();

// 지원 현황 필터 — 단계(다중 OR) · 마감 프리셋 · 회사명 검색
(function () {
  var bar = document.getElementById('app-filters');
  if (!bar) return;
  var rows = [].slice.call(document.querySelectorAll('#apps tbody tr[data-company]'));
  var stageBtns = [].slice.call(bar.querySelectorAll('[data-stage]'));
  var dueBtns = [].slice.call(bar.querySelectorAll('[data-due]'));
  var search = bar.querySelector('.fsearch');
  var none = document.getElementById('apps-none');
  var count = document.getElementById('apps-count');
  var stages = [], due = 'all';

  function apply() {
    var term = (search.value || '').trim().toLowerCase(), shown = 0;
    rows.forEach(function (tr) {
      var okStage = !stages.length || stages.indexOf(tr.dataset.stage) >= 0;
      var raw = tr.dataset.days, d = raw === '' ? null : parseInt(raw, 10);
      var okDue = due === 'all'
        || (due === 'past' ? (d !== null && d < 0)
                           : (d !== null && d >= 0 && d <= parseInt(due, 10)));
      var okQ = !term || tr.dataset.company.indexOf(term) >= 0;
      var on = okStage && okDue && okQ;
      tr.hidden = !on;
      if (on) shown++;
    });
    none.hidden = shown > 0;
    count.textContent = shown + ' / ' + rows.length + '건';
  }
  stageBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      var v = b.dataset.stage, i = stages.indexOf(v);
      if (i >= 0) stages.splice(i, 1); else stages.push(v);
      b.setAttribute('aria-pressed', i < 0);
      apply();
    });
  });
  dueBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      due = b.dataset.due;
      dueBtns.forEach(function (o) {
        o.setAttribute('aria-pressed', o === b);
      });
      apply();
    });
  });
  search.addEventListener('input', apply);
  apply();
})();

// 경험 원자 — 태그 필터(OR) + 페이지네이션
(function () {
  var grid = document.getElementById('exp-grid');
  if (!grid) return;
  var PAGE = __PAGE_SIZE__;
  var bar = document.getElementById('exp-filters');
  var cards = [].slice.call(grid.querySelectorAll('[data-tags]'));
  var btns = bar ? [].slice.call(bar.querySelectorAll('[data-tag]')) : [];
  var none = document.getElementById('exps-none');
  var count = document.getElementById('exps-count');
  var reset = document.getElementById('exp-reset');
  var pager = document.getElementById('exp-pager');
  var picked = [], page = 1;

  function match(el) {
    if (!picked.length) return true;
    var tags = el.dataset.tags;
    return picked.some(function (t) { return tags.indexOf('|' + t + '|') >= 0; });
  }
  function pbtn(label, target, opt) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'pbtn';
    b.textContent = label;
    if (opt && opt.disabled) b.disabled = true;
    if (opt && opt.current) b.setAttribute('aria-current', 'true');
    b.addEventListener('click', function () {
      page = target;
      apply();
      document.getElementById('exps').scrollIntoView({ block: 'start' });
    });
    return b;
  }
  function apply() {
    var list = cards.filter(match);
    var pages = Math.max(1, Math.ceil(list.length / PAGE));
    if (page > pages) page = pages;
    if (page < 1) page = 1;
    cards.forEach(function (el) { el.hidden = true; });
    list.slice((page - 1) * PAGE, page * PAGE).forEach(function (el) { el.hidden = false; });
    if (count) count.textContent = list.length + ' / ' + cards.length + '개';
    if (none) none.hidden = list.length > 0;
    if (reset) reset.hidden = !picked.length;
    pager.textContent = '';
    if (pages > 1) {
      pager.appendChild(pbtn('이전', page - 1, { disabled: page === 1 }));
      for (var i = 1; i <= pages; i++) {
        pager.appendChild(pbtn(String(i), i, { current: i === page }));
      }
      pager.appendChild(pbtn('다음', page + 1, { disabled: page === pages }));
      var info = document.createElement('span');
      info.className = 'pinfo';
      info.textContent = list.length + '개 중 ' + ((page - 1) * PAGE + 1) + '–'
        + Math.min(page * PAGE, list.length) + '번째';
      pager.appendChild(info);
    }
    pager.hidden = pages <= 1;
  }
  btns.forEach(function (b) {
    b.addEventListener('click', function () {
      var v = b.dataset.tag, i = picked.indexOf(v);
      if (i >= 0) picked.splice(i, 1); else picked.push(v);
      b.setAttribute('aria-pressed', i < 0);
      page = 1;
      apply();
    });
  });
  var more = document.getElementById('tag-more');
  if (more) {
    more.addEventListener('click', function () {
      var hiddenTags = bar.querySelectorAll('.fbtn.more[hidden]');
      if (hiddenTags.length) {
        [].forEach.call(hiddenTags, function (b) { b.hidden = false; });
        more.textContent = '접기';
      } else {
        var all = bar.querySelectorAll('.fbtn.more');
        [].forEach.call(all, function (b) {
          if (b.getAttribute('aria-pressed') !== 'true') b.hidden = true;
        });
        more.textContent = '+' + all.length + '개 더';
      }
    });
  }
  if (reset) {
    reset.addEventListener('click', function () {
      picked = [];
      btns.forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      page = 1;
      apply();
    });
  }
  apply();
})();
"""


def stage_chip(stage):
    if stage in TERMINAL:
        icon, cls = ("✓", "ok") if TERMINAL[stage] == "good" else ("✕", "crit")
        return f'<span class="chip {cls}">{icon} {e(stage)}</span>'
    if stage not in STAGES:
        # 모르는 단계값: 숨기지 말고 그대로, 점선 테두리로 표시한다
        return f'<span class="chip unk" title="meta.md의 stage 값이 목록에 없습니다">? {e(stage)}</span>'
    idx = STAGES.index(stage)
    return (f'<span class="chip"><span class="dot" style="background:var(--s{idx + 1})"></span>'
            f'{e(stage)}</span>')


def deadline_cell(deadline):
    d = days_left(deadline)
    if not deadline:
        return '<span style="color:var(--ink-muted)">—</span>'
    if d is None:
        return e(deadline)
    date_line = f'<br><span style="color:var(--ink-muted);font-size:12px">{e(deadline)}</span>'
    if d < 0:
        return f'<span class="crit">✕ 마감 {-d}일 지남</span>{date_line}'
    cls = "crit" if d <= 3 else ("warn" if d <= 7 else "")
    tag = f'<span class="{cls}">{"⚠ " if d <= 7 else ""}D-{d}</span>' if cls else f"D-{d}"
    return f"{tag}{date_line}"


def build():
    exps = collect_experiences()
    apps = collect_applications()
    count_usage(exps, apps)

    active = [a for a in apps if a["stage"] not in TERMINAL]
    soon = [a for a in active
            if (dl := days_left(a["deadline"])) is not None and 0 <= dl <= 7]
    me_dir = BUNDLE / "me"
    drafts = sum(1 for p in me_dir.rglob("*.md")
                 if p.name not in ("index.md", "log.md", "_template.md")
                 and parse_frontmatter(p)[0].get("status") == "draft") if me_dir.is_dir() else 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    h = []
    h.append("<!doctype html><html lang='ko'><head><meta charset='utf-8'>")
    h.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    h.append("<title>취업 준비 대시보드</title>")
    h.append(f"<style>{CSS}</style></head><body>")

    h.append("<header class='masthead'><div class='wrap'><h1>취업 준비 대시보드</h1>"
             f"<p class='sub'>경험 원자 {len(exps)}개 · 진행 중인 지원 {len(active)}건"
             f" · {now} 기준</p></div></header>")

    h.append("<nav class='gnb' aria-label='섹션 이동'><div class='wrap'><div class='navlinks'>")
    for i, (anchor, label) in enumerate(NAV, start=1):
        on = " class='on'" if i == 1 else ""
        h.append(f"<a href='#{anchor}'{on}><span class='idx'>{i:02d}</span>{e(label)}</a>")
    h.append("</div><button class='themebtn' id='theme'>테마</button></div></nav>")

    h.append("<main class='wrap'>")

    # ── 01 요약 ──
    h.append("<section id='summary'><div class='sec-head'><span class='sec-tag'>01 — 요약</span>"
             "<h2>지금 상태</h2></div><div class='tiles'>")
    for label, value, note in [
        ("진행 중인 지원", len(active), f"전체 {len(apps)}건"),
        ("7일 내 마감", len(soon), soon[0]["company"] if soon else "없음"),
        ("경험 원자", len(exps), f"지원 건에 쓰인 것 {sum(1 for x in exps if x['uses'])}개"),
        ("미완성 me/ 문서", drafts, "사실의 출처 채우기"),
    ]:
        h.append(f"<div class='card tile'><div class='label'>{e(label)}</div>"
                 f"<div class='value'>{value}</div><div class='note'>{e(note)}</div></div>")
    h.append("</div></section>")

    # ── 02 지원 현황 ──
    h.append("<section id='apps'><div class='sec-head'><span class='sec-tag'>02 — 지원 현황</span>"
             "<h2>회사별 진행 상황</h2><p>회사 폴더 하나가 지원 건 하나입니다. "
             "각 폴더의 <code>meta.md</code>를 갱신하면 이 표가 따라 바뀝니다.</p></div>")
    if apps:
        stage_counts = Counter(a["stage"] for a in apps)
        h.append("<div class='filters' id='app-filters'>")
        h.append("<div class='fgroup'><span class='flabel'>단계</span>")
        for s in STAGES + list(TERMINAL):
            if stage_counts.get(s):
                h.append(f"<button class='fbtn' type='button' aria-pressed='false' "
                         f"data-stage=\"{e(s)}\">{e(s)}"
                         f"<span class='n'>{stage_counts[s]}</span></button>")
        h.append("</div><div class='fgroup'><span class='flabel'>마감</span>")
        for val, label in DUE_PRESETS:
            h.append(f"<button class='fbtn' type='button' "
                     f"aria-pressed='{'true' if val == 'all' else 'false'}' "
                     f"data-due='{val}'>{e(label)}</button>")
        h.append("</div><div class='fgroup'>"
                 "<input class='fsearch' type='search' placeholder='회사명 검색' "
                 "aria-label='회사명 검색'></div>")
        h.append("<span class='fcount' id='apps-count'></span></div>")

        h.append("<div class='card tablecard'>")
        h.append("<table><thead><tr><th>회사 · 직무</th><th>단계</th><th>마감</th>"
                 "<th>다음 할 일</th><th>바로가기</th></tr></thead><tbody>")
        order = {s: i for i, s in enumerate(STAGES)}
        for a in sorted(apps, key=lambda x: (x["stage"] in TERMINAL,
                                             -order.get(x["stage"], 0))):
            badge = "<span class='sample'>샘플</span>" if a["sample"] else ""
            track = f"<span class='track'>{e(a['track'])}</span> " if a["track"] else ""
            links = " · ".join(
                f"<a href=\"{doc_link(a['folder'] / f)}\">{n}</a>"
                for f, n in [("strategy.md", "전략"), ("cover-letter.md", "자소서"),
                             ("interview.md", "면접")] if (a["folder"] / f).exists())
            d = days_left(a["deadline"])
            search_key = f"{a['company']} {a['role']} {a['track']}".lower()
            h.append(
                f"<tr data-stage=\"{e(a['stage'])}\" data-days=\"{'' if d is None else d}\" "
                f"data-company=\"{e(search_key)}\">"
                f"<td><a href=\"{doc_link(a['folder'] / 'index.md')}\" "
                f"style='text-decoration:none'><span class='co'>{e(a['company'])}</span></a>"
                f"{badge}<br><span class='role'>{track}{e(a['role'])}</span></td>"
                f"<td>{stage_chip(a['stage'])}"
                f"{('<span class=note>' + e(a['stage_note']) + '</span>') if a['stage_note'] else ''}</td>"
                f"<td class='num'>{deadline_cell(a['deadline'])}</td>"
                f"<td style='color:var(--ink-2)'>{e(a['next_action']) or '—'}</td>"
                f"<td style='font-size:12px'>{links or '—'}</td></tr>")
        h.append("</tbody></table>"
                 "<div class='fnone' id='apps-none' hidden>조건에 맞는 지원 건이 없습니다.</div>"
                 "</div>")
    else:
        h.append("<div class='card'><div class='empty'>아직 지원 건이 없습니다. "
                 "<code>applications/_template/</code>를 복사해서 회사 폴더를 만드세요."
                 "</div></div>")
    h.append("</section>")

    # ── 03 경험 원자 ──
    h.append("<section id='exps'><div class='sec-head'><span class='sec-tag'>03 — 경험 원자</span>"
             "<h2>지원 건에 자주 쓰인 순</h2><p>회사 폴더의 마크다운에서 경험 파일이 참조된 "
             "횟수로 정렬합니다. <code>strategy.md</code> 매핑표에 링크를 걸면 집계에 "
             "잡힙니다.</p></div>")
    if exps:
        tag_counts = Counter(t for x in exps for t in x["tags"])
        if tag_counts:
            h.append("<div class='filters' id='exp-filters'>"
                     "<div class='fgroup'><span class='flabel'>태그</span>")
            ranked = tag_counts.most_common()
            for i, (t, c) in enumerate(ranked):
                extra = " hidden class='fbtn more'" if i >= TAG_VISIBLE else " class='fbtn'"
                h.append(f"<button{extra} type='button' aria-pressed='false' "
                         f"data-tag=\"{e(t)}\">{e(t)}<span class='n'>{c}</span></button>")
            if len(ranked) > TAG_VISIBLE:
                h.append(f"<button class='fbtn ghost' type='button' id='tag-more'>"
                         f"+{len(ranked) - TAG_VISIBLE}개 더</button>")
            h.append("</div><div class='fgroup'>"
                     "<button class='fbtn' type='button' id='exp-reset' hidden>해제</button>"
                     "</div><span class='fcount' id='exps-count'></span></div>")

        def data_tags(x):
            return "|" + "|".join(x["tags"]) + "|" if x["tags"] else "|"

        h.append("<div class='exps' id='exp-grid'>")
        for x in exps:
            badge = "<span class='sample'>샘플</span>" if x["sample"] else ""
            uses = (f"{x['uses']}개 지원 건" if x["uses"]
                    else "<span style='color:var(--ink-muted)'>미사용</span>")
            tags = "".join(f"<span class='tag'>{e(t)}</span>" for t in x["tags"])
            h.append(
                f"<div class='card exp' data-tags=\"{e(data_tags(x))}\"><div class='top'>"
                f"<a class='name' href=\"{doc_link(x['path'])}\">{e(x['title'])}</a>{badge}"
                f"<span class='uses'>{uses}</span></div>"
                f"<p class='desc'>{e(x['description']) or '설명 없음'}</p>"
                f"<div>{tags}</div></div>")
        h.append("</div>")
        h.append("<nav class='pager' id='exp-pager' aria-label='경험 원자 페이지' hidden></nav>")
        h.append("<div class='card' id='exps-none' hidden style='margin-top:12px'>"
                 "<div class='fnone'>선택한 태그에 맞는 경험 원자가 없습니다.</div></div>")
    else:
        h.append("<div class='card'><div class='empty'>아직 경험 원자가 없습니다. "
                 "<code>me/experiences/_template.md</code>를 복사해서 사건 단위로 하나씩 "
                 "만드세요.</div></div>")
    h.append("</section>")

    # ── 04 바로가기 ──
    h.append("<section id='links'><div class='sec-head'>"
             "<span class='sec-tag'>04 — 바로가기</span><h2>자주 여는 문서</h2></div>"
             "<div class='links'>")
    groups = [
        ("나 (사실의 출처)", [("커리어 서사", "me/narrative.md"),
                              ("역량 인벤토리", "me/skills.md"),
                              ("포트폴리오", "me/portfolio.md"),
                              ("지원 기준", "me/target-criteria.md"),
                              ("프로필", "me/profile.md")]),
        ("공용 자산", [("질문 은행", "library/question-bank.md"),
                       ("필기·과제 복기", "library/assessments/review-log.md"),
                       ("지원 회고", "library/retrospectives/index.md")]),
        ("운영", [("AI 작업 규칙", "CLAUDE.md"), ("플레이북", "playbook.md"),
                  ("번들 목차", "index.md"), ("업데이트 로그", "log.md")]),
    ]
    for title, items in groups:
        h.append(f"<div class='card'><h3>{e(title)}</h3><ul>")
        for name, rel in items:
            if (BUNDLE / rel).exists():
                h.append(f"<li><a href=\"{doc_link(BUNDLE / rel)}\">{e(name)}</a></li>")
        h.append("</ul></div>")
    h.append("</div></section>")

    h.append("</main>")
    scheme_note = {
        "obsidian": f"제목 링크는 Obsidian 보관함 “{e(VAULT)}”에서 열립니다.",
        "vscode": "제목 링크는 VS Code에서 열립니다.",
        "file": "제목 링크는 기본 앱으로 열립니다.",
    }.get(LINK_SCHEME, "")
    h.append(f"<footer><div class='wrap'>{scheme_note} 링크가 안 열리면 "
             f"<code>--vault 이름</code> 또는 <code>--links vscode</code> 옵션을 쓰세요.<br>"
             f"갱신: 터미널에서 <code>python3 build-dashboard.py</code> · "
             f"마지막 생성 {now}</div></footer>")
    h.append(f"<script>{JS.replace(chr(95)*2 + 'PAGE_SIZE' + chr(95)*2, str(PAGE_SIZE))}</script></body></html>")

    OUT.write_text("".join(h), encoding="utf-8")
    print(f"✓ {OUT.name} 생성 — 경험 원자 {len(exps)}개, 지원 건 {len(apps)}건, "
          f"링크 {LINK_SCHEME}")
    for folder, stage in UNKNOWN_STAGES:
        print(f"⚠ {folder}/meta.md: stage '{stage}' 는 목록에 없습니다. "
              f"사용 가능: {' / '.join(STAGES + list(TERMINAL))}. 세부 단계는 stage_note에 적으세요.",
              file=sys.stderr)


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        sys.exit("Python 3.8 이상이 필요합니다.")
    build()
