---
type: Guide
title: 대시보드
description: build-dashboard.py 실행법, 옵션, 읽어 가는 파일, 링크가 열리는 방식과 문제 해결.
generated: { by: claude-code/claude-fable-5-1, at: 2026-09-08T00:30:00Z }
---

# 대시보드

`build-dashboard.py`는 이 폴더를 훑어 `dashboard.html` 한 파일을 만듭니다.
Python 표준 라이브러리만 쓰므로 설치할 것이 없습니다. **Python 3.8 이상**이면 됩니다.

## 실행

폴더 안에서 터미널을 열고:

```bash
python3 build-dashboard.py
```

Windows에서는 `py build-dashboard.py` 또는 `python build-dashboard.py`.

`dashboard.html`을 브라우저로 엽니다. 정적 HTML이라 브라우저가 폴더를 스스로 읽지 못합니다.
**만든 시점의 스냅샷**이므로 문서를 바꾼 뒤에는 다시 실행해야 합니다.
`dashboard.html`은 생성물이라 `.gitignore`에 들어 있습니다. 각자 만들어서 씁니다.

## 보여주는 것

- **요약** — 진행 중인 지원, 7일 내 마감, 경험 원자 수, 미완성(`status: draft`) 문서 수
- **지원 현황** — 회사별 단계 · 마감(D-day) · 다음 할 일. 단계 칩, 마감 프리셋, 회사명 검색으로 거를 수 있습니다
- **경험 원자** — 지원 건에서 참조된 횟수 순. 태그 필터(OR)와 페이지네이션
- **바로가기** — 자주 여는 문서

문서 제목을 누르면 원본 마크다운이 열립니다. 어디서 열리는지는 아래 "링크가 열리는 방식"을 보세요.

## 읽어 가는 파일

| 읽는 파일 | 쓰이는 곳 |
|---|---|
| `me/experiences/*.md`의 프론트매터 | 경험 원자 카드 (`title`, `description`, `tags`) |
| `applications/*/meta.md`의 프론트매터 | 지원 현황 표 (`company`, `role`, `track`, `stage`, `stage_note`, `deadline`, `next_action`) |
| `applications/*/**.md` 본문 | 경험 원자 참조 횟수. 경험 파일 이름이 등장하면 1회로 셉니다 |

- `_template`으로 시작하는 파일 · 폴더는 세지 않습니다. `_sample`로 시작하면 "샘플" 표시가 붙습니다.
- `deadline`은 `YYYY-MM-DD` 형식이어야 D-day가 계산됩니다.
- `stage`는 `관심 / 서류작성 / 지원완료 / 필기·과제 / 면접 / 결과대기 / 합격 / 불합격` 중 하나여야 필터와 정렬이 동작합니다. 예전 이름 `코테·과제`도 받습니다. 목록에 없는 값은 점선 칩으로 그대로 보이고 빌드 시 경고가 납니다. 세부 단계는 `stage_note`에 적으면 단계 옆에 표시됩니다.
- `track`은 자유 텍스트입니다. 표시와 검색에만 쓰입니다.
- `tags`는 한 줄(`tags: [백엔드, 협업]`)과 여러 줄(Obsidian 속성 편집기가 저장하는 형식) 둘 다 읽습니다.
- 경험 원자 정렬이 의미 있게 동작하려면 `strategy.md` 매핑표에 경험 링크를 걸어야 합니다.

## 옵션

| 옵션 | 설명 |
|---|---|
| `--links obsidian` | 기본값. 문서 링크가 Obsidian 보관함에서 열립니다 |
| `--links vscode` | VS Code에서 열립니다 |
| `--links file` | `file://` 링크. 브라우저가 마크다운을 글자 그대로 보여주거나 내려받습니다 |
| `--vault NAME` | Obsidian 보관함 이름 (기본값: 이 폴더 이름) |
| `--page-size N` | 경험 원자 카드 한 페이지 개수 (기본 9) |
| `--base PATH` | 링크에 쓸 절대경로 기준. 다른 컴퓨터에서 만들어 옮길 때만 |

예: `python3 build-dashboard.py --links vscode --page-size 12`

## 링크가 열리는 방식

대시보드의 "문서 열기" 링크는 **기본적으로 Obsidian을 가정**합니다.
Obsidian이 설치되어 있고, 이 폴더를 보관함으로 한 번 이상 열어 두어야 링크가 동작합니다.

- 보관함 이름은 **폴더 이름과 같아야** 합니다. 다르면 `--vault 보관함이름`으로 지정하세요.
- macOS는 한글 폴더명을 내부적으로 다르게 저장하는데(자모 분리), 스크립트가 알아서 맞춥니다. Windows · Linux에서는 그대로 둡니다.
- Obsidian을 쓰지 않는다면 `--links vscode`(VS Code 사용자) 또는 `--links file`을 쓰세요.

## 문제 해결

**링크를 눌러도 아무 일이 없다**
Obsidian이 설치되어 있지 않거나, 이 폴더를 보관함으로 연 적이 없는 경우입니다. Obsidian에서 폴더를 한 번 열거나 `--links vscode`로 다시 만드세요.

**Obsidian이 "Unable to find a vault"라고 한다**
보관함 이름이 폴더 이름과 다릅니다. Obsidian 왼쪽 아래 보관함 이름을 확인하고 `--vault 그이름`을 붙이세요.

**태그가 카드에 안 보인다**
경험 파일 맨 위 프론트매터의 `tags`를 확인하세요. `tags: [a, b]` 또는 아래 형식 둘 다 됩니다.
```yaml
tags:
  - 백엔드
  - 협업
```

**경험 원자가 전부 "0개 지원 건"이다**
회사 폴더의 `strategy.md`나 `cover-letter.md`에 경험 파일 이름이 등장하지 않아서입니다. 매핑표에 `[[/me/experiences/파일이름]]`처럼 링크를 거세요.

**단계 칩이 점선에 물음표로 나온다 / 빌드할 때 ⚠ 경고가 뜬다**
`meta.md`의 `stage` 값이 목록에 없습니다. 위 8개 중 하나로 고치고, 세부 단계는 `stage_note`에 옮기세요.

**마감이 D-day로 안 나온다**
`meta.md`의 `deadline`이 `YYYY-MM-DD` 형식인지 확인하세요.

**`python3: command not found` / `'py'은(는) 내부 또는 외부 명령이 아닙니다`**
Python이 없거나 PATH에 없습니다. [시작 가이드](/docs/getting-started.md)의 "Python 확인"을 보세요.
