---
type: Guide
title: 시작 가이드
description: 내려받기부터 첫 회사 폴더를 만들기까지. 터미널이 낯선 사람 기준으로 쓴 안내.
generated: { by: claude-code/claude-fable-5-1, at: 2026-09-08T00:30:00Z }
updated: { by: claude, at: 2026-11-10T04:02:49Z }
---

# 시작 가이드

이 문서는 "개발 도구가 익숙하지 않은 사람"을 기준으로 씁니다.
각 단계는 한 번만 하면 되는 것과 계속 반복하는 것을 나눠 두었습니다.

## 1. 준비물 확인 (한 번)

### Obsidian 설치

[obsidian.md](https://obsidian.md)에서 내려받아 설치합니다. 무료입니다.
이 저장소의 문서 링크와 대시보드의 "문서 열기" 버튼이 Obsidian을 기준으로 동작하므로, 가능하면 설치하세요.
다른 편집기(VS Code, 메모장 등)로도 파일을 쓸 수는 있지만 링크는 제대로 열리지 않습니다. 그 경우 [대시보드 문서](/docs/dashboard.md)의 "링크가 열리는 방식"을 보세요.

### Python 확인

대시보드를 만들 때만 필요합니다. 문서만 쓸 거라면 건너뛰어도 됩니다.

- **macOS**: 터미널(응용 프로그램 → 유틸리티 → 터미널)을 열고 `python3 --version`을 입력합니다. `Python 3.8` 이상이 보이면 됩니다. 없다면 [python.org](https://www.python.org/downloads/)에서 설치합니다.
- **Windows**: 시작 메뉴에서 "PowerShell"을 열고 `py --version`을 입력합니다. 없다면 [python.org](https://www.python.org/downloads/)에서 설치하고, 설치 화면의 **"Add python.exe to PATH"** 체크를 켭니다.

## 2. 저장소 내려받기 (한 번)

두 방법 중 하나를 고릅니다.

**방법 A. ZIP으로 받기 (권장, 터미널 불필요)**

1. GitHub 페이지에서 초록색 `Code` 버튼 → `Download ZIP`.
2. 압축을 풀고 폴더 이름을 `취업준비` 같은 원하는 이름으로 바꿉니다.

**방법 B. git으로 받기**

```bash
git clone https://github.com/fmaPark/job-prep-kit.git 취업준비
cd 취업준비
rm -rf .git && git init      # 여기서부터는 내 기록
```

Windows PowerShell에서는 `rm -rf .git` 대신 `Remove-Item -Recurse -Force .git`을 씁니다. 터미널이 낯설다면 방법 A가 가장 덜 막힙니다.

> 어느 방법이든, 자기 자료를 넣은 뒤 GitHub에 올릴 거라면 **비공개(private) 저장소**로 만드세요.
> 이력서 · 자소서 · 회사별 전략이 들어갑니다. `me/assets/` 폴더는 처음부터 `.gitignore`에 걸려 있어 올라가지 않습니다. 그 대신 GitHub에 백업되지도 않으니 원본 파일은 따로 백업하세요.

### 비공개 저장소로 올리기 (선택)

**이 저장소를 Fork하지 마세요.** 공개 저장소의 fork는 비공개로 바꿀 수 없습니다. 둘 중 하나를 씁니다.

- **GitHub 웹에서**: 이 저장소 페이지의 `Use this template` → `Create a new repository` → 공개 범위를 **Private**으로 고릅니다. 만든 저장소를 내려받아 씁니다.
- **내려받은 폴더에서**: GitHub에서 빈 **Private** 저장소를 만든 뒤, 폴더 안에서 아래를 실행합니다. 주소는 만든 저장소의 것으로 바꿉니다.

  ```bash
  git add -A && git commit -m "init"
  git branch -M main
  git remote add origin https://github.com/<내 계정>/<저장소 이름>.git
  git push -u origin main
  ```

올리기 전에 GitHub 저장소 설정에서 공개 범위가 Private인지 한 번 더 확인하세요.

## 3. Obsidian으로 열기 (한 번)

1. Obsidian 실행 → 왼쪽 아래 보관함 아이콘 → **"보관함으로 폴더 열기(Open folder as vault)"**.
2. 2단계에서 만든 폴더를 선택합니다.
3. 왼쪽 파일 목록에서 `index.md`를 열면 전체 목차가 나옵니다.

보관함 이름은 폴더 이름과 같아집니다. 대시보드가 이 이름으로 문서를 열기 때문에, 나중에 폴더 이름을 바꾸면 대시보드도 다시 만들어야 합니다.

## 4. `me/` 채우기 (한 번 채우고, 계속 갱신)

여기가 이 구조의 심장입니다. 이게 비어 있으면 자소서 작성은 매번 기억을 짜내는 일이 됩니다.

### 샘플 보기와 지우기

처음 받은 폴더에는 가상의 사람 · 회사로 만든 샘플이 들어 있습니다. 경험 원자 4개(`me/experiences/_sample-*.md`)와 지원 건 5건(`applications/_sample-*/`)입니다.
대시보드를 한 번 만들어 보고, 경험 파일과 `strategy.md` 매핑표가 어떻게 채워지는지 참고하세요.

#### 샘플 지우기

자기 자료를 채우기 시작하면 샘플을 지웁니다. 파일 탐색기에서 이름이 `_sample`로 시작하는 파일 · 폴더를 지우거나, 폴더 안에서 아래를 실행합니다.

```bash
rm -rf applications/_sample-* me/experiences/_sample-*
```

Windows PowerShell에서는 `Remove-Item -Recurse -Force applications/_sample-*, me/experiences/_sample-*`. 지운 뒤 대시보드를 다시 만듭니다.

### 처음 30분

전부 채우려 하지 말고, 첫 공고를 판단할 수 있을 만큼만 채웁니다.

| 시간 | 파일 | 무엇을 쓰나 |
|---|---|---|
| 10분 | `me/profile.md` | 기본 정보, 학력 · 경력, 그리고 「지원서 기재 표준」(학교 · 회사 · 기간을 어떤 표기로 쓸지) |
| 15분 | `me/experiences/` | `_template.md`를 복사해 경험 2~3개를 **사건 단위로**. 파일명은 `YYYY-키워드.md` |
| 5분 | `me/target-criteria.md` | 하드 필터(포기 못 하는 조건) 3개. 판단표 가중치는 나중에 다듬어도 됩니다 |

`target-criteria.md`의 하드 필터가 비어 있으면 [플레이북](/playbook.md) 「2.5 공고 스크리닝」을 돌릴 수 없습니다.
AI와 함께 채우려면 [AI와 함께 쓰기](/docs/ai-guide.md) 「자주 쓰는 요청 문장」의 첫 두 문장을 쓰세요.

### 그다음 (경험이 쌓이면)

| 파일 | 무엇을 쓰나 |
|---|---|
| `me/skills.md` | 역량마다 그것을 증명하는 경험 링크. 증명할 경험이 없는 역량은 적지 않습니다 |
| `me/narrative.md` | 경험들을 관통하는 한 문장. 모든 자소서의 뼈대. 이직 · 공백 사유 표준 답변도 여기 |
| `me/portfolio.md` | 프로젝트별 문제 → 결정 → 결과 → 내가 한 것 |

### 경험 파일에서 꼭 채울 것

- 프론트매터의 `title`, `description`, `tags`는 대시보드 카드에 그대로 보입니다. Obsidian의 속성(Properties) 편집 화면에서 고쳐도 됩니다.
- `scale`의 `weight`(주업무 / 부분업무 / 단발 / 활동 / 학업)와 본문 「본인 판단」 절은 비워 두지 마세요. AI가 자소서 소재를 고를 때 가장 먼저 보는 곳입니다([자소서 작성 규칙](/library/cover-letter-rules.md) A-1). 「본인 판단」에는 본인이 정한 평가만 적습니다.

## 5. 회사 추가하기 (지원 건마다 반복)

폴더를 만들기 전에 **지원할지부터 판단**합니다. 공고 원문과 `me/target-criteria.md`로 하드 필터 → 근거 매핑 → 판단표를 채우는 절차가 [플레이북](/playbook.md) 「2.5 공고 스크리닝」에 있습니다. 지원하지 않기로 한 공고는 폴더를 만들지 않습니다.

1. `applications/_template/` 폴더를 **통째로 복사**합니다.
2. 이름을 `applications/2026-09-회사명-직무/` 형식으로 바꿉니다.
3. `meta.md`부터 채웁니다. `company`, `role`, `track`, `stage`, `deadline`(YYYY-MM-DD)이 대시보드 표에 들어갑니다. `track`은 직군을 자유롭게 적고, 2차 면접 같은 세부 단계는 `stage_note`에 적습니다. 칸 설명은 `meta.md` 아래 메모에 있습니다.
4. 그다음 순서는 폴더 안 `index.md`에 적혀 있습니다. 핵심은 **`strategy.md`의 매핑표를 자소서보다 먼저 채우는 것**입니다. 자소서 밖의 칸(경력 · 프로젝트 · 자격 등)은 `application-form.md`에, 그 기준은 `me/profile.md` 「지원서 기재 표준」에 둡니다.
5. 경력기술서 · 설명회 정리 · 면접관별 질문 · 면접 복기가 필요하면 폴더 안 `optional/`에서 쓸 것만 회사 폴더로 옮기고 나머지는 지웁니다.
6. 상황이 바뀌면 `meta.md`를 고칩니다. 제출하면 `applied_at`, 다음 전형이 잡히면 `next_event` · `next_event_at`, 결과가 나오면 `passed` · `exit_stage` · `result_at`. 지원하지 않기로 했다면 `stage: 지원안함`과 `reason` · `result_at`.

## 6. 대시보드 만들기 (문서를 고칠 때마다)

폴더 안에서 터미널을 열고 실행합니다.

- **macOS**: Finder에서 폴더를 우클릭 → "폴더에서 새로운 터미널 열기" (없으면 터미널에서 `cd ` 뒤에 폴더를 끌어다 놓고 Enter)
- **Windows**: 폴더 안에서 Shift + 우클릭 → "여기에 PowerShell 창 열기"

```bash
python3 build-dashboard.py
```

Windows에서는 `python3` 대신 `py build-dashboard.py` 또는 `python build-dashboard.py`.

`dashboard.html`이 생기면 더블클릭해서 브라우저로 엽니다. `applications/index.md`의 파이프라인 · 일정 · 결과 표도 함께 갱신됩니다.
대시보드는 만든 시점의 스냅샷입니다. 문서를 고친 뒤에는 다시 실행하세요.
옵션과 문제 해결은 [대시보드 문서](/docs/dashboard.md)에 있습니다.

## 7. 반복 루프

| 시점 | 하는 일 | 남기는 곳 |
|---|---|---|
| 매주 | 파이프라인 상태 갱신, 마감 확인 | 각 회사 폴더의 `meta.md` → 대시보드 재생성 |
| 자소서 초안 후 | AI에게 반박 받기 → 수정 | `cover-letter.md`, 이전 버전은 `drafts/` |
| 면접 후 | 실제로 받은 질문 기록 | `library/question-bank.md` |
| 필기·과제 후 | 틀린 유형 · 막힌 지점 복기 | `library/assessments/review-log.md` |
| 결과 확인 후 | 회고 작성 → `me/`로 반영 | `library/retrospectives/` |

더 자세한 절차와 AI에게 던지는 요청 문장은 [플레이북](/playbook.md)에 있습니다.

문서를 새로 만들었다면 `python3 check-repo.py`로 프론트매터 `type`이 빠진 문서가 없는지 확인할 수 있습니다. 읽기만 하고 아무것도 고치지 않습니다.

## 8. Obsidian 없이 쓰기

마크다운 파일은 어떤 편집기로도 읽고 쓸 수 있습니다. 다만 아래가 달라집니다.

| 무엇 | Obsidian | VS Code 등 다른 편집기 |
|---|---|---|
| 대시보드의 "문서 열기" | 기본값으로 동작 | `python3 build-dashboard.py --links vscode`(VS Code) 또는 `--links file`로 다시 만듭니다 |
| `[역량](/me/skills.md)` 같은 절대경로 링크 | 열림 | GitHub 웹에서는 열리고, VS Code 미리보기에서는 열리지 않습니다 |
| `[[/me/experiences/…]]` 위키링크 | 열림 | 글자로만 보입니다. 파일 이름으로 찾아 엽니다 |
| 프론트매터 편집 | 속성(Properties) 화면 | 파일 맨 위 `---` 사이를 직접 고칩니다 |

자세한 내용은 [대시보드](/docs/dashboard.md) 「링크가 열리는 방식」과 [폴더 구조](/docs/structure.md) 「링크 규칙」에 있습니다.
