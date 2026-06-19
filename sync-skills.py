#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


ROOT = Path(__file__).resolve().parent
EXCLUDE_DIRS = {".git", "dist", "__pycache__", "docs"}
SURFACES = ("codex", "claude")


def discover_skills() -> list[Path]:
    skills = []
    for path in sorted(ROOT.iterdir()):
        if not path.is_dir() or path.name in EXCLUDE_DIRS or path.name.startswith("."):
            continue
        if all((path / surface / "SKILL.md").is_file() for surface in SURFACES):
            skills.append(path)
    if not skills:
        raise ValueError("No skill directories found; expected <skill>/{codex,claude}/SKILL.md")
    return skills


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    _prefix, raw, _body = text.split("---", 2)
    if yaml:
        return yaml.safe_load(raw) or {}
    data = {}
    for line in raw.splitlines():
        if not line.strip() or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        if value.strip():
            data[key.strip()] = value.strip().strip("'\"")
    return data


def validate(skills: list[Path]) -> None:
    for skill in skills:
        for surface in SURFACES:
            path = skill / surface / "SKILL.md"
            data = parse_frontmatter(path)
            for field in ("name", "description"):
                if not data.get(field):
                    raise ValueError(f"{path}: missing {field}")
            if data["name"] != skill.name:
                raise ValueError(f"{path}: name {data['name']!r} must match directory {skill.name!r}")
            if surface == "claude" and len(str(data["description"])) > 200:
                raise ValueError(f"{path}: Claude description must be <= 200 characters")


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"))


def install(skills: list[Path]) -> None:
    home = Path.home()
    for skill in skills:
        copy_tree(skill / "codex", home / ".codex" / "skills" / skill.name)
        copy_tree(skill / "claude", home / ".claude" / "skills" / skill.name)


def main() -> int:
    skills = discover_skills()
    validate(skills)
    install(skills)
    print("installed " + ", ".join(skill.name for skill in skills))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
