# 업데이트 로그

번들에 의미 있는 변경이 있을 때 한 줄씩 남긴다. 최신이 위.

## 2026-11-10

* **Docs**: `docs/scope.md`(이 저장소가 하지 않는 것) 신설 — 12개 항목의 경계와 사용자가 할 일 · 확장 지점. README에 4줄 요약 절과 링크, `docs/index.md` · `docs/structure.md`에 연결. README 「한계」에서 제출 관련 줄은 새 절로 옮김.

## 2026-11-09

* **Docs**: README 온보딩 보강 — 첫 30분 순서(`target-criteria.md` 포함), 지원 건 하나의 흐름표, 스크리닝 먼저, Fork 금지 · 비공개 저장소 안내, 첫 실행 빈 화면 안내, AI 첫 요청 3개. `docs/`에 대시보드가 읽는 필드 정정, 지원안함 결정일(`result_at`), Obsidian 없이 쓰기, 대화 간 이어 가기, 작성 규칙 문서 안내. playbook에 `me/` 채우기 요청 문장. `check-repo.py`는 Git 저장소가 아닐 때 git 오류를 숨기고, `build-dashboard.py`는 `-h`/`--help`에 사용법만 출력.

## 2026-11-07

* **Library**: 자소서 작성 규칙(`cover-letter-rules.md`)과 포트폴리오 작성 규칙(`portfolio-rules.md`) 신설 — 소재 선택, 골격, 문장 규칙, AI 작성 티 차단, 자체 검증, 연결 검증과 작업 순서, 초안 200% 규칙. 질문 은행에 자소서 문항 유형별 공략법, 회고 색인에 누적 패턴 절. CLAUDE.md·playbook에서 두 규칙 문서를 읽도록 연결.
* **Rules**: `playbook.md`에 공고 스크리닝 절차(§2.5), 지원서 칸·제출 전 점검, 디깅과 작성 분리, 작성·피드백 원칙, 대화 간 이어 가기(§6~8). `CLAUDE.md`에 현재 요청 우선, 판단·수정 권한, 상태와 대시보드, `updated` 메타데이터 관례, 빼라고 한 내용 금지. `me/target-criteria.md`에 하드 필터·역질문·100점 판단표·판정선·미확인 항목 처리·개별 예외(값은 예시).
* **Dashboard**: 빌더가 `applications/index.md`의 AUTO 블록(파이프라인 · 이번 주 일정 · 지원안함 · 누적 결과)을 다시 쓴다. `meta.md`에 `priority`·`applied_at`·`next_event`·`next_event_at`·`passed`·`skip`·`exit_stage`·`result_at`·`reason` 추가, 종료 단계 `지원안함` 추가, 결과 깔때기와 칸 누락 경고. 기존 단계명과 `stage_note`, OS별 한글 정규화, Windows 링크, 여러 줄 목록 파싱은 유지. 다른 표기(`서류제출` 등)는 경고 없이 읽는다.
* **me/**: 구조 보강. `profile.md`에 경력 기간 산정·지원서 기재 표준·정정 이력, `narrative.md`에 축의 위험·이직·공백 사유 표준 답변, `skills.md`에 성과 수치와 산출 방법, 경험 원자 템플릿에 `scale`·본인 판단·정의·기여 경계·한계 절, `experiences/index.md`에 사건 크기 순 목록과 사실 충돌 예시, `portfolio.md`에 공개 범위.
* **Templates**: 지원 건 템플릿 보강. `application-form.md`(지원서 칸·제출 확정값·우대사항 대조) 추가, `strategy.md`에 근거 등급·사건×칸 배치표·짝 검증 칸, `interview.md`를 대본 형식(〔확정〕/〔AI 초안〕 라벨, 말하는 시간)으로 재구성, 선택 문서 `optional/`(경력기술서·설명회 정리·면접관별 질문·면접 복기) 신설. 템플릿의 `generated`를 고정값에서 플레이스홀더로.

## 2026-09-08

* **Docs**: README 점검 후 수정. 첫 문단을 문제·해법·독자 순으로 재구성(직군 무관 문구 이동), `library/` 항목 추가, 비공개 경고를 시작하기 앞으로, clone에 `.git` 분리 단계 추가, Obsidian 필요 조건 명확화, 한계·문의 섹션 신설. 대시보드 스크린샷을 5개 직군 샘플과 `stage_note`가 보이도록 재촬영(샘플 데이터는 저장소에 넣지 않음).
* **Generality**: 직군 중립화. `track` 자유값, 면접·질문은행·역량 라벨 일반화, 개인 상태 문구 제거. `library/coding-test/` → `library/assessments/`, 단계명 `코테·과제` → `필기·과제`(예전 이름 호환). 대시보드에 `stage_note` 표시와 미등록 단계 경고 추가.
* **Docs**: README를 비개발자 기준으로 간결하게 재구성. 폴더 구조·대시보드·AI 안내는 `docs/`로 분리. Obsidian 의존성을 명시.
* **Dashboard**: 프론트매터의 여러 줄 `tags` 목록(Obsidian 속성 편집기 형식) 파싱 추가. Windows 경로 링크 수정, 한글 NFD 정규화를 macOS에서만 적용.

## YYYY-MM-DD

* **Initialization**: job-prep-kit으로 번들 생성.
