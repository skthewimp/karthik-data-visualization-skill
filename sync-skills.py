#!/usr/bin/env python3
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


ROOT = Path(__file__).resolve().parent
SKILL = ROOT / "karthik-data-visualization"
DIST = ROOT / "dist"


def split_skill(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    _prefix, raw, body = text.split("---", 2)
    return raw, body


def validate(path: Path) -> dict:
    raw, _body = split_skill(path)
    data = yaml.safe_load(raw) if yaml else {}
    for field in ("name", "description"):
        if not data.get(field):
            raise ValueError(f"{path}: missing {field}")
    return data


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"))


def write_claude_skill(src: Path, dest: Path) -> None:
    copy_tree(src, dest)
    raw, body = split_skill(src / "SKILL.md")
    data = yaml.safe_load(raw) if yaml else {}
    metadata = data.get("metadata") or {}
    description = metadata.get("claude-description") or data["description"]
    if len(description) > 200:
        raise ValueError("Claude description must be <= 200 characters")
    frontmatter = yaml.safe_dump(
        {"name": data["name"], "description": description},
        sort_keys=False,
        allow_unicode=True,
    )
    (dest / "SKILL.md").write_text(f"---\n{frontmatter}---{body}", encoding="utf-8")


def build() -> None:
    validate(SKILL / "SKILL.md")
    for subdir in ("codex", "claude", "claude-zips"):
        path = DIST / subdir
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    copy_tree(SKILL, DIST / "codex" / SKILL.name)
    write_claude_skill(SKILL, DIST / "claude" / SKILL.name)

    zip_path = DIST / "claude-zips" / f"{SKILL.name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted((DIST / "claude" / SKILL.name).rglob("*")):
            if path.is_file():
                zf.write(path, arcname=Path(SKILL.name) / path.relative_to(DIST / "claude" / SKILL.name))


def install() -> None:
    home = Path.home()
    copy_tree(DIST / "codex" / SKILL.name, home / ".codex" / "skills" / SKILL.name)
    copy_tree(DIST / "claude" / SKILL.name, home / ".claude" / "skills" / SKILL.name)


def main() -> int:
    build()
    install()
    print(f"built and installed {SKILL.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
