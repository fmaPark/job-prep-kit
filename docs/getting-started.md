---
type: Guide
title: 시작 가이드
description: 내려받기부터 첫 회사 폴더를 만들기까지. 터미널이 낯선 사람 기준으로 쓴 안내.
generated: { by: claude-code/claude-fable-5-1, at: 2026-09-08T00:30:00Z }
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

> 어느 방법이든, 자기 자료를 넣은 뒤 GitHub에 올릴 거라면 **비공개(private) 저장소**로 만드세요.
> 이력서 · 자소서 · 회사별 전략이 들어갑니다. `me/assets/` 폴더는 처음부터 `.gitignore`에 걸려 있어 올라가지 않습니다.

## 3. Obsidian으로 열기 (한 번)

1. Obsidian 실행 → 왼쪽 아래 보관함 아이콘 → **"보관함으로 폴더 열기(Open folder as vault)"**.
2. 2단계에서 만든 폴더를 선택합니다.
3. 왼쪽 파일 목록에서 `index.md`를 열면 전체 목차가 나옵니다.

보관함 이름은 폴더 이름과 같아집니다. 대시보드가 이 이름으로 문서를 열기 때문에, 나중에 폴더 이름을 바꾸면 대시보드도 다시 만들어야 합니다.

## 4. `me/` 채우기 (한 번 채우고, 계속 갱신)

여기가 이 구조의 심장입니다. 이게 비어 있으면 자소서 작성은 매번 기억을 짜내는 일이 됩니다.

| 순서 | 파일 | 무엇을 쓰나 |
|---|---|---|
| 1 | `me/profile.md` | 기본 정보, 학력 · 경력, 현재 상태 |
| 2 | `me/experiences/` | `_template.md`를 복사해 경험을 **사건 단위로** 하나씩. 파일명은 `YYYY-키워드.md` |
| 3 | `me/skills.md` | 역량마다 그것을 증명하는 경험 링크. 증명할 경험이 없는 역량은 적지 않습니다 |
| 4 | `me/narrative.md` | 경험들을 관통하는 한 문장. 모든 자소서의 뼈대 |
| 5 | `me/target-criteria.md` | 어떤 회사에 왜 가고 싶은지. 지원 여부 판단선 |
| 6 | `me/portfolio.md` | 프로젝트별 문제 → 결정 → 결과 → 내가 한 것 |

경험 파일 위쪽의 `---`로 감싼 부분(프론트매터)에서 `title`, `description`, `tags`는 대시보드 카드에 그대로 보입니다.
Obsidian의 속성(Properties) 편집 화면에서 고쳐도 됩니다.

## 5. 회사 추가하기 (지원 건마다 반복)

1. `applications/_template/` 폴더를 **통째로 복사**합니다.
2. 이름을 `applications/2026-09-회사명-직무/` 형식으로 바꿉니다.
3. `meta.md`부터 채웁니다. `company`, `role`, `track`, `stage`, `deadline`(YYYY-MM-DD)이 대시보드 표에 들어갑니다. `track`은 직군을 자유롭게 적고, 2차 면접 같은 세부 단계는 `stage_note`에 적습니다.
4. 그다음 순서는 폴더 안 `index.md`에 적혀 있습니다. 핵심은 **`strategy.md`의 매핑표를 자소서보다 먼저 채우는 것**입니다.

## 6. 대시보드 만들기 (문서를 고칠 때마다)

폴더 안에서 터미널을 열고 실행합니다.

- **macOS**: Finder에서 폴더를 우클릭 → "폴더에서 새로운 터미널 열기" (없으면 터미널에서 `cd ` 뒤에 폴더를 끌어다 놓고 Enter)
- **Windows**: 폴더 안에서 Shift + 우클릭 → "여기에 PowerShell 창 열기"

```bash
python3 build-dashboard.py
```

Windows에서는 `python3` 대신 `py build-dashboard.py` 또는 `python build-dashboard.py`.

`dashboard.html`이 생기면 더블클릭해서 브라우저로 엽니다.
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
