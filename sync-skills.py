#!/usr/bin/env python3
from __future__ import annotations

import shutil
import argparse
import re
import subprocess
from pathlib import Path
from typing import Any

try:
    import yaml
    from yaml import YAMLError
except ImportError:
    yaml = None
    YAMLError = Exception


ROOT = Path(__file__).resolve().parent
EXCLUDE_DIRS = {".git", "dist", "__pycache__", "docs"}
SOURCE_SURFACES = ("codex", "claude")
DEFAULT_INSTALL_SURFACES = SOURCE_SURFACES
SCRIPT_REFERENCE_RE = re.compile(r"scripts/([A-Za-z0-9_.-]+\.(?:py|sh|js|R))")


def discover_skills() -> list[Path]:
    skills = []
    for path in sorted(ROOT.iterdir()):
        if not path.is_dir() or path.name in EXCLUDE_DIRS or path.name.startswith("."):
            continue
        if all((path / surface / "SKILL.md").is_file() for surface in SOURCE_SURFACES):
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
        try:
            data = yaml.safe_load(raw) or {}
        except YAMLError as exc:
            raise ValueError(f"{path}: invalid YAML frontmatter: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"{path}: YAML frontmatter must be a mapping")
        return data
    data = {}
    for line in raw.splitlines():
        if not line.strip() or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        if value.strip():
            data[key.strip()] = value.strip().strip("'\"")
    return data


def require_string(data: dict[str, Any], field: str, path: Path) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: missing {field}")
    return value.strip()


def validate(skills: list[Path]) -> None:
    for skill in skills:
        for surface in SOURCE_SURFACES:
            path = skill / surface / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            data = parse_frontmatter(path)
            name = require_string(data, "name", path)
            description = require_string(data, "description", path)
            if name != skill.name:
                raise ValueError(f"{path}: name {name!r} must match directory {skill.name!r}")
            if surface == "claude" and len(description) > 200:
                raise ValueError(f"{path}: Claude description must be <= 200 characters")
            for filename in sorted(set(SCRIPT_REFERENCE_RE.findall(text))):
                runtime_path = skill / surface / "scripts" / filename
                if not runtime_path.is_file():
                    raise ValueError(f"{path}: referenced runtime file is missing: {runtime_path}")
                if (ROOT / ".git").exists():
                    ignored = subprocess.run(
                        ["git", "check-ignore", "--quiet", str(runtime_path)],
                        cwd=ROOT,
                        check=False,
                    )
                    if ignored.returncode == 0:
                        raise ValueError(f"{runtime_path}: referenced runtime file is ignored by git")


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"))


def install(skills: list[Path], surfaces: tuple[str, ...] = DEFAULT_INSTALL_SURFACES) -> None:
    home = Path.home()
    for skill in skills:
        if "codex" in surfaces:
            copy_tree(skill / "codex", home / ".codex" / "skills" / skill.name)
        if "claude" in surfaces:
            copy_tree(skill / "claude", home / ".claude" / "skills" / skill.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and install Karthik data-visualization skills.")
    parser.add_argument("--validate-only", action="store_true", help="validate skill metadata without installing")
    parser.add_argument(
        "--surface",
        choices=("all", "codex", "claude"),
        default="all",
        help="which surface to install after validation",
    )
    args = parser.parse_args()

    skills = discover_skills()
    validate(skills)
    if args.validate_only:
        print("validated " + ", ".join(skill.name for skill in skills))
        return 0

    surfaces = DEFAULT_INSTALL_SURFACES if args.surface == "all" else (args.surface,)
    install(skills, surfaces)
    print(f"installed {args.surface}: " + ", ".join(skill.name for skill in skills))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
