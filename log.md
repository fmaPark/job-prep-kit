# 업데이트 로그

번들에 의미 있는 변경이 있을 때 한 줄씩 남긴다. 최신이 위.

## 2026-11-10

* **Consistency**: README · docs · 템플릿 정합성 점검 후 수정. 대시보드가 `stale_after` · `sources`를 읽는다는 잘못된 설명 정정, 지원 상태는 `meta.md` 한 곳에만 적도록 playbook · `applications/index.md` 통일, playbook 회사 추가 절차에 `meta.md` 추가, `me/` 채우는 순서 문구 통일, Windows용 clone 명령 추가, Cursor 등 도구별 안내 정정.
* **Dashboard**: `_template copy` · `_template 복사본` 같은 템플릿 사본을 지원 건과 경험에서 제외. 경험 참조는 파일 이름 전체가 맞을 때만 센다(`2024-협업`이 `2024-협업갈등`에 걸리지 않음).
* **Templates**: 위키링크를 `[[me/...]]` 형식으로(앞 `/` 제거), `research.md`의 고정된 `stale_after` 날짜를 비우고 안내 추가.
* **Docs**: 가상의 작성 예시 `docs/examples/` 추가(경험 원자 · 매핑표). 미완성 문서 수 의미와 `status: draft` 지우는 시점 안내.

## 2026-09-08

* **Docs**: README 점검 후 수정. 첫 문단을 문제·해법·독자 순으로 재구성(직군 무관 문구 이동), `library/` 항목 추가, 비공개 경고를 시작하기 앞으로, clone에 `.git` 분리 단계 추가, Obsidian 필요 조건 명확화, 한계·문의 섹션 신설. 대시보드 스크린샷을 5개 직군 샘플과 `stage_note`가 보이도록 재촬영(샘플 데이터는 저장소에 넣지 않음).
* **Generality**: 직군 중립화. `track` 자유값, 면접·질문은행·역량 라벨 일반화, 개인 상태 문구 제거. `library/coding-test/` → `library/assessments/`, 단계명 `코테·과제` → `필기·과제`(예전 이름 호환). 대시보드에 `stage_note` 표시와 미등록 단계 경고 추가.
* **Docs**: README를 비개발자 기준으로 간결하게 재구성. 폴더 구조·대시보드·AI 안내는 `docs/`로 분리. Obsidian 의존성을 명시.
* **Dashboard**: 프론트매터의 여러 줄 `tags` 목록(Obsidian 속성 편집기 형식) 파싱 추가. Windows 경로 링크 수정, 한글 NFD 정규화를 macOS에서만 적용.

## YYYY-MM-DD

* **Initialization**: job-prep-kit으로 번들 생성.
