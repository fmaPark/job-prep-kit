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
    -h, --help     이 사용법만 보여 주고 끝낸다. 빌드하지 않는다.

읽는 것
    me/experiences/*.md        경험 원자 (프론트매터 title/description/tags)
    applications/*/meta.md     지원 건 상태 — 정본. 칸 설명은 applications/_template/meta.md
    applications/*/**.md       경험 원자 참조 횟수 집계용

쓰는 것
    dashboard.html
    applications/index.md      <!-- AUTO:키 --> … <!-- /AUTO:키 --> 사이만 다시 쓴다
                               (pipeline · week · skipped · results)

meta.md 칸이 이상하면 빌드할 때 ⚠ 경고로 알리고 대시보드 위쪽에도 띄운다.

표준 라이브러리만 씁니다. 설치할 것 없음.
"""

import html
import re
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

BUNDLE = Path(__file__).resolve().parent
OUT = BUNDLE / "dashboard.html"

# --help / -h: 사용법만 보여 주고 아무것도 쓰지 않는다.
if __name__ == "__main__" and ({"-h", "--help"} & set(sys.argv[1:])):
    print(__doc__.strip())
    sys.exit(0)


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

# 진행 단계(순서대로)와 종료 단계. 색은 CSS 변수 --st-<키>.
STAGES = ["관심", "서류작성", "지원완료", "필기·과제", "면접", "결과대기"]
STAGE_KEY = {"관심": "watch", "서류작성": "draft", "지원완료": "sub",
             "필기·과제": "test", "면접": "intv", "결과대기": "final"}
TERMINAL = {"합격": "good", "불합격": "critical", "지원안함": "neutral"}
TERMINAL_LABEL = {"합격": "합격", "불합격": "불합격", "지원안함": "지원 안 함"}
SUBMITTED = {"지원완료", "필기·과제", "면접", "결과대기", "합격", "불합격"}
# 예전·다른 표기 → 현재 이름. 기존 meta.md를 고치지 않아도 되게 경고 없이 읽는다.
STAGE_ALIASES = {"코테·과제": "필기·과제", "코테/과제": "필기·과제", "코테": "필기·과제",
                 "과제": "필기·과제", "필기·코테": "필기·과제", "서류제출": "지원완료",
                 "최종대기": "결과대기", "지원 안 함": "지원안함"}
WEEKDAYS = "월화수목금토일"
WARNINGS = []
BOARD = BUNDLE / "applications" / "index.md"
PAGE_SIZE = int(_arg("--page-size", "9"))   # 경험 원자 카드 한 페이지 개수
TAG_VISIBLE = 12
NAV = [("summary", "요약"), ("apps", "지원 현황"),
       ("exps", "경험 원자"), ("links", "바로가기")]
DUE_PRESETS = [("all", "전체"), ("7", "7일 내"), ("30", "30일 내"), ("none", "날짜 미정"), ("past", "지난 일정")]


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
    # 목록이 아니었던 빈 값은 빈 문자열로 되돌린다 (목록으로 읽는 칸은 빈 목록 유지)
    for k, v in meta.items():
        if v == [] and k not in ("tags", "passed", "skip"):
            meta[k] = ""
    return meta, body


def norm(s):
    """문서 안 링크(NFC)와 macOS 파일명(NFD)을 같은 형태로 맞춘다."""
    return unicodedata.normalize("NFC", s)


# ── 수집 ────────────────────────────────────────────────────────────────

def is_template(name):
    """_template, "_template copy", "_template 복사본"처럼 템플릿 사본도 세지 않는다."""
    return norm(name).startswith("_template")


def stem_pattern(stem):
    """파일 이름 전체가 등장할 때만 맞춘다. "2024-협업"이 "2024-협업갈등"에 걸리지 않게."""
    return re.compile(r"(?<![\w-])" + re.escape(stem) + r"(?![\w-])")


def collect_experiences():
    d = BUNDLE / "me" / "experiences"
    if not d.is_dir():
        return []
    items = []
    for p in sorted(d.glob("*.md")):
        if p.name in ("index.md", "log.md") or is_template(p.name):
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
    for folder in sorted(x for x in d.iterdir() if x.is_dir() and not is_template(x.name)):
        meta, _ = parse_frontmatter(folder / "meta.md")
        if not meta:
            continue
        name = norm(folder.name)
        raw = norm(str(meta.get("stage") or "관심")).strip()
        stage, exit_stage = raw, norm(str(meta.get("exit_stage") or "")).strip()
        m = re.match(r"^(합격|불합격|지원안함)\s*\((.+)\)$", raw)
        if m:
            stage, exit_stage = m.group(1), exit_stage or m.group(2)
            WARNINGS.append(f"{name}: stage '{raw}' → 'stage: {stage}'와 "
                            f"'exit_stage: {m.group(2)}'로 나눠 적으세요")
        elif raw in STAGE_ALIASES:
            stage = STAGE_ALIASES[raw]
        if stage not in STAGES and stage not in TERMINAL:
            WARNINGS.append(f"{name}: 알 수 없는 단계 '{raw}' — 관심으로 표시합니다. "
                            f"사용 가능: {' / '.join(STAGES + list(TERMINAL))}. "
                            "세부 단계는 stage_note에 적으세요")
            stage = "관심"
        when = {k: parse_when(meta.get(k)) for k in
                ("deadline", "applied_at", "next_event_at", "result_at")}
        for k, (dd, _, shown) in when.items():
            if shown and dd is None and not re.match(r"^\d{4}-\d{2}$", shown):
                WARNINGS.append(f"{name}: {k} '{shown}'를 날짜로 읽지 못했습니다 "
                                "(YYYY-MM-DD 또는 YYYY-MM-DD HH:MM)")
        if stage == "불합격" and not exit_stage:
            WARNINGS.append(f"{name}: 불합격인데 exit_stage(어느 전형에서 끝났는지)가 없습니다")
        if stage == "지원안함" and not meta.get("reason"):
            WARNINGS.append(f"{name}: 지원안함인데 reason이 없습니다")
        if stage in SUBMITTED and not when["applied_at"][2]:
            WARNINGS.append(f"{name}: 제출 이후 단계인데 applied_at이 없습니다")
        apps.append({
            "folder": folder,
            "name": name,
            "company": norm(str(meta.get("company") or name)),
            "role": norm(str(meta.get("role") or "")),
            "track": norm(str(meta.get("track") or "")),
            "stage": stage,
            "stage_note": norm(str(meta.get("stage_note") or "")),
            "priority": norm(str(meta.get("priority") or "")),
            "deadline": when["deadline"],
            "applied": when["applied_at"],
            "event": when["next_event_at"],
            "result": when["result_at"],
            "next_event": norm(str(meta.get("next_event") or "")),
            "next_action": norm(str(meta.get("next_action") or "")),
            "exit_stage": exit_stage,
            "reason": norm(str(meta.get("reason") or "")),
            "passed": as_list(meta.get("passed")),
            "skip": as_list(meta.get("skip")),
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
            if exp["stem"] and stem_pattern(exp["stem"]).search(blob):
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


def parse_when(raw):
    # 'YYYY-MM-DD', 'YYYY-MM-DD HH:MM', ISO('…T17:00:00+09:00'), 'YYYY-MM'을 받는다.
    # 반환: (date 또는 None, 'HH:MM' 또는 '', 표시용 문자열)
    s = norm(str(raw or "")).strip()
    if not s:
        return None, "", ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?", s)
    if not m:
        return None, "", s
    try:
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None, "", s
    t = f"{m.group(4)}:{m.group(5)}" if m.group(4) else ""
    return d, t, d.isoformat() + (f" {t}" if t else "")


def days_until(d):
    return None if d is None else (d - date.today()).days


def fmt_day(d, t=""):
    return f"{d:%m/%d}({WEEKDAYS[d.weekday()]})" + (f" {t}" if t else "")


def fmt_full(d, t=""):
    return f"{d.isoformat()}({WEEKDAYS[d.weekday()]})" + (f" {t}" if t else "")


def short(company):
    return re.sub(r"\s*\(.*\)\s*$", "", company) or company


def as_list(v):
    if isinstance(v, list):
        return [norm(x) for x in v if x]
    v = norm(str(v or "")).strip()
    return [x.strip() for x in v.split(",") if x.strip()] if v else []


def step_group(name):
    # 전형 이름 → 집계 묶음: '서류' / '면접' / 그 밖(코테·인적성·과제·PT …)은 '필기·과제'
    n = name or ""
    if not n:
        return ""
    if "서류" in n:
        return "서류"
    if "면접" in n:
        return "면접"
    return "필기·과제"


def next_point(a):
    # 다음에 챙길 날짜 — 제출 전이면 서류 마감, 제출 뒤면 다음 전형. (date|None, 시각, 라벨)
    if a["stage"] in TERMINAL:
        return None, "", ""
    if a["stage"] in ("관심", "서류작성"):
        d, t, _ = a["deadline"]
        return d, t, "서류 마감"
    d, t, _ = a["event"]
    return d, t, a["next_event"]


def sort_active(a):
    d, _, _ = next_point(a)
    return (d is None, d or date.max, -STAGES.index(a["stage"]))


def sort_closed(a):
    return max(a["result"][2], a["applied"][2], a["deadline"][2])


def funnel(apps):
    real = [a for a in apps if not a["sample"]]
    sub = [a for a in real if a["stage"] in SUBMITTED]

    def groups(xs):
        return {step_group(x) for x in xs}

    def reached(a, g):
        return g in groups(a["passed"]) or step_group(a["exit_stage"]) == g

    direct = [a for a in sub if "서류" in groups(a["skip"])]
    doc = [a for a in sub if "서류" not in groups(a["skip"])]
    doc_done = [a for a in doc if reached(a, "서류")]
    return {
        "sub": sub,
        "open": [a for a in sub if a["stage"] not in TERMINAL],
        "closed": [a for a in sub if a["stage"] in TERMINAL],
        "direct": direct,
        "doc": doc,
        "doc_done": doc_done,
        "doc_pass": [a for a in doc if "서류" in groups(a["passed"])],
        "doc_fail": [a for a in doc if step_group(a["exit_stage"]) == "서류"],
        "doc_wait": [a for a in doc if not reached(a, "서류") and a["stage"] not in TERMINAL],
        "test_done": [a for a in sub if reached(a, "필기·과제")],
        "test_pass": [a for a in sub if "필기·과제" in groups(a["passed"])],
        "test_now": [a for a in sub if a["stage"] == "필기·과제"],
        "intv": [a for a in sub if reached(a, "면접") or a["stage"] in ("면접", "결과대기", "합격")],
    }


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
  --st-watch:#8f8d86; --st-draft:#c98a00; --st-sub:#2a78d6; --st-test:#7b55d6; --st-intv:#0f8f84; --st-final:#c2417a;
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
    --st-watch:#a3a29b; --st-draft:#f0b429; --st-sub:#5598e7; --st-test:#a48af0; --st-intv:#3cc1b3; --st-final:#e57aa6;
    --accent:#3987e5; --accent-soft:rgba(57,135,229,0.18);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --plane:#0d0d0d; --surface:#1a1a19;
  --ink:#ffffff; --ink-2:#c3c2b7; --ink-muted:#898781;
  --line:rgba(255,255,255,0.10); --rule:#2c2c2a;
  --st-watch:#a3a29b; --st-draft:#f0b429; --st-sub:#5598e7; --st-test:#a48af0; --st-intv:#3cc1b3; --st-final:#e57aa6;
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
td .note { display:block; font-size:11px; color:var(--ink-muted); margin-top:3px; }

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

/* 칩 — 단계마다 색이 다르다 */
.chip { --c:var(--ink-muted); display:inline-flex; align-items:center; gap:6px; font-size:12px;
        white-space:nowrap; padding:2px 9px 2px 8px; border-radius:999px; color:var(--ink);
        background:color-mix(in srgb, var(--c) 14%, transparent);
        border:1px solid color-mix(in srgb, var(--c) 38%, transparent); }
.dot { width:8px; height:8px; border-radius:50%; flex:none; background:var(--c); }
.st-watch { --c:var(--st-watch); } .st-draft { --c:var(--st-draft); } .st-sub { --c:var(--st-sub); }
.st-test { --c:var(--st-test); } .st-intv { --c:var(--st-intv); } .st-final { --c:var(--st-final); }
.st-pass { --c:var(--good); } .st-fail { --c:var(--critical); } .st-skip { --c:var(--ink-muted); }
.st-watch.dot, .st-watch .dot { background:transparent; box-shadow:inset 0 0 0 1.5px var(--c); }
.chip.st-fail { color:var(--critical); } .chip.st-pass { color:var(--good); }
.chip.st-skip { color:var(--ink-2); }
.fbtn .dot { display:inline-block; width:7px; height:7px; margin-right:6px; vertical-align:1px; }
.tag { display:inline-block; font-size:11px; color:var(--ink-2); border:1px solid var(--line);
       border-radius:999px; padding:1px 8px; margin:0 4px 4px 0; }
.track { font-size:11px; color:var(--ink-2); border:1px solid var(--line);
         border-radius:4px; padding:1px 6px; }
.warn { color:#8a5a00; } .crit { color:var(--critical); } .ok { color:var(--good); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .warn { color:var(--warning); } }
:root[data-theme="dark"] .warn { color:var(--warning); }

/* 지원 현황 부가 */
.prio { font-size:10.5px; border:1px solid var(--line); border-radius:3px; padding:0 5px;
        color:var(--ink-2); margin-left:6px; vertical-align:1px; }
.mute { color:var(--ink-muted); }
.small { font-size:12px; }
td.when { font-variant-numeric:tabular-nums; min-width:130px; }
td.when .d { font-weight:600; }
td.when .small, td.golinks { white-space:nowrap; }
.tiles-label { font-family:var(--mono); font-size:10px; font-weight:600; letter-spacing:0.09em;
               text-transform:uppercase; color:var(--ink-muted); margin:22px 0 9px; }
.closed { margin-top:14px; }
.closed > summary { cursor:pointer; padding:13px 16px; font-size:13.5px; font-weight:600;
                    list-style:none; }
.closed > summary::-webkit-details-marker { display:none; }
.closed > summary::before { content:"▸"; display:inline-block; width:16px; color:var(--ink-muted); }
.closed[open] > summary::before { content:"▾"; }
.closed[open] > summary { border-bottom:1px solid var(--rule); }
.closed .mute { font-weight:400; }
.notice { padding:12px 16px; margin-bottom:14px; font-size:13px;
          border-color:color-mix(in srgb, var(--warning) 60%, transparent); }
.notice ul { margin:6px 0 0; padding-left:18px; color:var(--ink-2); }

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
        || (due === 'none' ? d === null
          : due === 'past' ? (d !== null && d < 0)
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


def stage_chip(a):
    s = a["stage"]
    if s == "합격":
        return "<span class='chip st-pass'>✓ 합격</span>"
    if s == "불합격":
        txt = f"{a['exit_stage']} 탈락" if a["exit_stage"] else "불합격"
        return f"<span class='chip st-fail'>✕ {e(txt)}</span>"
    if s == "지원안함":
        return "<span class='chip st-skip'>지원 안 함</span>"
    note = f"<span class='note'>{e(a['stage_note'])}</span>" if a.get("stage_note") else ""
    return f"<span class='chip st-{STAGE_KEY[s]}'><span class='dot'></span>{e(s)}</span>{note}"


def folder_doc(a):
    return a["folder"] / ("index.md" if (a["folder"] / "index.md").exists() else "meta.md")


def company_cell(a):
    badge = "<span class='sample'>샘플</span>" if a["sample"] else ""
    prio = f"<span class='prio'>{e(a['priority'])}</span>" if a["priority"] else ""
    track = f"<span class='track'>{e(a['track'])}</span> " if a["track"] else ""
    return (f"<a href=\"{doc_link(folder_doc(a))}\" style='text-decoration:none'>"
            f"<span class='co'>{e(a['company'])}</span></a>{prio}{badge}"
            f"<br><span class='role'>{track}{e(a['role'])}</span>")


def links_cell(a):
    links = "<br>".join(
        f"<a href=\"{doc_link(a['folder'] / f)}\">{n}</a>"
        for f, n in [("strategy.md", "전략"), ("cover-letter.md", "자소서"),
                     ("interview.md", "면접")] if (a["folder"] / f).exists())
    return links or "<span class='mute'>—</span>"


def date_cell(when):
    d, _, shown = when
    if d is not None:
        return e(d.isoformat())
    return e(shown) if shown else "<span class='mute'>—</span>"


def next_cell(a):
    d, t, label = next_point(a)
    if d is None:
        if not label:
            return "<span class='mute'>—</span>"
        return f"{e(label)}<br><span class='mute small'>날짜 미정</span>"
    n = days_until(d)
    if n < 0:
        tag = f"<span class='crit'>✕ {-n}일 지남 · meta.md 갱신</span>"
    elif n == 0:
        tag = "<span class='crit d'>⚠ 오늘</span>"
    elif n <= 3:
        tag = f"<span class='crit d'>⚠ D-{n}</span>"
    elif n <= 7:
        tag = f"<span class='warn d'>⚠ D-{n}</span>"
    else:
        tag = f"<span class='d'>D-{n}</span>"
    return f"{e(label)}<br>{tag} <span class='mute small'>{e(fmt_day(d, t))}</span>"


# ── applications/index.md 자동 블록 ───────────────────────────────────

def md(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()


def board_link(a):
    path = "/" + norm(folder_doc(a).relative_to(BUNDLE).as_posix())
    return f"<{path}>" if " " in path else path


def board_status(a):
    s = a["stage"]
    if s in ("합격", "불합격"):
        bits = []
        if s == "불합격" and a["exit_stage"]:
            bits.append(f"{a['exit_stage']} 탈락")
        if "서류" in {step_group(x) for x in a["skip"]}:
            bits.append("서류 없이 직행")
        if a["result"][2]:
            bits.append(a["result"][2].split(" ")[0])
        return f"**{s}**" + (f" ({' · '.join(bits)})" if bits else "")
    return (f"**{s}**" + (f" ({a['stage_note']})" if a["stage_note"] else "")
            + (f" · {a['priority']}" if a["priority"] else ""))


def board_next(a):
    d, t, label = next_point(a)
    if d is not None:
        return f"{label} {fmt_full(d, t)}"
    return f"{label} (날짜 미정)" if label else "—"


def board_blocks(apps, today):
    real = [a for a in apps if not a["sample"]]
    active = sorted((a for a in real if a["stage"] not in TERMINAL), key=sort_active)
    done = sorted((a for a in real if a["stage"] in ("합격", "불합격")),
                  key=sort_closed, reverse=True)
    skipped = sorted((a for a in real if a["stage"] == "지원안함"),
                     key=lambda a: a["result"][2] or a["deadline"][2])
    blocks = {}

    rows = [f"> 자동 생성 · {today} — 각 회사 폴더의 `meta.md`를 고친 뒤 "
            "`python3 build-dashboard.py`를 돌리면 다시 써진다. 여기를 손으로 고치면 다음 빌드 때 사라진다.",
            "",
            "| 회사 | 직무 | 트랙 | 지원일 | 상태 | 다음 일정 | 다음 할 일 |",
            "|---|---|---|---|---|---|---|"]
    for a in active + done:
        co = f"[{md(a['company'])}]({board_link(a)})"
        if a["stage"] not in TERMINAL:
            co = f"**{co}**"
        applied = a["applied"][2].split(" ")[0] if a["applied"][2] else "—"
        rows.append(f"| {co} | {md(a['role'])} | {md(a['track']) or '—'} | {applied} | "
                    f"{md(board_status(a))} | {md(board_next(a))} | "
                    f"{md(a['next_action']) or '—'} |")
    rows += ["", "단계: " + " → ".join(f"`{s}`" for s in STAGES) + " → "
             + " / ".join(f"`{s}`" for s in TERMINAL)]
    blocks["pipeline"] = "\n".join(rows)

    soon, later, undated, stale = [], [], [], []
    for a in active:
        d, t, label = next_point(a)
        n = days_until(d)
        name = short(a["company"])
        if n is None:
            if label:
                undated.append(f"{name}({label})")
        elif n < 0:
            stale.append(f"{name} {label} {fmt_full(d, t)}")
        elif n <= 7:
            soon.append(f"* **{name} {label} — {fmt_full(d, t)}**"
                        + (f" · {a['priority']}" if a["priority"] else ""))
        elif n <= 14:
            later.append(f"{name} {label} — {fmt_full(d, t)}")
    lines = [f"_{today} 기준 7일 안. 서류 마감은 아직 제출 전인 건만 센다._", ""]
    lines += soon or ["* 7일 안에 잡힌 일정 없음"]
    if later:
        lines.append("* 그다음 주: " + " · ".join(later))
    if undated:
        lines.append("* 날짜 미정: " + " · ".join(undated))
    if stale:
        lines.append("* ⚠ 날짜가 지났는데 `meta.md`가 그대로인 건: " + " · ".join(stale))
    blocks["week"] = "\n".join(lines)

    rows = ["| 회사 | 직무 | 결정일 | 근거 |", "|---|---|---|---|"]
    for a in skipped:
        when = a["result"][2].split(" ")[0] if a["result"][2] else "—"
        rows.append(f"| **[{md(a['company'])}]({board_link(a)})** | {md(a['role'])} | "
                    f"**{when}** | {md(a['reason']) or '—'} |")
    if not skipped:
        rows.append("| — | — | — | — |")
    blocks["skipped"] = "\n".join(rows)

    fn = funnel(apps)

    def names(xs):
        return " · ".join(short(a["company"]) for a in xs)

    def tagged(label, xs):
        return f"{label} {len(xs)}: {names(xs)}" if xs else ""

    def cell(xs, *extras):
        ex = " · ".join(x for x in extras if x)
        return f"{len(xs)}건" + (f" ({ex})" if ex else "")

    fail_note = f" ({tagged('탈락', fn['doc_fail'])})" if fn["doc_fail"] else ""
    rows = ["| 지표 | 값 |", "|---|---|",
            f"| 지원 | **{len(fn['sub'])}건** (진행 중 {len(fn['open'])} · 종료 {len(fn['closed'])}) |",
            f"| 서류 전형 있는 건 | {cell(fn['doc'], tagged('서류 없이 직행', fn['direct']))} |",
            f"| 서류 결과 확인 | {cell(fn['doc_done'], tagged('대기', fn['doc_wait']))} |",
            f"| 서류 통과 | **{len(fn['doc_pass'])}건**{fail_note} |",
            f"| 필기·과제 응시 | {cell(fn['test_done'], names(fn['test_done']), tagged('진행 중', fn['test_now']))} |",
            f"| **필기·과제 통과** | **{len(fn['test_pass'])}건** |",
            f"| 면접 진출 | {cell(fn['intv'], names(fn['intv']))} |"]
    blocks["results"] = "\n".join(rows)
    return blocks


def replace_block(text, key, body):
    start, end = f"<!-- AUTO:{key} -->", f"<!-- /AUTO:{key} -->"
    i = text.find(start)
    j = text.find(end, i + 1) if i >= 0 else -1
    if i < 0 or j < 0:
        WARNINGS.append(f"applications/index.md: {start} … {end} 표시가 없어 이 블록을 건너뛰었습니다")
        return text
    return text[:i + len(start)] + "\n" + body.rstrip() + "\n" + text[j:]


def write_board(apps, today):
    if not BOARD.exists():
        return False
    raw = BOARD.read_text(encoding="utf-8")
    text = norm(raw)
    for key, body in board_blocks(apps, today).items():
        text = replace_block(text, key, body)
    if not unicodedata.is_normalized("NFC", raw):
        text = unicodedata.normalize("NFD", text)
    if text == raw:
        return False
    BOARD.write_text(text, encoding="utf-8")
    return True


def build():
    exps = collect_experiences()
    apps = collect_applications()
    count_usage(exps, apps)
    board_written = write_board(apps, date.today().isoformat())

    active = [a for a in apps if a["stage"] not in TERMINAL]
    closed = [a for a in apps if a["stage"] in TERMINAL]
    me_dir = BUNDLE / "me"
    drafts = sum(1 for p in me_dir.rglob("*.md")
                 if p.name not in ("index.md", "log.md") and not is_template(p.name)
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
    fn = funnel(apps)
    upcoming = []
    for a in active:
        d, _, label = next_point(a)
        n = days_until(d)
        if n is not None and 0 <= n <= 7:
            upcoming.append((n, short(a["company"]), label))
    upcoming.sort()
    if upcoming:
        n0, co0, lb0 = upcoming[0]
        nearest = f"{co0} {lb0} " + ("오늘" if n0 == 0 else f"D-{n0}")
    else:
        nearest = "없음"
    prep = sum(1 for a in active if a["stage"] in ("관심", "서류작성"))

    def tiles(items):
        out = ["<div class='tiles'>"]
        for label, value, note in items:
            out.append(f"<div class='card tile'><div class='label'>{e(label)}</div>"
                       f"<div class='value'>{e(str(value))}</div><div class='note'>{e(note)}</div></div>")
        out.append("</div>")
        return "".join(out)

    h.append("<section id='summary'><div class='sec-head'><span class='sec-tag'>01 — 요약</span>"
             "<h2>지금 상태</h2></div>")
    h.append(tiles([
        ("진행 중인 지원", len(active), f"제출 후 {len(active) - prep}건 · 준비 중 {prep}건"),
        ("7일 내 일정", len(upcoming), nearest),
        ("경험 원자", len(exps), f"지원 건에 쓰인 것 {sum(1 for x in exps if x['uses'])}개"),
        ("미완성 me/ 문서", drafts, "사실의 출처 채우기"),
    ]))
    h.append("<div class='tiles-label'>지원 결과 누적</div>")
    h.append(tiles([
        ("지원", len(fn["sub"]), f"진행 중 {len(fn['open'])} · 종료 {len(fn['closed'])}"),
        ("서류 통과", f"{len(fn['doc_pass'])} / {len(fn['doc_done'])}",
         f"결과 대기 {len(fn['doc_wait'])} · 서류 없이 직행 {len(fn['direct'])}"),
        ("필기·과제 통과", f"{len(fn['test_pass'])} / {len(fn['test_done'])}",
         f"결과 나온 건 기준 · 진행 중 {len(fn['test_now'])}"),
        ("면접 진출", len(fn["intv"]), "1차 면접 이상"),
    ]))
    h.append("</section>")

    # ── 02 지원 현황 ──
    h.append("<section id='apps'><div class='sec-head'><span class='sec-tag'>02 — 지원 현황</span>"
             "<h2>회사별 진행 상황</h2><p>각 회사 폴더의 <code>meta.md</code>가 정본입니다. "
             "고친 뒤 빌더를 돌리면 이 표와 <code>applications/index.md</code>의 보드가 함께 "
             "바뀝니다. 다음 일정이 가까운 순서입니다.</p></div>")
    if WARNINGS:
        h.append(f"<div class='card notice'><b>meta.md 확인 필요 {len(WARNINGS)}건</b><ul>"
                 + "".join(f"<li>{e(w)}</li>" for w in WARNINGS) + "</ul></div>")
    if apps:
        stage_counts = Counter(a["stage"] for a in active)
        h.append("<div class='filters' id='app-filters'>")
        h.append("<div class='fgroup'><span class='flabel'>단계</span>")
        for s in STAGES:
            if stage_counts.get(s):
                h.append(f"<button class='fbtn' type='button' aria-pressed='false' "
                         f"data-stage=\"{e(s)}\"><span class='dot st-{STAGE_KEY[s]}'></span>"
                         f"{e(s)}<span class='n'>{stage_counts[s]}</span></button>")
        h.append("</div><div class='fgroup'><span class='flabel'>일정</span>")
        for val, label in DUE_PRESETS:
            h.append(f"<button class='fbtn' type='button' "
                     f"aria-pressed='{'true' if val == 'all' else 'false'}' "
                     f"data-due='{val}'>{e(label)}</button>")
        h.append("</div><div class='fgroup'>"
                 "<input class='fsearch' type='search' placeholder='회사명 검색' "
                 "aria-label='회사명 검색'></div>")
        h.append("<span class='fcount' id='apps-count'></span></div>")

        h.append("<div class='card tablecard'>")
        h.append("<table><thead><tr><th>회사 · 직무</th><th>단계</th><th>지원일</th>"
                 "<th>다음 일정</th><th>다음 할 일</th><th>바로가기</th></tr></thead><tbody>")
        for a in sorted(active, key=sort_active):
            d, _, _ = next_point(a)
            n = days_until(d)
            search_key = f"{a['company']} {a['role']} {a['track']}".lower()
            h.append(
                f"<tr data-stage=\"{e(a['stage'])}\" data-days=\"{'' if n is None else n}\" "
                f"data-company=\"{e(search_key)}\">"
                f"<td>{company_cell(a)}</td><td>{stage_chip(a)}</td>"
                f"<td class='num'>{date_cell(a['applied'])}</td>"
                f"<td class='when'>{next_cell(a)}</td>"
                f"<td style='color:var(--ink-2)'>{e(a['next_action']) or '—'}</td>"
                f"<td class='golinks' style='font-size:12px'>{links_cell(a)}</td></tr>")
        h.append("</tbody></table>"
                 "<div class='fnone' id='apps-none' hidden>조건에 맞는 지원 건이 없습니다.</div>"
                 "</div>")

        if closed:
            cnt = Counter(a["stage"] for a in closed)
            summ = " · ".join(f"{TERMINAL_LABEL[s]} {cnt[s]}" for s in TERMINAL if cnt.get(s))
            h.append(f"<details class='card closed'><summary>종료된 지원 {len(closed)}건 "
                     f"<span class='mute'>— {e(summ)}</span></summary><div class='tablecard'>"
                     "<table><thead><tr><th>회사 · 직무</th><th>결과</th><th>지원일</th>"
                     "<th>결과일</th><th>메모</th></tr></thead><tbody>")
            for a in sorted(closed, key=sort_closed, reverse=True):
                memo = a["reason"] if a["stage"] == "지원안함" else a["next_action"]
                memo = memo.replace("**", "")
                h.append(f"<tr><td>{company_cell(a)}</td><td>{stage_chip(a)}</td>"
                         f"<td class='num'>{date_cell(a['applied'])}</td>"
                         f"<td class='num'>{date_cell(a['result'])}</td>"
                         f"<td style='color:var(--ink-2)'>{e(memo) or '—'}</td></tr>")
            h.append("</tbody></table></div></details>")
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
    if board_written:
        print("✓ applications/index.md 자동 블록 갱신")
    for w in WARNINGS:
        print(f"⚠ {w}")


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        sys.exit("Python 3.8 이상이 필요합니다.")
    build()
