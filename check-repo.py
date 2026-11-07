#!/usr/bin/env python3
"""
번들 점검 (읽기 전용, Python 3.8 이상, 표준 라이브러리만)

    python3 check-repo.py

Git이 추적하는 파일과 ignore되지 않은 새 파일 중 .md를 읽어,
OKF 규칙대로 YAML 프론트매터에 `type`이 있는지 확인한다.
index.md · log.md · README.md는 예외다(OKF 예약 파일과 GitHub 첫 화면).

아무 파일도 고치지 않는다. 누락 목록과 개수를 출력하고, 누락이 있으면 종료 코드 1.
최상위 `type:` 줄이 있는지만 보는 간단한 검사이며 YAML 전체 문법을 검증하지는 않는다.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXEMPT = {"index.md", "log.md", "README.md"}
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.S)
TYPE_LINE = re.compile(r"^type:\s*[^\s#]+", re.M)


def markdown_files():
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT)
        names = [n for n in out.decode("utf-8").split("\0") if n]
        return [ROOT / n for n in sorted(set(names)) if n.endswith(".md")]
    except (OSError, subprocess.CalledProcessError):
        # Git 저장소가 아니면(압축 파일로 받은 경우) 폴더를 직접 훑는다.
        skip = {".git", ".obsidian", ".agent-work", ".agent-notes", "node_modules"}
        return sorted(p for p in ROOT.rglob("*.md")
                      if not skip.intersection(p.relative_to(ROOT).parts))


def main():
    missing = []
    for path in markdown_files():
        if path.name in EXEMPT or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            missing.append((path, "읽을 수 없음"))
            continue
        m = FRONTMATTER.match(text)
        if not m:
            missing.append((path, "프론트매터 없음"))
        elif not TYPE_LINE.search(m.group(1)):
            missing.append((path, "type 없음"))
    for path, why in missing:
        print(f"⚠ {path.relative_to(ROOT).as_posix()}: {why}")
    print(f"type 누락 {len(missing)}건")
    return 1 if missing else 0


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        sys.exit("Python 3.8 이상이 필요합니다.")
    sys.exit(main())
