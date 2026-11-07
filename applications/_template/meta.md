---
type: Application
title: <회사명> — <직무>
description: 이 지원 건의 상태 메타데이터. 대시보드가 이 파일을 읽는다.
company: <회사명>
role: <직무>
track:
stage: 관심
stage_note:
priority:
deadline:
applied_at:
next_event:
next_event_at:
next_action:
passed: []
skip: []
exit_stage:
result_at:
reason:
url:
status: draft
generated: { by: "<human|claude|codex>", at: "<ISO8601>" }
---

# 메모

(상태 관련 자유 메모. 표에 안 들어가는 맥락.)

> **이 파일이 현재 상태의 정본이다.** 바꾼 뒤 `python3 build-dashboard.py`를 돌리면 `dashboard.html`과 `applications/index.md`의 보드가 함께 갱신된다.
>
> - `stage`: 관심 / 서류작성 / 지원완료 / 필기·과제 / 면접 / 결과대기 / 합격 / 불합격 / 지원안함
> - `stage_note`: 세부 단계 자유 기입. 예: `2차 면접`, `인턴 전환 평가`, `처우 협의`. 대시보드에 단계 옆에 표시된다.
> - `track`: 자유롭게. 예: 개발 / PM / 디자인 / 마케팅 / 데이터 / 영업 / 사무
> - `priority`: 자유롭게. 예: `1순위`, `보험`. 보드에 단계 옆에 붙는다.
> - 날짜(`deadline` · `applied_at` · `next_event_at` · `result_at`): `YYYY-MM-DD` 또는 `YYYY-MM-DD HH:MM`.
> - 제출 전에는 `deadline`이, 제출 뒤에는 `next_event`(예: `1차 면접`) + `next_event_at`이 "다음 일정"으로 보인다.
> - `passed`: 통과한 전형. 예: `[서류, 코딩테스트]`. `skip`: 이 지원에 아예 없던 전형. 예: `[서류]`. 둘 다 결과 깔때기 집계에 쓰인다.
> - 불합격이면 `exit_stage`(어느 전형에서 끝났는지, 예: `서류` · `인적성` · `1차 면접`)와 `result_at`을 적는다.
> - 지원안함이면 `reason`(왜 지원하지 않기로 했는지)을 적는다. 다음에 같은 고민을 반복하지 않게 해 준다.
> - 칸이 빠졌거나 날짜를 읽지 못하면 빌드할 때 ⚠ 경고가 뜬다.
