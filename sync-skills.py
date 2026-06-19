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
DIST = ROOT / "dist"
EXCLUDE_DIRS = {".git", "dist", "__pycache__"}


def discover_skills() -> list[Path]:
    skills = []
    for path in sorted(ROOT.iterdir()):
        if not path.is_dir() or path.name in EXCLUDE_DIRS or path.name.startswith("."):
            continue
        if (path / "SKILL.md").is_file():
            skills.append(path)
    if not skills:
        raise ValueError("No skill directories found")
    return skills


def split_skill(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    _prefix, raw, body = text.split("---", 2)
    return raw, body


def parse_frontmatter(raw: str) -> dict:
    if yaml:
        return yaml.safe_load(raw) or {}
    # Tiny YAML subset fallback: top-level key: value plus one-level metadata mapping.
    data: dict = {}
    current_map: dict | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = value.strip('"\'')
                current_map = None
            else:
                data[key] = {}
                current_map = data[key]
        elif current_map is not None and ":" in line:
            key, value = line.split(":", 1)
            current_map[key.strip()] = value.strip().strip('"\'')
    return data


def dump_frontmatter(data: dict) -> str:
    if yaml:
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key, sub_value in value.items():
                lines.append(f"  {sub_key}: {sub_value}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"


def validate(path: Path) -> dict:
    raw, _body = split_skill(path)
    data = parse_frontmatter(raw)
    for field in ("name", "description"):
        if not data.get(field):
            raise ValueError(f"{path}: missing {field}")
    if data["name"] != path.parent.name:
        raise ValueError(f"{path}: name {data['name']!r} must match directory {path.parent.name!r}")
    return data


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"))


def write_claude_skill(src: Path, dest: Path) -> None:
    copy_tree(src, dest)
    raw, body = split_skill(src / "SKILL.md")
    data = parse_frontmatter(raw)
    metadata = data.get("metadata") or {}
    description = metadata.get("claude-description") or data["description"]
    if len(description) > 200:
        raise ValueError(f"{src.name}: Claude description must be <= 200 characters")
    frontmatter = dump_frontmatter({"name": data["name"], "description": description})
    (dest / "SKILL.md").write_text(f"---\n{frontmatter}---{body}", encoding="utf-8")


def build() -> list[Path]:
    skills = discover_skills()
    for skill in skills:
        validate(skill / "SKILL.md")

    for subdir in ("codex", "claude", "claude-zips"):
        path = DIST / subdir
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    for skill in skills:
        copy_tree(skill, DIST / "codex" / skill.name)
        write_claude_skill(skill, DIST / "claude" / skill.name)
        zip_path = DIST / "claude-zips" / f"{skill.name}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted((DIST / "claude" / skill.name).rglob("*")):
                if path.is_file():
                    zf.write(path, arcname=Path(skill.name) / path.relative_to(DIST / "claude" / skill.name))
    return skills


def install(skills: list[Path]) -> None:
    home = Path.home()
    for skill in skills:
        copy_tree(DIST / "codex" / skill.name, home / ".codex" / "skills" / skill.name)
        copy_tree(DIST / "claude" / skill.name, home / ".claude" / "skills" / skill.name)


def main() -> int:
    skills = build()
    install(skills)
    print("built and installed " + ", ".join(skill.name for skill in skills))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
