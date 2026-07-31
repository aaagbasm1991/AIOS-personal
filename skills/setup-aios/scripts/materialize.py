#!/usr/bin/env python3
"""Deterministic AIOS release-template materializer.

Turns the tracked release assets under ``assets/templates/`` into a first-install
product tree, applying the fixed mappings:

    assets/templates/common/private.example/    -> <dest>/private/
    assets/templates/<edition>/private.example/  -> <dest>/private/
    assets/templates/common/.aios/local.example.md -> <dest>/.aios/local.md
    *.template                                   -> * (rendered {{AIOS_*}})

Rules:
  * Apply common first, then the chosen edition (overlay).
  * create-if-missing: never overwrite an existing target.
  * Never overwrite existing ``private/`` or ``.aios/local.md`` (including --upgrade).
  * Strip ``.template`` and render every ``{{AIOS_*}}`` placeholder.
  * --upgrade: never overwrite AGENTS.md / CLAUDE.md / private / local; when an
    entry template differs, write ``<entry>.proposed.md`` and an upgrade report.
  * Repeated runs are idempotent.

Standard library only. This is the materializer CLI; the black-box smoke test
lives in a separate CLI (smoke_test.py) and drives this one as a subprocess.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_ROOT = SCRIPT_DIR.parent / "assets" / "templates"

PLACEHOLDER_RE = re.compile(r"\{\{(AIOS_[A-Z0-9_]+)\}\}")
METADATA_FILES = {Path(".aios/version.md"), Path(".aios/manifest.md")}

COMMON_DIRS = (
    "skills",
    "knowledge/sources",
    "knowledge/wiki",
    "knowledge/outputs",
    "knowledge/assets",
    "shared/rules",
    "shared/templates",
    "shared/assets",
    "private/assets",
    "workspace/inbox",
    "workspace/drafts",
    "workspace/projects",
    "workspace/references",
    "workspace/handoff",
    "workspace/archive",
)
EDITION_DIRS = {
    "personal": ("workspace/learning", "workspace/life-admin"),
    "company": (
        "workspace/meetings",
        "workspace/drafts/specs",
        "workspace/drafts/ui-strings",
        "workspace/drafts/weekly-reports",
    ),
}


def render(text: str, variables: dict[str, str]) -> str:
    """Replace every {{AIOS_*}} token; unknown tokens become an empty string."""
    return PLACEHOLDER_RE.sub(lambda m: variables.get(m.group(1), ""), text)


def transform_relpath(rel: Path) -> Path:
    """Map a template-relative path to its materialized destination path."""
    parts = ["private" if p == "private.example" else p for p in rel.parts]
    name = parts[-1]
    if name == "local.example.md":
        name = "local.md"
    if name.endswith(".template"):
        name = name[: -len(".template")]
    parts[-1] = name
    return Path(*parts)


def is_protected(dest_rel: Path) -> bool:
    """private/ tree and .aios/local.md are user-owned; never overwrite."""
    parts = dest_rel.parts
    if parts and parts[0] == "private":
        return True
    if dest_rel.as_posix() == ".aios/local.md":
        return True
    return False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_if_changed(path: Path, content: str) -> bool:
    """Write UTF-8 text only when bytes differ; return whether a write occurred."""
    if path.exists() and read_text(path) == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if is_junction and is_junction():
        return True
    if os.name == "nt":
        try:
            attributes = getattr(path.lstat(), "st_file_attributes", 0)
        except OSError:
            return False
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        return bool(attributes & reparse_flag)
    return False


def first_absolute_link_component(path: Path) -> Path | None:
    """Return an existing link/reparse component in an absolute path."""
    absolute = path.absolute()
    current = Path(absolute.anchor)
    if is_link_or_junction(current):
        return current
    for part in absolute.parts[1:]:
        current = current / part
        if is_link_or_junction(current):
            return current
        if not current.exists():
            break
    return None


def first_link_component(root: Path, target: Path) -> Path | None:
    """Return the first existing link/junction from root to target, if any."""
    relative = target.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if is_link_or_junction(current):
            return current
        if not current.exists():
            break
    return None


def safe_mkdir(root: Path, target: Path) -> bool:
    """Create a directory without traversing an existing link or Junction."""
    if first_link_component(root, target) is not None:
        return False
    target.mkdir(parents=True, exist_ok=True)
    return True


def iter_template_files(edition: str):
    """Yield (source_path, tree_relative_path) for common then edition trees."""
    for tree_name in ("common", edition):
        tree = TEMPLATE_ROOT / tree_name
        if not tree.is_dir():
            continue
        for src in sorted(tree.rglob("*")):
            if src.is_file():
                yield src, src.relative_to(tree)


def build_template_plan(edition: str) -> list[tuple[Path, Path]]:
    """Return one source per destination; the edition overlay wins collisions."""
    plan: dict[Path, Path] = {}
    for src, rel in iter_template_files(edition):
        plan[transform_relpath(rel)] = src
    return sorted(plan.items(), key=lambda item: item[0].as_posix())


def version_from_text(content: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("- version:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def upsert_manifest_field(content: str, key: str, value: str) -> str:
    """Update or insert one ``- key: value`` field before manifest sections."""
    replacement = f"- {key}: {value}"
    lines = content.splitlines()
    pattern = re.compile(rf"^\s*-\s*{re.escape(key)}\s*:")
    for index, line in enumerate(lines):
        if pattern.match(line):
            lines[index] = replacement
            return "\n".join(lines).rstrip() + "\n"
    insert_at = next(
        (index for index, line in enumerate(lines) if line.startswith("## ")),
        len(lines),
    )
    while insert_at > 0 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, replacement)
    return "\n".join(lines).rstrip() + "\n"


def _entry_kind(entry: Path, skills: Path) -> str:
    if not entry.exists() and not entry.is_symlink():
        return "missing"
    try:
        if entry.resolve() == skills.resolve():
            return "link"
    except OSError:
        return "conflict"
    if entry.is_dir() and not entry.is_symlink():
        return "copy"
    return "conflict"


def _existing_link_type(entries: tuple[Path, Path]) -> str:
    if all(entry.is_symlink() for entry in entries):
        return "relative-symlink"
    is_junction = [
        bool(getattr(entry, "is_junction", lambda: False)())
        for entry in entries
    ]
    if all(is_junction):
        return "junction"
    return "mixed-link"


def _create_link(entry: Path, skills: Path) -> str:
    entry.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink("../skills", entry, target_is_directory=True)
        return "relative-symlink"
    except OSError:
        if os.name != "nt":
            raise
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(entry), str(skills.resolve())],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise OSError(completed.stderr.strip() or completed.stdout.strip())
    return "junction"


def _remove_created_link(entry: Path, link_type: str) -> None:
    if link_type == "relative-symlink":
        entry.unlink()
    elif link_type == "junction":
        os.rmdir(entry)


def _create_copy(entry: Path, skills: Path) -> None:
    entry.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skills, entry)


def tree_signature(root: Path) -> str:
    """Hash a physical directory tree and reject nested links/Junctions."""
    digest = hashlib.sha256()
    for current, dirnames, filenames in os.walk(
        root, topdown=True, followlinks=False
    ):
        current_path = Path(current)
        dirnames.sort()
        filenames.sort()
        for name in dirnames:
            child = current_path / name
            if is_link_or_junction(child):
                raise RuntimeError(
                    f"Skill tree contains Symlink or Junction "
                    f"{child.relative_to(root).as_posix()}; setup did not "
                    "copy or publish linked content."
                )
            digest.update(
                b"D\0"
                + child.relative_to(root).as_posix().encode("utf-8")
                + b"\0"
            )
        for name in filenames:
            child = current_path / name
            if is_link_or_junction(child):
                raise RuntimeError(
                    f"Skill tree contains Symlink or Junction "
                    f"{child.relative_to(root).as_posix()}; setup did not "
                    "copy or publish linked content."
                )
            digest.update(
                b"F\0"
                + child.relative_to(root).as_posix().encode("utf-8")
                + b"\0"
            )
            file_digest = hashlib.sha256()
            with child.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    file_digest.update(chunk)
            digest.update(file_digest.digest())
    return digest.hexdigest()


def ensure_skill_entries(
    dest: Path, requested_mode: str, prior_copy_signature: str | None
) -> tuple[str, str, str]:
    """Create or finalize both platform Skill entries without replacing
    user-diverged content.

    In copy mode, an existing platform copy is only ever re-synced to the
    current root ``skills/`` tree when its own signature still matches the
    signature that was recorded (in the manifest) the last time it was
    generated — i.e. it is proven to be an untouched generated copy that
    merely predates newer root content (the empty-skeleton-then-install-Skill
    sequence). Anything else about an existing copy is treated as a
    user-owned divergence and is preserved, never overwritten.

    Returns (effective_mode, link_type, current_root_skills_signature).
    """
    skills = dest / "skills"
    entries = (dest / ".agents" / "skills", dest / ".claude" / "skills")
    if first_link_component(dest, skills) is not None:
        raise RuntimeError(
            "Existing <aios-root>/skills is a Symlink or Junction; setup "
            "preserved it and did not create platform entries."
        )
    for entry in entries:
        linked_parent = first_link_component(dest, entry.parent)
        if linked_parent is not None:
            raise RuntimeError(
                f"Existing parent {linked_parent} is a Symlink or Junction; "
                "setup did not write through it."
            )
    kinds = [_entry_kind(entry, skills) for entry in entries]
    source_signature = tree_signature(skills)

    if "conflict" in kinds or ("link" in kinds and "copy" in kinds):
        raise RuntimeError(
            "Existing .agents/.claude Skill entries do not resolve to one "
            "consistent <aios-root>/skills source; no entry was replaced."
        )

    resync: list[Path] = []
    for entry, kind in zip(entries, kinds):
        if kind != "copy":
            continue
        entry_signature = tree_signature(entry)
        if entry_signature == source_signature:
            continue
        if prior_copy_signature and entry_signature == prior_copy_signature:
            # Unchanged since it was generated; root skills/ gained or
            # changed content since then (e.g. a Skill was installed after
            # an empty-skeleton materialize) — safe to regenerate.
            resync.append(entry)
            continue
        raise RuntimeError(
            f"Existing copy-mode Skill entry "
            f"{entry.relative_to(dest).as_posix()} differs from root "
            "skills; setup preserved both and stopped for manual sync."
        )
    for entry in resync:
        shutil.rmtree(entry)
        _create_copy(entry, skills)

    if all(kind == "link" for kind in kinds):
        return "link", _existing_link_type(entries), source_signature
    if all(kind == "copy" for kind in kinds):
        return "copy", "copy", source_signature

    existing_mode = next((kind for kind in kinds if kind != "missing"), None)
    mode = existing_mode or requested_mode
    if mode == "copy":
        for entry, kind in zip(entries, kinds):
            if kind == "missing":
                _create_copy(entry, skills)
        return "copy", "copy", source_signature

    created: list[tuple[Path, str]] = []
    try:
        for entry, kind in zip(entries, kinds):
            if kind == "missing":
                link_type = _create_link(entry, skills)
                created.append((entry, link_type))
        return "link", _existing_link_type(entries), source_signature
    except OSError:
        for entry, link_type in reversed(created):
            _remove_created_link(entry, link_type)
        if existing_mode == "link":
            raise RuntimeError(
                "Could not create the missing Skill link while preserving an "
                "existing link; no fallback replacement was attempted."
            )
        for entry, kind in zip(entries, kinds):
            if kind == "missing":
                _create_copy(entry, skills)
        return "copy", "fallback-copy", source_signature


def find_proposal_conflicts(
    dest: Path,
    template_plan: list[tuple[Path, Path]],
    variables: dict[str, str],
) -> list[Path]:
    """Read-only preflight: find existing ``<entry>.proposed.md`` files whose
    bytes differ from the freshly generated candidate (for example a
    user-reviewed or edited proposal). Performs no writes."""
    conflicts: list[Path] = []
    for dest_rel, src in template_plan:
        if dest_rel in METADATA_FILES or is_protected(dest_rel):
            continue
        target = dest / dest_rel
        if not target.exists():
            continue
        content = render(read_text(src), variables)
        if read_text(target) == content:
            continue
        proposed = target.with_name(target.name + ".proposed.md")
        if proposed.exists() and read_text(proposed) != content:
            conflicts.append(dest_rel)
    return conflicts


def materialize(edition: str, dest: Path, variables: dict[str, str],
                upgrade: bool, skills_mode: str) -> dict:
    dest = dest.absolute()
    linked_root = first_absolute_link_component(dest)
    if linked_root is not None:
        raise RuntimeError(
            f"Destination path crosses Symlink, Junction, or reparse point "
            f"{linked_root}; setup preserved it and requires a physical "
            "AIOS root path."
        )
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    for managed_path in (
        dest / ".aios",
        dest / ".agents",
        dest / ".claude",
        dest / "skills",
    ):
        if managed_path.exists() and not managed_path.is_dir():
            raise RuntimeError(
                f"Managed path {managed_path.relative_to(dest).as_posix()} "
                "exists but is not a directory; setup preserved it and stopped."
            )
        linked_component = first_link_component(dest, managed_path)
        if linked_component is not None:
            raise RuntimeError(
                f"Managed path {linked_component.relative_to(dest)} is a "
                "Symlink or Junction; setup preserved it and stopped."
            )
    managed_files = [
        dest / ".aios" / "version.md",
        dest / ".aios" / "manifest.md",
    ]
    if upgrade:
        managed_files.append(dest / ".aios" / "upgrade-report.md")
    for managed_file in managed_files:
        linked_component = first_link_component(dest, managed_file)
        if linked_component is not None:
            raise RuntimeError(
                f"Managed file {managed_file.relative_to(dest).as_posix()} "
                "crosses existing Symlink or Junction "
                f"{linked_component.relative_to(dest).as_posix()}; "
                "setup preserved it and stopped."
            )
    variables = dict(variables)
    variables["AIOS_EDITION"] = edition
    template_plan = build_template_plan(edition)
    for dest_rel, _ in template_plan:
        if dest_rel in METADATA_FILES or is_protected(dest_rel):
            continue
        target = dest / dest_rel
        linked_component = first_link_component(dest, target)
        if linked_component is not None:
            raise RuntimeError(
                f"Public target {dest_rel.as_posix()} crosses existing "
                f"Symlink or Junction "
                f"{linked_component.relative_to(dest).as_posix()}; "
                "setup preserved it and stopped."
            )
    for rel in (*COMMON_DIRS, *EDITION_DIRS[edition]):
        rel_path = Path(rel)
        if is_protected(rel_path):
            continue
        directory = dest / rel_path
        linked_component = first_link_component(dest, directory)
        if linked_component is not None:
            raise RuntimeError(
                f"Public directory {rel_path.as_posix()} crosses existing "
                f"Symlink or Junction "
                f"{linked_component.relative_to(dest).as_posix()}; "
                "setup did not materialize any release content."
            )
    skills_path = dest / "skills"
    if skills_path.is_dir():
        tree_signature(skills_path)

    prior_manifest = dest / ".aios" / "manifest.md"
    edition_path = dest / ".aios" / "edition.md"
    installed_editions = {
        value
        for value in (
            read_manifest_field(prior_manifest, "edition"),
            read_manifest_field(edition_path, "edition"),
        )
        if value
    }
    if installed_editions and installed_editions != {edition}:
        found = ", ".join(sorted(installed_editions))
        raise RuntimeError(
            f"Existing install edition is {found}; requested {edition}. "
            "Setup does not mix personal and company editions in one root."
        )
    version_path = dest / ".aios" / "version.md"
    source_version = read_version(version_path)
    if source_version == "unknown":
        source_version = (
            read_manifest_field(prior_manifest, "version") or "unknown"
        )
    version_template = TEMPLATE_ROOT / "common" / ".aios" / "version.md.template"
    version_template_text = read_text(version_template)
    target_version = version_from_text(version_template_text)
    prior_upgrade_from = read_manifest_field(prior_manifest, "upgrade_from")
    prior_upgrade_to = read_manifest_field(prior_manifest, "upgrade_to")
    repeated_same_upgrade = (
        upgrade
        and source_version == target_version
        and prior_upgrade_to == target_version
    )
    upgrade_from = (
        prior_upgrade_from
        if repeated_same_upgrade and prior_upgrade_from
        else source_version
    )
    if "AIOS_DATE" not in variables:
        preserved_date = (
            read_manifest_field(version_path, "updated")
            if repeated_same_upgrade
            else ""
        )
        variables["AIOS_DATE"] = (
            preserved_date or datetime.date.today().isoformat()
        )
    version_content = render(version_template_text, variables)

    proposal_conflicts = find_proposal_conflicts(dest, template_plan, variables)
    if proposal_conflicts:
        names = ", ".join(
            f"{dest_rel.as_posix()}.proposed.md" for dest_rel in proposal_conflicts
        )
        raise RuntimeError(
            f"Existing proposed file(s) {names} differ from the freshly "
            "generated candidate (for example a user-reviewed or edited "
            "proposal); setup preserved them byte-for-byte and stopped "
            "before writing any other release changes. Resolve or remove "
            "the *.proposed.md file(s) and rerun."
        )

    result = {
        "created": [],
        "updated": [],
        "skipped": [],
        "proposed": [],
        "preserved": [],
        "missing_variables": set(),
    }

    for dest_rel, src in template_plan:
        if dest_rel in METADATA_FILES:
            continue
        target = dest / dest_rel
        linked_component = first_link_component(dest, target)
        if linked_component is not None:
            if is_protected(dest_rel):
                result["preserved"].append(
                    f"{dest_rel.as_posix()} (link boundary: "
                    f"{linked_component.relative_to(dest).as_posix()})"
                )
                continue
            raise RuntimeError(
                f"Public target {dest_rel.as_posix()} crosses existing "
                f"Symlink or Junction "
                f"{linked_component.relative_to(dest).as_posix()}; "
                "setup preserved it and stopped."
            )
        source_text = read_text(src)
        result["missing_variables"].update(
            token for token in PLACEHOLDER_RE.findall(source_text)
            if token not in variables
        )
        content = render(source_text, variables)

        if target.exists():
            if read_text(target) == content:
                result["skipped"].append(dest_rel.as_posix())
            elif is_protected(dest_rel):
                result["preserved"].append(dest_rel.as_posix())
            else:
                proposed = target.with_name(target.name + ".proposed.md")
                proposed_link = first_link_component(dest, proposed)
                if proposed_link is not None:
                    raise RuntimeError(
                        f"Proposed target {proposed.relative_to(dest).as_posix()} "
                        "crosses existing Symlink or Junction "
                        f"{proposed_link.relative_to(dest).as_posix()}; "
                        "setup preserved it and stopped."
                    )
                write_if_changed(proposed, content)
                result["proposed"].append(dest_rel.as_posix())
            continue

        write_if_changed(target, content)
        result["created"].append(dest_rel.as_posix())

    for rel in (*COMMON_DIRS, *EDITION_DIRS[edition]):
        directory = dest / rel
        if not safe_mkdir(dest, directory):
            result["preserved"].append(f"{rel} (link boundary)")

    prior_copy_signature = (
        read_manifest_field(prior_manifest, "skills_copy_signature") or None
    )
    effective_mode, link_type, current_skills_signature = ensure_skill_entries(
        dest, skills_mode, prior_copy_signature
    )
    prior_link_type = read_manifest_field(prior_manifest, "skills_link_type")
    if (
        effective_mode == "copy"
        and link_type == "copy"
        and prior_link_type == "fallback-copy"
    ):
        link_type = prior_link_type

    if not version_path.exists():
        write_if_changed(version_path, version_content)
        result["created"].append(".aios/version.md")
    elif upgrade and write_if_changed(version_path, version_content):
        result["updated"].append(".aios/version.md")
    else:
        result["skipped"].append(".aios/version.md")

    manifest_template = TEMPLATE_ROOT / "common" / ".aios" / "manifest.md.template"
    manifest_path = dest / ".aios" / "manifest.md"
    manifest_existed = manifest_path.exists()
    manifest_content = (
        read_text(manifest_path)
        if manifest_existed
        else render(read_text(manifest_template), variables)
    )
    manifest_content = upsert_manifest_field(
        manifest_content, "skills_mode", effective_mode
    )
    manifest_content = upsert_manifest_field(
        manifest_content, "skills_link_type", link_type
    )
    manifest_content = upsert_manifest_field(
        manifest_content,
        "skills_copy_signature",
        current_skills_signature if effective_mode == "copy" else "",
    )
    if not manifest_existed or upgrade:
        manifest_content = upsert_manifest_field(
            manifest_content, "edition", variables["AIOS_EDITION"]
        )
        manifest_content = upsert_manifest_field(
            manifest_content, "version", target_version
        )
        if upgrade:
            unapplied_items = [
                f"{path}.proposed.md" for path in result["proposed"]
            ]
            unapplied = ", ".join(unapplied_items) or "none"
            manifest_content = upsert_manifest_field(
                manifest_content, "upgrade_from", upgrade_from
            )
            manifest_content = upsert_manifest_field(
                manifest_content, "upgrade_to", target_version
            )
            manifest_content = upsert_manifest_field(
                manifest_content,
                "upgrade_status",
                "pending-review" if result["proposed"] else "complete",
            )
            manifest_content = upsert_manifest_field(
                manifest_content, "unapplied_differences", unapplied
            )
    changed = write_if_changed(manifest_path, manifest_content)
    if changed:
        bucket = "updated" if manifest_existed else "created"
        result[bucket].append(".aios/manifest.md")
    else:
        result["skipped"].append(".aios/manifest.md")

    if upgrade:
        write_upgrade_report(
            dest,
            upgrade_from,
            target_version,
            variables["AIOS_DATE"],
            result,
        )

    result["skills_mode"] = effective_mode
    result["skills_link_type"] = link_type
    return result


def read_version(version_path: Path) -> str:
    if not version_path.exists():
        return "unknown"
    for line in read_text(version_path).splitlines():
        line = line.strip()
        if line.startswith("- version:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def read_manifest_field(manifest_path: Path, key: str) -> str:
    if not manifest_path.exists():
        return ""
    pattern = re.compile(rf"^\s*-\s*{re.escape(key)}\s*:\s*(.*)$")
    for line in read_text(manifest_path).splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return ""


def write_upgrade_report(
    dest: Path,
    source_version: str,
    target_version: str,
    generated_date: str,
    result: dict,
) -> None:
    report = dest / ".aios" / "upgrade-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# AIOS Upgrade Report",
        "",
        f"- source_version: {source_version}",
        f"- target_version: {target_version}",
        f"- generated: {generated_date}",
        "",
        "## Proposed updates (not applied)",
        "",
    ]
    if result["proposed"]:
        for path in result["proposed"]:
            lines.append(f"- {path} → {path}.proposed.md（既有入口不同，保留原檔）")
    else:
        lines.append("- 無：既有入口與新版一致或不存在差異。")
    lines += [
        "",
        "## Preserved user-owned or linked paths",
        "",
    ]
    for path in result["preserved"] or ["- 無"]:
        lines.append(f"- {path}" if path != "- 無" else path)
    lines.append("")
    write_if_changed(report, "\n".join(lines) + "\n")


def parse_vars(pairs) -> dict[str, str]:
    variables: dict[str, str] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise SystemExit(f"--var expects KEY=VALUE, got: {pair}")
        key, value = pair.split("=", 1)
        variables[key.strip()] = value
    return variables


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Materialize an AIOS install from release templates.")
    parser.add_argument("--edition", required=True, choices=["personal", "company"])
    parser.add_argument("--dest", required=True, help="Destination AIOS root directory.")
    parser.add_argument("--var", action="append", metavar="KEY=VALUE",
                        help="Set an {{AIOS_*}} placeholder value (repeatable).")
    parser.add_argument("--skills-mode", default="link", choices=["link", "copy"])
    parser.add_argument("--upgrade", action="store_true",
                        help="Safe upgrade of an existing install.")
    args = parser.parse_args(argv)

    dest = Path(args.dest)
    variables = parse_vars(args.var)
    try:
        result = materialize(
            args.edition, dest, variables, args.upgrade, args.skills_mode
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(
        f"created={len(result['created'])} updated={len(result['updated'])} "
        f"skipped={len(result['skipped'])} proposed={len(result['proposed'])} "
        f"preserved={len(result['preserved'])} "
        f"skills_mode={result['skills_mode']}"
    )
    if result["missing_variables"]:
        print(
            "NOTICE placeholders without values were rendered blank: "
            + ", ".join(sorted(result["missing_variables"])),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
