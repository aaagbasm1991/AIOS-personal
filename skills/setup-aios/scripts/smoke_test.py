#!/usr/bin/env python3
"""Black-box smoke test for the AIOS materializer.

Runs against synthetic data in temporary directories only; never touches real
user data. It drives ``materialize.py`` as a subprocess (never imports it),
checks hard-coded golden paths, computes sentinel hashes here in the test, uses
real ``git check-ignore``, and uses filesystem ``resolve``/``samefile`` for link
resolution. It also runs negative validator checks so the validators cannot pass
tautologically.

Usage:
    python smoke_test.py --all
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MATERIALIZE = SCRIPT_DIR / "materialize.py"
TEMPLATE_VERSION = (
    SCRIPT_DIR.parent / "assets" / "templates" / "common"
    / ".aios" / "version.md.template"
)

STD_VARS = [
    "--var", "AIOS_NAME=SmokeAIOS",
    "--var", "AIOS_OWNER=SmokeOwner",
    "--var", "AIOS_LANGUAGE=zh-TW",
    "--var", "AIOS_PRIMARY_TASKS=- 任務一\n- 任務二",
    "--var", "AIOS_WORKING_STYLE=- 精簡\n- 先給答案",
    "--var", "AIOS_ALWAYS_NEVER=- NEVER 保存憑證",
    "--var", "AIOS_EDITION_RULES=- 個人記憶留 private/",
    "--var", "AIOS_DATE=2026-07-29",
]

EXPECTED_VERSION = "0.2.0"

GOLDEN_COMMON = [
    ".aios/edition.md",
    ".aios/local.md",
    ".aios/manifest.md",
    ".aios/version.md",
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "connections/obsidian/README.md",
    "knowledge/assets/.gitkeep",
    "knowledge/conflicts/README.md",
    "knowledge/inbox/README.md",
    "knowledge/index.md",
    "knowledge/log.md",
    "knowledge/outputs/.gitkeep",
    "private/README.md",
    "private/connections/obsidian/vault.md",
    "private/context/me.md",
    "private/context/what_not_to_do.md",
    "private/context/working_style.md",
    "private/memory/active-context.md",
    "private/memory/archive/README.md",
    "private/memory/daily/README.md",
    "private/memory/decisions.md",
    "private/memory/feedback.md",
    "private/memory/inbox.md",
    "private/memory/index.md",
    "private/memory/preferences.md",
    "private/memory/profile.md",
    "private/memory/review-state.md",
    "private/memory/reviews/README.md",
    "shared/README.md",
    "shared/agent-guidelines/karpathy-guidelines.md",
    "workspace/README.md",
]
GOLDEN_PERSONAL = [
    "knowledge/LAYOUT.md",
    "knowledge/sources/decisions/.gitkeep",
    "knowledge/sources/learning/.gitkeep",
    "knowledge/sources/life/.gitkeep",
    "knowledge/sources/projects/.gitkeep",
    "knowledge/wiki/people/.gitkeep",
    "knowledge/wiki/places/.gitkeep",
    "knowledge/wiki/projects/.gitkeep",
    "knowledge/wiki/topics/.gitkeep",
    "private/context/personal/content-and-learning.md",
    "private/context/personal/goals.md",
    "private/context/personal/habits.md",
    "private/context/personal/projects.md",
]
GOLDEN_COMPANY = [
    "knowledge/LAYOUT.md",
    "knowledge/sources/analysis/.gitkeep",
    "knowledge/sources/decisions/.gitkeep",
    "knowledge/sources/meetings/.gitkeep",
    "knowledge/sources/specs/.gitkeep",
    "knowledge/wiki/entities/.gitkeep",
    "knowledge/wiki/features/.gitkeep",
    "knowledge/wiki/games/.gitkeep",
    "knowledge/wiki/mechanics/.gitkeep",
    "knowledge/wiki/projects/.gitkeep",
    "knowledge/wiki/topics/.gitkeep",
    "private/context/work/active-projects.md",
    "private/context/work/my-role-and-responsibilities.md",
    "private/context/work/personal-work-notes.md",
    "private/context/work/team-and-stakeholders.md",
    "shared/company/README.md",
    "shared/company/about-company.md",
    "shared/company/products-and-services.md",
    "shared/company/team-workflow.md",
    "shared/team-memory/README.md",
    "shared/team-memory/glossary.md",
    "shared/team-memory/output-standards.md",
    "shared/team-memory/working-agreements.md",
]

REQUIRED_DIRS = [
    "workspace/inbox", "workspace/drafts", "workspace/projects",
    "workspace/references", "workspace/handoff", "workspace/archive",
]
KARPATHY_REF = "shared/agent-guidelines/karpathy-guidelines.md"

# Canonical minimum set of platform-native control artifacts (entry-policy.md).
NATIVE_ARTIFACTS = [
    "AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "CLAUDE.local.md",
    ".agents/", ".claude/", ".codex/", ".mcp.json",
]
FALLBACK_FILENAMES_PHRASE = "fallback instruction filenames"

# Canonical default data-file allowlist (entry-policy.md "預設資料檔 allowlist").
# Extension comparison is exact-set, not substring "contains allowlist".
ALLOWED_EXTENSIONS = [
    ".md", ".markdown", ".txt", ".rst", ".pdf", ".docx", ".pptx", ".xlsx",
    ".csv", ".tsv", ".json", ".yaml", ".yml",
    ".png", ".jpg", ".jpeg", ".webp",
]
SIZE_LIMIT_TOKENS = ["25 MiB", "100 MiB"]
PRECEDENCE_TOKENS = ["原生控制 artifact", "永遠優先"]
REJECTION_TOKENS = [
    "壓縮檔", "可執行檔", "安裝程式", "函式庫", "shell", "程式腳本",
    "巨集文件", "HTML", "SVG", "active content", "捷徑",
    "副檔名與內容類型不符",
]
# Matches the entries' inline "只有 `.ext`、`.ext2`…。" phrasing.
ENTRY_ALLOWLIST_RE = re.compile(
    r"預設資料檔 allowlist（副檔名不分大小寫）只有(.*?)。", re.DOTALL
)
# Matches the canonical entry-policy.md fenced ```text extension block.
POLICY_ALLOWLIST_RE = re.compile(
    r"預設只允許：\n\n```text\n(.*?)\n```", re.DOTALL
)
EXT_TOKEN_RE = re.compile(r"\.[A-Za-z0-9]+")

# Excluded folders/files the materialized external Obsidian Vault config must
# quarantine (private/connections/obsidian/vault.md).
VAULT_EXCLUDED_FOLDERS = [".agents", ".claude", ".codex"]
VAULT_EXCLUDED_FILES = [
    "AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "CLAUDE.local.md", ".mcp.json",
]

# Quarantine semantics shared verbatim by AGENTS.md/CLAUDE.md section 5
# (outside the platform-specific first bullet normalized in entry_mirror_failures).
SHARED_QUARANTINE_SEMANTICS = [
    "保持受信任 AIOS 根為工作目錄",
    "預設資料檔 allowlist",
    "不遞迴複製未知或隱藏目錄",
    "不追蹤 Symlink、Junction 或其他 reparse point",
    "inert 名稱",
    "不保留控制目錄結構",
    "採納不自動授權",
]

# Source-tree docs (not materialized output) required to keep synchronized
# coverage of the native-control artifact minimum set.
REFERENCE_DOC_PATHS = {
    "setup-aios/SKILL.md": SCRIPT_DIR.parent / "SKILL.md",
    "references/entry-policy.md": SCRIPT_DIR.parent / "references" / "entry-policy.md",
    "workspace README template":
        SCRIPT_DIR.parent / "assets" / "templates" / "common" / "workspace" / "README.md",
    "knowledge inbox README template":
        SCRIPT_DIR.parent / "assets" / "templates" / "common" / "knowledge" / "inbox" / "README.md",
    "references/obsidian-connection.md": SCRIPT_DIR.parent / "references" / "obsidian-connection.md",
    "bundled obsidian-vault SKILL.md":
        SCRIPT_DIR.parent / "assets" / "default-skills" / "obsidian-vault" / "SKILL.md",
    "update-wiki/SKILL.md": SCRIPT_DIR.parent.parent / "update-wiki" / "SKILL.md",
}


def template_version() -> str:
    for line in TEMPLATE_VERSION.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- version:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError(f"No version field in {TEMPLATE_VERSION}")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def run_materialize(edition: str, dest: Path, upgrade: bool = False,
                    skills_mode: str = "link") -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(MATERIALIZE), "--edition", edition, "--dest", str(dest),
           "--skills-mode", skills_mode, *STD_VARS]
    if upgrade:
        cmd.append("--upgrade")
    return subprocess.run(cmd, capture_output=True, text=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def snapshot_tree(root: Path) -> dict[str, tuple[str, str | None, float | None]]:
    """Complete destination-tree inventory keyed by relative POSIX path:
    entry type, file byte digest, and mtime (files only; never access time).
    Used to prove a rejected operation writes nothing anywhere in the tree,
    not only to the paths it explicitly names."""
    snapshot: dict[str, tuple[str, str | None, float | None]] = {}
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot[rel] = ("symlink", None, None)
        elif path.is_dir():
            snapshot[rel] = ("dir", None, None)
        elif path.is_file():
            snapshot[rel] = ("file", sha256(path), path.stat().st_mtime)
        else:
            snapshot[rel] = ("other", None, None)
    return snapshot


def snapshot_diff(
    label: str,
    before: dict[str, tuple[str, str | None, float | None]],
    after: dict[str, tuple[str, str | None, float | None]],
) -> list[str]:
    """Readable diff between two snapshot_tree() results: new/deleted paths,
    entry-type changes, and byte/mtime drift on files that survive."""
    fails: list[str] = []
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    if added:
        fails.append(f"{label} new path(s) appeared: {added}")
    if removed:
        fails.append(f"{label} path(s) disappeared: {removed}")
    for rel in sorted(set(before) & set(after)):
        before_kind, before_hash, before_mtime = before[rel]
        after_kind, after_hash, after_mtime = after[rel]
        if before_kind != after_kind:
            fails.append(
                f"{label} {rel} entry type changed {before_kind!r} -> {after_kind!r}"
            )
        elif before_kind == "file":
            if before_hash != after_hash:
                fails.append(f"{label} {rel} bytes changed")
            if before_mtime != after_mtime:
                fails.append(f"{label} {rel} mtime changed")
    return fails


def independent_tree_signature(root: Path) -> str:
    """Independently recompute the documented deterministic physical tree
    signature — per-directory-level sorted D\\0/F\\0 relative POSIX path
    markers plus SHA-256 file digests — as an oracle kept separate from
    materialize.py's own tree_signature(); this test never imports it."""
    digest = hashlib.sha256()
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        dirnames.sort()
        filenames.sort()
        for name in dirnames:
            child = current_path / name
            digest.update(
                b"D\0" + child.relative_to(root).as_posix().encode("utf-8") + b"\0"
            )
        for name in filenames:
            child = current_path / name
            digest.update(
                b"F\0" + child.relative_to(root).as_posix().encode("utf-8") + b"\0"
            )
            digest.update(hashlib.sha256(child.read_bytes()).digest())
    return digest.hexdigest()


def scan_unresolved(root: Path) -> list[str]:
    return [p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and "{{AIOS_" in _safe_text(p)]


def scan_bad_skill_link(root: Path) -> list[str]:
    return [p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and "../../skills" in _safe_text(p)]


def _safe_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def has_skill_md(skill_dir: Path) -> bool:
    return (skill_dir / "SKILL.md").is_file()


def has_placeholder(s: str) -> bool:
    return "{{AIOS_" in s


def create_dir_link(link: Path, target: Path) -> str | None:
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(str(target), link, target_is_directory=True)
        return "symlink"
    except OSError:
        if os.name != "nt":
            return None
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
    )
    return "junction" if result.returncode == 0 else None


def parse_kv(path: Path, key: str) -> str | None:
    for line in text(path).splitlines():
        line = line.strip().lstrip("-").strip()
        if line.startswith(key + ":"):
            return line.split(":", 1)[1].strip()
    return None


def installed_skill_names(manifest: Path) -> list[str]:
    names: list[str] = []
    in_section = False
    for line in text(manifest).splitlines():
        if line.strip() == "## Installed Skills":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] == "Skill" or set(cells[0]) == {"-"}:
            continue
        if cells[2].lower() in {"installed", "ready", "ok"}:
            names.append(cells[0])
    return names


def markdown_sections(content: str) -> dict[str, str]:
    matches = list(re.finditer(r"^## (\d+)\. .+$", content, re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        sections[match.group(1)] = content[match.start():end].strip()
    return sections


def missing_native_artifacts(content: str) -> list[str]:
    missing = [token for token in NATIVE_ARTIFACTS if token not in content]
    if FALLBACK_FILENAMES_PHRASE not in content:
        missing.append(FALLBACK_FILENAMES_PHRASE)
    return missing


def extract_allowlist_extensions(content: str) -> set[str] | None:
    """Pull the extension tokens out of the allowlist statement, whether it
    is the entries' inline backtick-list form or the canonical entry-policy.md
    fenced ```text block form. None if neither form is found."""
    match = ENTRY_ALLOWLIST_RE.search(content) or POLICY_ALLOWLIST_RE.search(content)
    if not match:
        return None
    return set(EXT_TOKEN_RE.findall(match.group(1)))


def entry_policy_failures(label: str, content: str) -> list[str]:
    """Validate the executable import boundary itself — the exact extension
    allowlist set, size limits, native-control precedence, and rejection
    semantics — not just the presence of the word "allowlist"."""
    fails: list[str] = []
    found = extract_allowlist_extensions(content)
    if found is None:
        fails.append(f"{label} allowlist statement not found")
    else:
        expected = set(ALLOWED_EXTENSIONS)
        if found != expected:
            missing = sorted(expected - found)
            extra = sorted(found - expected)
            fails.append(
                f"{label} allowlist extension set mismatch: "
                f"missing={missing} extra={extra}"
            )
    for token in SIZE_LIMIT_TOKENS:
        if token not in content:
            fails.append(f"{label} missing size limit {token!r}")
    for token in PRECEDENCE_TOKENS:
        if token not in content:
            fails.append(f"{label} missing native-control precedence token {token!r}")
    for token in REJECTION_TOKENS:
        if token not in content:
            fails.append(f"{label} missing rejection semantic {token!r}")
    return fails


# Hard-coded semantic requirements for the file-output authorization Gate
# (references/entry-policy.md "## 檔案產出授權 Gate"), verified verbatim in
# both the generated entry files' section 2 (協作方式) and the canonical
# policy doc. These tokens are checked independently of entry_mirror_failures
# / native_quarantine_failures, neither of which covers section 2 — a
# synchronized removal from both entries would otherwise pass mirror parity.
GATE_TOKENS = [
    "預設只在對話中顯示內容，不建立",
    "明確要求建立、修改、寫入、儲存、實作或修正檔案",
    "內容預覽、精確目標路徑與實質變更範圍",
    "查看、分析、規劃、研究、審查、整理內容",
    "不構成寫檔授權",
]


def gate_failures(label: str, content: str) -> list[str]:
    """Independent oracle for the file-output authorization Gate: checks
    hard-coded semantic tokens are present verbatim, regardless of whether
    AGENTS.md and CLAUDE.md still mirror each other."""
    return [
        f"{label} missing file-output authorization Gate token {token!r}"
        for token in GATE_TOKENS
        if token not in content
    ]


def vault_config_failures(root: Path) -> list[str]:
    """Independent oracle: the materialized external Obsidian Vault config
    must quarantine the native-control artifacts, not just data files."""
    path = root / "private" / "connections" / "obsidian" / "vault.md"
    if not path.is_file():
        return ["materialized private/connections/obsidian/vault.md is missing"]
    content = text(path)
    fails: list[str] = []
    for token in VAULT_EXCLUDED_FOLDERS:
        if f"- {token}" not in content:
            fails.append(f"vault.md missing excluded folder {token!r}")
    for token in VAULT_EXCLUDED_FILES:
        if f"- {token}" not in content:
            fails.append(f"vault.md missing excluded file {token!r}")
    return fails


def native_quarantine_failures(agents_text: str, claude_text: str) -> list[str]:
    """Independent completeness check for the native-control quarantine
    contract: the generated trust sections must both carry the full minimum
    artifact set and the shared quarantine semantics, not just mirror
    each other (mirror parity is checked separately)."""
    fails: list[str] = []
    agents_sections = markdown_sections(agents_text)
    claude_sections = markdown_sections(claude_text)
    for label, sections in (("AGENTS.md", agents_sections), ("CLAUDE.md", claude_sections)):
        trust = sections.get("5", "")
        if not trust:
            fails.append(f"{label} missing trust boundary section 5")
            continue
        missing = missing_native_artifacts(trust)
        if missing:
            fails.append(f"{label} trust section missing native-control items {missing}")
        for phrase in SHARED_QUARANTINE_SEMANTICS:
            if phrase not in trust:
                fails.append(f"{label} trust section missing quarantine semantic {phrase!r}")
        fails.extend(f"{label} {failure}" for failure in entry_policy_failures(label, trust))
    return fails


CONTEXT_PATH_RE = re.compile(r"`((?:\.\./)+context/[^`]+\.md)`")


def canonical_context_path_failures(root: Path) -> list[str]:
    """Independent validator: canonical routes declared in the private/memory
    provenance ledgers must resolve, from private/memory/, to real files
    under private/context/. Oracle paths are hard-coded here, not derived
    from materialize.py."""
    fails: list[str] = []
    memory_dir = root / "private" / "memory"
    context_dir = (root / "private" / "context").resolve()
    sources = [
        memory_dir / "profile.md",
        memory_dir / "preferences.md",
        memory_dir / "index.md",
    ]
    found_any = False
    for src in sources:
        if not src.is_file():
            continue
        for rel in CONTEXT_PATH_RE.findall(text(src)):
            found_any = True
            resolved = (memory_dir / rel).resolve()
            label = f"{rel!r} declared in {src.relative_to(root).as_posix()}"
            if not resolved.is_file():
                fails.append(
                    f"canonical path {label} does not resolve to an "
                    "existing file"
                )
            elif resolved != context_dir and context_dir not in resolved.parents:
                fails.append(
                    f"canonical path {label} does not resolve under "
                    "private/context/"
                )
    if not found_any:
        fails.append(
            "no canonical private/context/ paths declared under private/memory/"
        )
    return fails


def entry_mirror_failures(root: Path) -> list[str]:
    agents = text(root / "AGENTS.md")
    claude = text(root / "CLAUDE.md")
    agents_sections = markdown_sections(agents)
    claude_sections = markdown_sections(claude)
    fails: list[str] = []
    if set(agents_sections) != set(claude_sections):
        fails.append("entry mirror section numbering differs")
        return fails

    for section_number in ("4", "6", "7", "9", "10", "11", "12", "13"):
        if agents_sections[section_number] != claude_sections[section_number]:
            fails.append(
                f"entry mirror shared section {section_number} differs"
            )

    agents_trust = agents_sections["5"].replace(
        "Codex 包括 `AGENTS.md`、`AGENTS.override.md` 與 host 設定的 "
        "fallback instruction filenames",
        "PLATFORM_NATIVE_SOURCES",
    )
    claude_trust = claude_sections["5"].replace(
        "Claude Code 包括 `CLAUDE.md`、`CLAUDE.local.md` 與其他 host 設定的"
        "原生指令來源",
        "PLATFORM_NATIVE_SOURCES",
    )
    if agents_trust != claude_trust:
        fails.append("entry mirror trust section differs beyond platform entry")

    agents_priority = agents_sections["8"].replace(
        "`AGENTS.md`", "`PRIMARY_ENTRY.md`"
    )
    claude_priority = claude_sections["8"].replace(
        "`CLAUDE.md`", "`PRIMARY_ENTRY.md`"
    )
    if agents_priority != claude_priority:
        fails.append("entry mirror memory-priority section differs")

    def routing_table(section: str) -> str:
        start = section.find("| 讀取 |")
        end = section.find("\n\n永不", start)
        return section[start:end]

    if routing_table(agents_sections["3"]) != routing_table(claude_sections["3"]):
        fails.append("entry mirror conditional-routing table differs")
    return fails


def validate_install(root: Path, edition: str | None = None) -> list[str]:
    """Independent output oracle used for positive and mutated fixtures."""
    fails: list[str] = []
    for rel in GOLDEN_COMMON:
        if not (root / rel).exists():
            fails.append(f"missing required path {rel}")
    for rel in REQUIRED_DIRS:
        if not (root / rel).is_dir():
            fails.append(f"missing required directory {rel}")

    unresolved = scan_unresolved(root)
    if unresolved:
        fails.append(f"unresolved placeholders in {unresolved}")
    bad_links = scan_bad_skill_link(root)
    if bad_links:
        fails.append(f"stale ../../skills in {bad_links}")
    fails.extend(canonical_context_path_failures(root))

    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    if agents.exists():
        if "private/memory/index.md" not in text(agents):
            fails.append("AGENTS.md missing conditional memory index route")
        if KARPATHY_REF not in text(agents):
            fails.append("AGENTS.md missing Karpathy route")
        fails.extend(gate_failures("AGENTS.md", text(agents)))
    if claude.exists():
        if "private/memory/index.md" not in text(claude):
            fails.append("CLAUDE.md missing conditional memory index route")
        if KARPATHY_REF in text(claude):
            fails.append("CLAUDE.md unexpectedly contains Karpathy route")
        fails.extend(gate_failures("CLAUDE.md", text(claude)))
    if agents.exists() and claude.exists():
        fails.extend(entry_mirror_failures(root))
        fails.extend(native_quarantine_failures(text(agents), text(claude)))

    if (root / "private" / "connections" / "obsidian").is_dir():
        fails.extend(vault_config_failures(root))

    manifest = root / ".aios" / "manifest.md"
    version = root / ".aios" / "version.md"
    edition_file = root / ".aios" / "edition.md"
    if manifest.exists() and version.exists():
        manifest_version = parse_kv(manifest, "version")
        version_value = parse_kv(version, "version")
        if manifest_version != version_value:
            fails.append(
                f"version mismatch manifest={manifest_version} "
                f"version.md={version_value}"
            )
        if version_value != EXPECTED_VERSION:
            fails.append(
                f"release version {version_value}, expected {EXPECTED_VERSION}"
            )
    if edition and manifest.exists() and edition_file.exists():
        manifest_edition = parse_kv(manifest, "edition")
        file_edition = parse_kv(edition_file, "edition")
        if not (manifest_edition == file_edition == edition):
            fails.append(
                f"edition mismatch manifest={manifest_edition} "
                f"edition.md={file_edition} expected={edition}"
            )

    if manifest.exists():
        mode = parse_kv(manifest, "skills_mode")
        skills = root / "skills"
        entries = (root / ".agents" / "skills", root / ".claude" / "skills")
        if mode == "link":
            for entry in entries:
                if not entry.exists() or entry.resolve() != skills.resolve():
                    fails.append(f"Skill link does not resolve to root skills: {entry}")
                elif os.name != "nt" and entry.is_symlink():
                    if os.readlink(entry) != "../skills":
                        fails.append(
                            f"Skill symlink target is {os.readlink(entry)!r}, "
                            "expected '../skills'"
                        )
        elif mode == "copy":
            for entry in entries:
                if not entry.is_dir() or entry.is_symlink():
                    fails.append(f"copy-mode entry is not a physical directory: {entry}")
        else:
            fails.append(f"unknown skills_mode {mode!r}")

        for skill_name in installed_skill_names(manifest):
            for base in (root / "skills", *entries):
                if not has_skill_md(base / skill_name):
                    fails.append(
                        f"manifest marks {skill_name!r} installed but "
                        f"{base / skill_name / 'SKILL.md'} is missing"
                    )
    return fails


# --------------------------------------------------------------------------- #
# test cases — each returns a list of failure strings (empty == pass)
# --------------------------------------------------------------------------- #
def t_materialize_edition(edition: str, golden_extra: list[str]) -> list[str]:
    fails: list[str] = []
    dest = Path(tempfile.mkdtemp(prefix=f"aios-{edition}-"))
    try:
        r = run_materialize(edition, dest, skills_mode="copy")
        if r.returncode != 0:
            return [f"[{edition}] materialize rc={r.returncode}: {r.stderr.strip()}"]
        for rel in GOLDEN_COMMON + golden_extra:
            if not (dest / rel).exists():
                fails.append(f"[{edition}] missing golden path {rel}")
        fails.extend(f"[{edition}] {failure}" for failure in validate_install(dest, edition))
        # mapping: no template/example artifacts survive in output
        leftovers = [p.relative_to(dest).as_posix() for p in dest.rglob("*")
                     if p.is_file() and (p.name.endswith(".template")
                                         or p.name == "local.example.md"
                                         or "private.example" in p.relative_to(dest).parts)]
        if leftovers:
            fails.append(f"[{edition}] unmapped template/example artifacts {leftovers}")
        wrong_edition = (
            dest / "private" / "context"
            / ("work" if edition == "personal" else "personal")
        )
        if wrong_edition.exists():
            fails.append(f"[{edition}] leaked other-edition context {wrong_edition}")
        if edition == "company":
            for stale in (
                "shared/company/glossary.md",
                "shared/company/output-standards.md",
            ):
                if (dest / stale).exists():
                    fails.append(
                        f"[company] duplicated team-memory authority at {stale}"
                    )
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return fails


def t_idempotent_and_sentinel() -> list[str]:
    fails: list[str] = []
    dest = Path(tempfile.mkdtemp(prefix="aios-idem-"))
    try:
        first = run_materialize("personal", dest, skills_mode="copy")
        if first.returncode != 0:
            return [f"[idempotent] first run failed: {first.stderr.strip()}"]
        sentinels = {
            dest / "private" / "memory" / "inbox.md":
                "USER-OWNED PRIVATE SENTINEL\n",
            dest / ".aios" / "local.md":
                "USER-OWNED LOCAL SENTINEL\n",
            dest / "notes.md":
                "USER-OWNED EXTRA FILE\n",
        }
        for path, content in sentinels.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        before = {path: sha256(path) for path in sentinels}
        r2 = run_materialize("personal", dest, skills_mode="copy")
        if r2.returncode != 0:
            fails.append(f"[idempotent] second run rc={r2.returncode}")
        for path, digest in before.items():
            if sha256(path) != digest:
                fails.append(f"[idempotent] sentinel overwritten: {path}")
        if "created=0" not in r2.stdout:
            fails.append(f"[idempotent] second run created files, expected none: {r2.stdout.strip()}")
        if list(dest.rglob("private.example")):
            fails.append("[idempotent] nested private.example survived")
        if list(dest.rglob("*.proposed.md.proposed.md")):
            fails.append("[idempotent] generated nested proposed file")
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return fails


def t_safe_upgrade() -> list[str]:
    fails: list[str] = []
    dest = Path(tempfile.mkdtemp(prefix="aios-upgrade-"))
    try:
        (dest / ".aios").mkdir(parents=True)
        (dest / "private" / "memory").mkdir(parents=True)
        (dest / ".aios" / "version.md").write_text(
            "# AIOS Version\n\n- version: 0.1.0\n- updated: 2026-01-01\n",
            encoding="utf-8",
        )
        (dest / ".aios" / "manifest.md").write_text(
            "# AIOS Manifest\n\n"
            "- edition: personal\n"
            "- version: 0.1.0\n"
            "- created: 2026-01-01\n"
            "- skills_mode: copy\n"
            "- skills_link_type: fallback-copy\n\n"
            "- upgrade_from: 0.0.0\n"
            "- upgrade_to: 0.1.0\n"
            "- upgrade_status: complete\n"
            "- unapplied_differences: none\n\n"
            "## Installed Skills\n\n"
            "| Skill | Source | Status | Notes |\n"
            "|---|---|---|---|\n\n"
            "## Missing or Optional Skills\n\n"
            "| Skill | Reason | Suggested action |\n"
            "|---|---|---|\n",
            encoding="utf-8",
        )
        agents = dest / "AGENTS.md"
        claude = dest / "CLAUDE.md"
        private = dest / "private" / "memory" / "inbox.md"
        local = dest / ".aios" / "local.md"
        extra = dest / "notes.md"
        agents.write_text("# USER 0.1 AGENTS\n", encoding="utf-8")
        claude.write_text("# USER 0.1 CLAUDE\n", encoding="utf-8")
        private.write_text("USER PRIVATE SENTINEL\n", encoding="utf-8")
        local.write_text("USER LOCAL SENTINEL\n", encoding="utf-8")
        extra.write_text("USER EXTRA SENTINEL\n", encoding="utf-8")
        protected = (agents, claude, private, local, extra)
        protected_hashes = {path: sha256(path) for path in protected}

        r = run_materialize(
            "personal", dest, upgrade=True, skills_mode="copy"
        )
        if r.returncode != 0:
            fails.append(f"[upgrade] rc={r.returncode}: {r.stderr.strip()}")
            return fails
        for path, digest in protected_hashes.items():
            if sha256(path) != digest:
                fails.append(f"[upgrade] protected file was overwritten: {path}")
        for proposed in ("AGENTS.md.proposed.md", "CLAUDE.md.proposed.md"):
            if not (dest / proposed).exists():
                fails.append(f"[upgrade] missing {proposed}")
        report = dest / ".aios" / "upgrade-report.md"
        manifest = dest / ".aios" / "manifest.md"
        version = dest / ".aios" / "version.md"
        if not report.exists():
            fails.append("[upgrade] upgrade-report.md not created")
        else:
            report_text = text(report)
            if "- source_version: 0.1.0" not in report_text:
                fails.append("[upgrade] report lost source_version 0.1.0")
            if f"- target_version: {EXPECTED_VERSION}" not in report_text:
                fails.append("[upgrade] report has wrong target_version")
            if "- generated: 2026-07-29" not in report_text:
                fails.append("[upgrade] report did not persist operation date")
        if parse_kv(version, "version") != EXPECTED_VERSION:
            fails.append("[upgrade] managed version metadata did not advance")
        expected_manifest = {
            "version": EXPECTED_VERSION,
            "upgrade_from": "0.1.0",
            "upgrade_to": EXPECTED_VERSION,
            "upgrade_status": "pending-review",
            "skills_link_type": "fallback-copy",
        }
        for key, expected in expected_manifest.items():
            if parse_kv(manifest, key) != expected:
                fails.append(
                    f"[upgrade] manifest {key}={parse_kv(manifest, key)!r}, "
                    f"expected {expected!r}"
                )
        unapplied = parse_kv(manifest, "unapplied_differences") or ""
        for proposed in ("AGENTS.md.proposed.md", "CLAUDE.md.proposed.md"):
            if proposed not in unapplied:
                fails.append(f"[upgrade] manifest omitted {proposed}")

        stable_outputs = (
            *protected,
            dest / "AGENTS.md.proposed.md",
            dest / "CLAUDE.md.proposed.md",
            report,
            manifest,
            version,
        )
        stable_hashes = {path: sha256(path) for path in stable_outputs}
        # idempotent repeat upgrade
        r2 = run_materialize(
            "personal", dest, upgrade=True, skills_mode="copy"
        )
        if r2.returncode != 0:
            fails.append(f"[upgrade] repeat rc={r2.returncode}")
        for path, digest in stable_hashes.items():
            if sha256(path) != digest:
                fails.append(f"[upgrade] repeat upgrade changed {path}")
        if list(dest.rglob("*.proposed.md.proposed.md")):
            fails.append("[upgrade] repeat produced nested proposed file")
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return fails


def t_edited_proposal_sentinel() -> list[str]:
    """A user-reviewed/edited *.proposed.md must never be silently
    overwritten, and the conflict must stop the whole upgrade before any
    other release change (version/manifest) is written."""
    fails: list[str] = []
    dest = Path(tempfile.mkdtemp(prefix="aios-editedproposal-"))
    try:
        (dest / ".aios").mkdir(parents=True)
        (dest / "private" / "memory").mkdir(parents=True)
        (dest / ".aios" / "version.md").write_text(
            "# AIOS Version\n\n- version: 0.1.0\n- updated: 2026-01-01\n",
            encoding="utf-8",
        )
        (dest / ".aios" / "manifest.md").write_text(
            "# AIOS Manifest\n\n"
            "- edition: personal\n"
            "- version: 0.1.0\n"
            "- created: 2026-01-01\n"
            "- skills_mode: copy\n"
            "- skills_link_type: fallback-copy\n\n"
            "- upgrade_from: 0.0.0\n"
            "- upgrade_to: 0.1.0\n"
            "- upgrade_status: complete\n"
            "- unapplied_differences: none\n\n"
            "## Installed Skills\n\n"
            "| Skill | Source | Status | Notes |\n"
            "|---|---|---|---|\n\n"
            "## Missing or Optional Skills\n\n"
            "| Skill | Reason | Suggested action |\n"
            "|---|---|---|\n",
            encoding="utf-8",
        )
        (dest / "AGENTS.md").write_text("# USER 0.1 AGENTS\n", encoding="utf-8")
        (dest / "CLAUDE.md").write_text("# USER 0.1 CLAUDE\n", encoding="utf-8")
        (dest / "private" / "memory" / "inbox.md").write_text(
            "USER PRIVATE SENTINEL\n", encoding="utf-8"
        )
        (dest / ".aios" / "local.md").write_text(
            "USER LOCAL SENTINEL\n", encoding="utf-8"
        )

        first = run_materialize("personal", dest, upgrade=True, skills_mode="copy")
        if first.returncode != 0:
            return [f"[edited-proposal] seeding upgrade failed: {first.stderr.strip()}"]

        proposed = dest / "AGENTS.md.proposed.md"
        if not proposed.exists():
            return ["[edited-proposal] fixture did not produce AGENTS.md.proposed.md"]

        manifest = dest / ".aios" / "manifest.md"
        version = dest / ".aios" / "version.md"
        manifest_before = sha256(manifest)
        version_before = sha256(version)

        # simulate the user reviewing and editing the proposal
        proposed.write_text("# USER EDITED PROPOSAL\n", encoding="utf-8")
        old_mtime = 1700000000
        os.utime(proposed, (old_mtime, old_mtime))
        edited_hash = sha256(proposed)

        # whole-tree inventory (path/type + file bytes/mtime), taken after
        # the seeding upgrade and the edit, before the conflicting run — this
        # is what proves the conflict is a zero-write stop everywhere in the
        # existing release tree (.aios/upgrade-report.md, manifest, version,
        # the other proposal, all public/managed output, no new paths), not
        # only for the edited proposal/manifest/version.
        tree_before_conflict = snapshot_tree(dest)

        second = run_materialize("personal", dest, upgrade=True, skills_mode="copy")
        if second.returncode == 0:
            fails.append(
                "[edited-proposal] materialize did not stop for an edited "
                "proposal conflict"
            )
        if "proposed" not in (second.stderr or "").lower():
            fails.append(
                "[edited-proposal] conflict was not reported on stderr"
            )
        if sha256(proposed) != edited_hash:
            fails.append(
                "[edited-proposal] user-edited proposal bytes were overwritten"
            )
        if int(proposed.stat().st_mtime) != old_mtime:
            fails.append(
                "[edited-proposal] user-edited proposal mtime was touched"
            )
        if sha256(manifest) != manifest_before:
            fails.append(
                "[edited-proposal] conflict still wrote manifest.md "
                "(partial upgrade)"
            )
        if sha256(version) != version_before:
            fails.append(
                "[edited-proposal] conflict still wrote version.md "
                "(partial upgrade)"
            )
        fails.extend(
            f"[edited-proposal] second run {failure}"
            for failure in snapshot_diff(
                "whole-tree", tree_before_conflict, snapshot_tree(dest)
            )
        )

        # repeated runs must not proliferate files while the conflict stands
        third = run_materialize("personal", dest, upgrade=True, skills_mode="copy")
        if third.returncode == 0:
            fails.append(
                "[edited-proposal] repeated run stopped reporting the conflict"
            )
        if list(dest.rglob("*.proposed.md.proposed.md")) or list(
            dest.glob("AGENTS.md.proposed*.md*")
        ) != [proposed]:
            fails.append(
                "[edited-proposal] repeated runs proliferated proposal files"
            )
        fails.extend(
            f"[edited-proposal] third run {failure}"
            for failure in snapshot_diff(
                "whole-tree", tree_before_conflict, snapshot_tree(dest)
            )
        )
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return fails


def t_git_check_ignore() -> list[str]:
    if shutil.which("git") is None:
        print("  [SKIP] git not on PATH — cannot verify check-ignore")
        return []
    fails: list[str] = []
    dest = Path(tempfile.mkdtemp(prefix="aios-git-"))
    try:
        materialized = run_materialize("personal", dest, skills_mode="copy")
        if materialized.returncode != 0:
            return [f"[git] materialize failed: {materialized.stderr.strip()}"]
        subprocess.run(["git", "init", "-q"], cwd=dest, check=True,
                       capture_output=True, text=True)
        must_ignore = [
            "private/x.md",
            "workspace/y.md",
            ".aios/local.md",
            ".agents/skills",
            ".claude/skills",
            ".env",
            "knowledge/outputs/z.md",
        ]
        for rel in must_ignore:
            res = subprocess.run(["git", "check-ignore", "-q", rel], cwd=dest,
                                 capture_output=True, text=True)
            if res.returncode != 0:
                fails.append(f"[git] expected ignored but not: {rel}")
        # a tracked path must NOT be ignored
        res = subprocess.run(["git", "check-ignore", "-q", "AGENTS.md"], cwd=dest,
                             capture_output=True, text=True)
        if res.returncode == 0:
            fails.append("[git] AGENTS.md unexpectedly ignored")
        res = subprocess.run(
            ["git", "check-ignore", "-q", "private.example/README.md"],
            cwd=dest, capture_output=True, text=True,
        )
        if res.returncode == 0:
            fails.append("[git] tracked private.example template unexpectedly ignored")
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return fails


def t_link_and_copy_mode() -> list[str]:
    fails: list[str] = []
    link_dest = Path(tempfile.mkdtemp(prefix="aios-link-"))
    copy_dest = Path(tempfile.mkdtemp(prefix="aios-copy-"))
    try:
        for dest in (link_dest, copy_dest):
            skill = dest / "skills" / "demo-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: Synthetic smoke fixture.\n---\n",
                encoding="utf-8",
            )

        copied = run_materialize("personal", copy_dest, skills_mode="copy")
        if copied.returncode != 0:
            fails.append(f"[copy-mode] materialize failed: {copied.stderr.strip()}")
        else:
            if parse_kv(copy_dest / ".aios" / "manifest.md", "skills_mode") != "copy":
                fails.append("[copy-mode] manifest did not record actual copy mode")
            for entry in (
                copy_dest / ".agents" / "skills",
                copy_dest / ".claude" / "skills",
            ):
                if entry.is_symlink() or not has_skill_md(entry / "demo-skill"):
                    fails.append(f"[copy-mode] invalid physical Skill entry {entry}")

        for entry in (
            copy_dest / ".agents" / "skills",
            copy_dest / ".claude" / "skills",
        ):
            shutil.rmtree(entry)
        transitioned = run_materialize(
            "personal", copy_dest, skills_mode="link"
        )
        if transitioned.returncode != 0:
            fails.append(
                f"[mode-transition] materialize failed: "
                f"{transitioned.stderr.strip()}"
            )
        else:
            manifest_mode = parse_kv(
                copy_dest / ".aios" / "manifest.md", "skills_mode"
            )
            manifest_type = parse_kv(
                copy_dest / ".aios" / "manifest.md", "skills_link_type"
            )
            if manifest_mode == "link":
                for entry in (
                    copy_dest / ".agents" / "skills",
                    copy_dest / ".claude" / "skills",
                ):
                    if entry.resolve() != (copy_dest / "skills").resolve():
                        fails.append(
                            "[mode-transition] manifest says link but entry "
                            f"does not resolve to root skills: {entry}"
                        )
            elif manifest_mode == "copy":
                if manifest_type not in {"copy", "fallback-copy"}:
                    fails.append(
                        "[mode-transition] copy fallback has wrong "
                        f"skills_link_type {manifest_type!r}"
                    )
            else:
                fails.append(
                    f"[mode-transition] manifest kept stale mode "
                    f"{manifest_mode!r}"
                )

        linked = run_materialize("personal", link_dest, skills_mode="link")
        if linked.returncode != 0:
            fails.append(f"[link-mode] materialize failed: {linked.stderr.strip()}")
        else:
            actual_mode = parse_kv(
                link_dest / ".aios" / "manifest.md", "skills_mode"
            )
            entries = (
                link_dest / ".agents" / "skills",
                link_dest / ".claude" / "skills",
            )
            if actual_mode == "copy":
                print(
                    "  [SKIP] host could not create Symlink/Junction; "
                    "materializer recorded and verified fallback copy"
                )
                for entry in entries:
                    if not has_skill_md(entry / "demo-skill"):
                        fails.append(
                            f"[link fallback] missing copied Skill at {entry}"
                        )
            elif actual_mode == "link":
                for entry in entries:
                    if entry.resolve() != (link_dest / "skills").resolve():
                        fails.append(
                            f"[link-mode] {entry} does not resolve to root skills"
                        )
                    target_file = entry / "demo-skill" / "SKILL.md"
                    if not target_file.exists() or not os.path.samefile(
                        target_file,
                        link_dest / "skills" / "demo-skill" / "SKILL.md",
                    ):
                        fails.append(
                            f"[link-mode] SKILL.md not identical through {entry}"
                        )
                    if os.name != "nt" and entry.is_symlink():
                        if os.readlink(entry) != "../skills":
                            fails.append(
                                f"[link-mode] lexical target is "
                                f"{os.readlink(entry)!r}, expected '../skills'"
                            )
            else:
                fails.append(f"[link-mode] unknown actual mode {actual_mode!r}")
    finally:
        shutil.rmtree(link_dest, ignore_errors=True)
        shutil.rmtree(copy_dest, ignore_errors=True)
    return fails


def t_copy_finalize_sync() -> list[str]:
    """Independent black-box fixture using the real documented order —
    materialize an empty skeleton, THEN install a Skill into root skills/
    (not a pre-seeded root Skill) — and prove finalize/rerun repairs the
    copy-mode platform entries, is idempotent, and never touches a
    platform copy that has diverged from what was generated."""
    fails: list[str] = []
    dest = Path(tempfile.mkdtemp(prefix="aios-copy-finalize-"))
    try:
        skeleton = run_materialize("personal", dest, skills_mode="copy")
        if skeleton.returncode != 0:
            return [f"[copy-finalize] skeleton materialize failed: {skeleton.stderr.strip()}"]
        entries = (dest / ".agents" / "skills", dest / ".claude" / "skills")
        for entry in entries:
            if list(entry.iterdir()):
                fails.append(f"[copy-finalize] expected empty skeleton entry {entry}")

        # Install a Skill into the root tree AFTER the skeleton, exactly as
        # the documented setup sequence does.
        skill = dest / "skills" / "demo-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: Synthetic finalize fixture.\n---\n",
            encoding="utf-8",
        )

        finalized = run_materialize("personal", dest, skills_mode="copy")
        if finalized.returncode != 0:
            fails.append(f"[copy-finalize] finalize rc={finalized.returncode}: {finalized.stderr.strip()}")
        else:
            for entry in entries:
                target = entry / "demo-skill" / "SKILL.md"
                if not target.exists():
                    fails.append(f"[copy-finalize] finalize did not repair {entry}")
                elif sha256(target) != sha256(skill / "SKILL.md"):
                    fails.append(f"[copy-finalize] {entry} content diverges from root skills")
            skills_root = dest / "skills"
            expected_signature = independent_tree_signature(skills_root)
            manifest_signature = parse_kv(
                dest / ".aios" / "manifest.md", "skills_copy_signature"
            )
            if manifest_signature != expected_signature:
                fails.append(
                    "[copy-finalize] manifest skills_copy_signature "
                    f"{manifest_signature!r} does not equal the independently "
                    f"computed root skills/ signature {expected_signature!r}"
                )
            for entry in entries:
                entry_signature = independent_tree_signature(entry)
                if entry_signature != expected_signature:
                    fails.append(
                        f"[copy-finalize] platform copy {entry} tree signature "
                        f"{entry_signature!r} does not equal root skills/ "
                        f"signature {expected_signature!r} after finalize"
                    )

        # idempotent rerun: an already-synced copy must not change again
        before_hashes = {
            p: sha256(p) for entry in entries for p in entry.rglob("*") if p.is_file()
        }
        rerun = run_materialize("personal", dest, skills_mode="copy")
        if rerun.returncode != 0:
            fails.append(f"[copy-finalize] idempotent rerun rc={rerun.returncode}: {rerun.stderr.strip()}")
        after_hashes = {
            p: sha256(p) for entry in entries for p in entry.rglob("*") if p.is_file()
        }
        if before_hashes != after_hashes:
            fails.append("[copy-finalize] idempotent rerun changed synced copies")

        # negative sentinel: modify only the second-scanned platform copy
        # (.claude/skills), then add content to root skills/. Root gaining
        # content makes the untouched first-scanned entry (.agents/skills)
        # eligible and queued for resync — its own signature still matches
        # what was last recorded — before the scan even reaches the
        # second-scanned entry and discovers its divergence. This proves the
        # whole resync is all-or-nothing: the queued first entry must not be
        # partially applied, and the divergent second entry must be
        # preserved exactly (byte/path/mtime), in this documented order.
        first_entry, second_entry = entries
        before_first = {
            p: (sha256(p), p.stat().st_mtime)
            for p in first_entry.rglob("*") if p.is_file()
        }
        stray = second_entry / "demo-skill" / "USER-ADDED.md"
        stray.write_text("USER MODIFIED\n", encoding="utf-8")
        before_second = {
            p: (sha256(p), p.stat().st_mtime)
            for p in second_entry.rglob("*") if p.is_file()
        }
        (skill / "second.txt").write_text("root gained more content\n", encoding="utf-8")

        diverged = run_materialize("personal", dest, skills_mode="copy")
        if diverged.returncode == 0:
            fails.append(
                "[copy-finalize] a modified platform copy was silently reconciled"
            )
        after_first = {
            p: (sha256(p), p.stat().st_mtime)
            for p in first_entry.rglob("*") if p.is_file()
        }
        after_second = {
            p: (sha256(p), p.stat().st_mtime)
            for p in second_entry.rglob("*") if p.is_file()
        }
        if after_first != before_first:
            fails.append(
                f"[copy-finalize] queued first-scanned entry {first_entry} "
                "was partially applied despite the second-scanned entry's "
                "conflict"
            )
        if after_second != before_second:
            fails.append(
                f"[copy-finalize] divergent second-scanned entry {second_entry} "
                "was overwritten or deleted"
            )
        if (first_entry / "demo-skill" / "second.txt").exists():
            fails.append(
                "[copy-finalize] the queued first-scanned entry received the "
                "new root file despite the conflict"
            )
        if (second_entry / "demo-skill" / "second.txt").exists():
            fails.append(
                "[copy-finalize] the divergent second-scanned entry received "
                "the new root file"
            )
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return fails


def t_installed_vs_missing_skill() -> list[str]:
    fails: list[str] = []
    dest = Path(tempfile.mkdtemp(prefix="aios-skillmd-"))
    try:
        good = dest / "skills" / "good"
        good.mkdir(parents=True)
        (good / "SKILL.md").write_text(
            "---\nname: good\ndescription: Synthetic smoke fixture.\n---\n",
            encoding="utf-8",
        )
        materialized = run_materialize("personal", dest, skills_mode="copy")
        if materialized.returncode != 0:
            return [f"[skill-md] materialize failed: {materialized.stderr.strip()}"]
        manifest = dest / ".aios" / "manifest.md"
        manifest_text = text(manifest).replace(
            "|---|---|---|---|",
            "|---|---|---|---|\n"
            "| good | skills/good | installed | synthetic |",
            1,
        )
        manifest.write_text(manifest_text, encoding="utf-8")
        validation = validate_install(dest, "personal")
        if validation:
            fails.extend(f"[skill-md] {failure}" for failure in validation)
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return fails


def t_link_boundary_safety() -> list[str]:
    fails: list[str] = []
    sandbox = Path(tempfile.mkdtemp(prefix="aios-link-boundary-"))
    try:
        dest = sandbox / "install"
        external = sandbox / "external-private"
        dest.mkdir()
        external.mkdir()
        sentinel = external / "sentinel.txt"
        sentinel.write_text("DO NOT CHANGE\n", encoding="utf-8")
        if create_dir_link(dest / "private", external) is None:
            print("  [SKIP] host cannot create a synthetic private link/Junction")
            return fails
        before_hash = sha256(sentinel)
        result = run_materialize("personal", dest, skills_mode="copy")
        if result.returncode != 0:
            fails.append(
                f"[link-boundary] protected private link caused full failure: "
                f"{result.stderr.strip()}"
            )
        if (
            sorted(path.name for path in external.iterdir()) != ["sentinel.txt"]
            or sha256(sentinel) != before_hash
        ):
            fails.append("[link-boundary] setup wrote through private link/Junction")

        managed_dest = sandbox / "managed-install"
        managed_external = sandbox / "external-agents"
        managed_dest.mkdir()
        managed_external.mkdir()
        if create_dir_link(managed_dest / ".agents", managed_external) is not None:
            managed = run_materialize(
                "personal", managed_dest, skills_mode="copy"
            )
            if managed.returncode == 0:
                fails.append(
                    "[link-boundary] setup accepted a linked managed .agents path"
                )
            if list(managed_external.iterdir()):
                fails.append(
                    "[link-boundary] setup wrote through managed .agents link"
                )

        public_dest = sandbox / "public-install"
        public_external = sandbox / "external-shared"
        public_dest.mkdir()
        public_external.mkdir()
        public_sentinel = public_external / "sentinel.txt"
        public_sentinel.write_text("DO NOT CHANGE\n", encoding="utf-8")
        if create_dir_link(public_dest / "shared", public_external) is not None:
            public_before = sha256(public_sentinel)
            public = run_materialize(
                "personal", public_dest, skills_mode="copy"
            )
            if public.returncode == 0:
                fails.append(
                    "[link-boundary] setup accepted a linked public shared path"
                )
            if (
                sorted(path.name for path in public_external.iterdir())
                != ["sentinel.txt"]
                or sha256(public_sentinel) != public_before
            ):
                fails.append(
                    "[link-boundary] setup wrote through public shared link"
                )

        # shared/rules has no backing template file (directory-only public
        # destination, created via COMMON_DIRS); it must still be rejected
        # as a link boundary before any release content is written.
        dironly_dest = sandbox / "dironly-install"
        dironly_external = sandbox / "external-dironly"
        dironly_dest.mkdir()
        dironly_external.mkdir()
        dironly_sentinel = dironly_external / "sentinel.txt"
        dironly_sentinel.write_text("DO NOT CHANGE\n", encoding="utf-8")
        if create_dir_link(
            dironly_dest / "shared" / "rules", dironly_external
        ) is not None:
            dironly_before = sha256(dironly_sentinel)
            dironly = run_materialize(
                "personal", dironly_dest, skills_mode="copy"
            )
            if dironly.returncode == 0:
                fails.append(
                    "[link-boundary] setup accepted a directory-only public "
                    "link boundary (shared/rules)"
                )
            if (
                sorted(path.name for path in dironly_external.iterdir())
                != ["sentinel.txt"]
                or sha256(dironly_sentinel) != dironly_before
            ):
                fails.append(
                    "[link-boundary] setup wrote through a directory-only "
                    "public link boundary"
                )
            if (dironly_dest / ".aios" / "manifest.md").exists():
                fails.append(
                    "[link-boundary] setup materialized release content "
                    "before rejecting a directory-only public link boundary"
                )

        skill_dest = sandbox / "nested-skill-link-install"
        skill_external = sandbox / "external-skill"
        (skill_dest / "skills").mkdir(parents=True)
        skill_external.mkdir()
        skill_sentinel = skill_external / "SKILL.md"
        skill_sentinel.write_text(
            "---\nname: external\ndescription: Must remain external.\n---\n",
            encoding="utf-8",
        )
        if create_dir_link(
            skill_dest / "skills" / "external", skill_external
        ) is not None:
            skill_before = sha256(skill_sentinel)
            nested = run_materialize(
                "personal", skill_dest, skills_mode="copy"
            )
            if nested.returncode == 0:
                fails.append(
                    "[link-boundary] setup accepted a nested linked Skill"
                )
            if sha256(skill_sentinel) != skill_before:
                fails.append(
                    "[link-boundary] setup modified nested linked Skill data"
                )

        physical_root = sandbox / "physical-root"
        linked_root = sandbox / "linked-root"
        physical_root.mkdir()
        if create_dir_link(linked_root, physical_root) is not None:
            root_link = run_materialize(
                "personal", linked_root, skills_mode="copy"
            )
            if root_link.returncode == 0:
                fails.append(
                    "[link-boundary] setup accepted a linked destination root"
                )
            if list(physical_root.iterdir()):
                fails.append(
                    "[link-boundary] setup wrote through destination root link"
                )

        ancestor_target = sandbox / "external-ancestor"
        ancestor_link = sandbox / "linked-ancestor"
        ancestor_target.mkdir()
        if create_dir_link(ancestor_link, ancestor_target) is not None:
            ancestor = run_materialize(
                "personal",
                ancestor_link / "install",
                skills_mode="copy",
            )
            if ancestor.returncode == 0:
                fails.append(
                    "[link-boundary] setup accepted a linked destination ancestor"
                )
            if list(ancestor_target.iterdir()):
                fails.append(
                    "[link-boundary] setup wrote through destination ancestor"
                )
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
    return fails


def t_negative_validators() -> list[str]:
    """Mutate real materialized trees; each mutation must be detected."""
    fails: list[str] = []
    dest = Path(tempfile.mkdtemp(prefix="aios-neg-"))
    try:
        materialized = run_materialize("personal", dest, skills_mode="copy")
        if materialized.returncode != 0:
            return [f"[negative] fixture materialize failed: {materialized.stderr.strip()}"]
        if validate_install(dest, "personal"):
            return ["[negative] clean fixture failed validation before mutation"]

        readme = dest / "README.md"
        clean_readme = text(readme)
        readme.write_text(
            clean_readme + "\n{{AIOS_UNRESOLVED_NEGATIVE}}\n",
            encoding="utf-8",
        )
        if not any("unresolved placeholders" in failure
                   for failure in validate_install(dest, "personal")):
            fails.append("[negative] unresolved placeholder mutation was missed")
        readme.write_text(clean_readme, encoding="utf-8")

        agents = dest / "AGENTS.md"
        clean_agents = text(agents)
        agents.write_text(
            clean_agents.replace("../skills", "../../skills", 1),
            encoding="utf-8",
        )
        if not any("stale ../../skills" in failure
                   for failure in validate_install(dest, "personal")):
            fails.append("[negative] wrong Skill-link text mutation was missed")
        agents.write_text(clean_agents, encoding="utf-8")

        claude = dest / "CLAUDE.md"
        clean_claude = text(claude)
        claude.write_text(
            clean_claude.replace(
                "## 6. Knowledge Vault",
                "MIRROR-DRIFT-NEGATIVE\n\n## 6. Knowledge Vault",
                1,
            ),
            encoding="utf-8",
        )
        if not any(
            "entry mirror" in failure
            for failure in validate_install(dest, "personal")
        ):
            fails.append("[negative] one-sided entry mirror drift was missed")
        claude.write_text(clean_claude, encoding="utf-8")

        profile = dest / "private" / "memory" / "profile.md"
        clean_profile = text(profile)
        mutated_profile = clean_profile.replace(
            "../context/me.md", "../../context/me.md", 1
        )
        if mutated_profile == clean_profile:
            fails.append(
                "[negative] canonical path fixture found no ../context/me.md "
                "to mutate"
            )
        else:
            profile.write_text(mutated_profile, encoding="utf-8")
            if not any(
                "canonical path" in failure
                for failure in validate_install(dest, "personal")
            ):
                fails.append(
                    "[negative] wrong canonical context path (../../context/...) "
                    "mutation was missed"
                )
            profile.write_text(clean_profile, encoding="utf-8")

        clean_agents = text(agents)
        clean_claude = text(claude)
        mutated_agents = clean_agents.replace("`.mcp.json`", "", 1)
        mutated_claude = clean_claude.replace("`.mcp.json`", "", 1)
        if mutated_agents == clean_agents or mutated_claude == clean_claude:
            fails.append(
                "[negative] native-control removal fixture found no "
                "`.mcp.json` token to remove"
            )
        else:
            agents.write_text(mutated_agents, encoding="utf-8")
            claude.write_text(mutated_claude, encoding="utf-8")
            mutated_fails = validate_install(dest, "personal")
            if any("entry mirror" in failure for failure in mutated_fails):
                fails.append(
                    "[negative] synchronized native-control removal broke "
                    "mirror parity unexpectedly"
                )
            if not any(
                "missing native-control items" in failure
                for failure in mutated_fails
            ):
                fails.append(
                    "[negative] synchronized native-control removal from both "
                    "entries was not detected by completeness validation"
                )
            agents.write_text(clean_agents, encoding="utf-8")
            claude.write_text(clean_claude, encoding="utf-8")

        clean_agents = text(agents)
        clean_claude = text(claude)
        mutated_agents_ext = clean_agents.replace("`.webp`", "", 1)
        mutated_claude_ext = clean_claude.replace("`.webp`", "", 1)
        if mutated_agents_ext == clean_agents or mutated_claude_ext == clean_claude:
            fails.append(
                "[negative] allowlist-extension removal fixture found no "
                "`.webp` token to remove"
            )
        else:
            agents.write_text(mutated_agents_ext, encoding="utf-8")
            claude.write_text(mutated_claude_ext, encoding="utf-8")
            mutated_fails = validate_install(dest, "personal")
            if any("entry mirror" in failure for failure in mutated_fails):
                fails.append(
                    "[negative] synchronized allowlist-extension removal broke "
                    "mirror parity unexpectedly"
                )
            if not any(
                "allowlist extension set mismatch" in failure
                for failure in mutated_fails
            ):
                fails.append(
                    "[negative] removing an allowed extension from both entries "
                    "was not detected by allowlist completeness validation"
                )
            agents.write_text(clean_agents, encoding="utf-8")
            claude.write_text(clean_claude, encoding="utf-8")

        clean_agents = text(agents)
        clean_claude = text(claude)
        mutated_agents_gate = clean_agents
        mutated_claude_gate = clean_claude
        for token in GATE_TOKENS:
            mutated_agents_gate = mutated_agents_gate.replace(token, "", 1)
            mutated_claude_gate = mutated_claude_gate.replace(token, "", 1)
        if mutated_agents_gate == clean_agents or mutated_claude_gate == clean_claude:
            fails.append(
                "[negative] file-output Gate removal fixture found no Gate "
                "tokens to remove"
            )
        else:
            agents.write_text(mutated_agents_gate, encoding="utf-8")
            claude.write_text(mutated_claude_gate, encoding="utf-8")
            mutated_fails = validate_install(dest, "personal")
            if any("entry mirror" in failure for failure in mutated_fails):
                fails.append(
                    "[negative] synchronized file-output Gate removal broke "
                    "mirror parity unexpectedly"
                )
            if not any(
                "file-output authorization Gate token" in failure
                for failure in mutated_fails
            ):
                fails.append(
                    "[negative] removing the file-output authorization Gate "
                    "from both entries was not detected by the independent "
                    "Gate validator"
                )
            agents.write_text(clean_agents, encoding="utf-8")
            claude.write_text(clean_claude, encoding="utf-8")

        manifest = dest / ".aios" / "manifest.md"
        clean_manifest = text(manifest)
        manifest.write_text(
            clean_manifest.replace(
                "|---|---|---|---|",
                "|---|---|---|---|\n"
                "| missing-skill | skills/missing-skill | installed | negative |",
                1,
            ),
            encoding="utf-8",
        )
        if not any("missing-skill" in failure
                   for failure in validate_install(dest, "personal")):
            fails.append("[negative] missing installed SKILL.md was not detected")
        manifest.write_text(clean_manifest, encoding="utf-8")

        rogue = (
            dest / ".agents" / "skills" / "rogue-copy" / "SKILL.md"
        )
        rogue.parent.mkdir(parents=True)
        rogue.write_text(
            "---\nname: rogue-copy\ndescription: Divergent copy fixture.\n---\n",
            encoding="utf-8",
        )
        divergent = run_materialize(
            "personal", dest, skills_mode="copy"
        )
        if divergent.returncode == 0:
            fails.append(
                "[negative] divergent copy-mode Skill entry was accepted"
            )
        if (
            dest
            / ".claude"
            / "skills"
            / "rogue-copy"
            / "SKILL.md"
        ).exists():
            fails.append(
                "[negative] divergent copy was propagated without consent"
            )
        shutil.rmtree(rogue.parent)

        reserved = Path(tempfile.mkdtemp(prefix="aios-edition-var-"))
        try:
            cmd = [
                sys.executable, str(MATERIALIZE),
                "--edition", "personal", "--dest", str(reserved),
                "--skills-mode", "copy", *STD_VARS,
                "--var", "AIOS_EDITION=company",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                fails.append(
                    f"[negative] reserved edition fixture failed: {result.stderr}"
                )
            elif parse_kv(
                reserved / ".aios" / "edition.md", "edition"
            ) != "personal":
                fails.append("[negative] --var overrode reserved AIOS_EDITION")
        finally:
            shutil.rmtree(reserved, ignore_errors=True)

        mixed = Path(tempfile.mkdtemp(prefix="aios-edition-mix-"))
        try:
            personal = run_materialize(
                "personal", mixed, skills_mode="copy"
            )
            if personal.returncode != 0:
                fails.append(
                    f"[negative] edition-mix fixture failed: {personal.stderr}"
                )
            else:
                manifest = mixed / ".aios" / "manifest.md"
                manifest_before = sha256(manifest)
                company = run_materialize(
                    "company", mixed, upgrade=True, skills_mode="copy"
                )
                if company.returncode == 0:
                    fails.append(
                        "[negative] materializer mixed company over personal"
                    )
                if sha256(manifest) != manifest_before:
                    fails.append(
                        "[negative] rejected edition mix changed manifest"
                    )
                if (
                    mixed
                    / "private"
                    / "context"
                    / "work"
                    / "my-role-and-responsibilities.md"
                ).exists():
                    fails.append(
                        "[negative] rejected edition mix wrote company context"
                    )
        finally:
            shutil.rmtree(mixed, ignore_errors=True)

        # NOTE: this does not construct a tree_signature hash collision (root
        # and the copy-mode entries have different file counts, so their
        # digests differ for that reason alone); it only proves that a
        # copy-mode Skill entry whose file set/content diverges from the root
        # skills/ tree is rejected, not silently accepted as in sync.
        divergent_copy_tree = Path(tempfile.mkdtemp(prefix="aios-copy-divergence-"))
        try:
            root_skills = divergent_copy_tree / "skills"
            root_skills.mkdir(parents=True)
            (root_skills / "a").write_bytes(b"")
            (root_skills / "b").write_bytes(b"X")
            for entry in (
                divergent_copy_tree / ".agents" / "skills",
                divergent_copy_tree / ".claude" / "skills",
            ):
                entry.mkdir(parents=True)
                (entry / "a").write_bytes(b"F\0b\0X")
            result = run_materialize(
                "personal", divergent_copy_tree, skills_mode="copy"
            )
            if result.returncode == 0:
                fails.append(
                    "[negative] divergent copy-mode Skill tree content was "
                    "accepted"
                )
        finally:
            shutil.rmtree(divergent_copy_tree, ignore_errors=True)
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return fails


def t_native_quarantine_docs() -> list[str]:
    """Synchronized coverage: the source-tree reference docs (not the
    materialized output) must each still enumerate the complete native-control
    artifact minimum set, independent of materialize.py. The canonical
    references/entry-policy.md must additionally carry the exact allowlist
    extension set, size limits, precedence, and rejection semantics."""
    fails: list[str] = []
    for label, path in REFERENCE_DOC_PATHS.items():
        if not path.is_file():
            fails.append(f"[doc-quarantine] missing reference file for {label}: {path}")
            continue
        content = text(path)
        missing = missing_native_artifacts(content)
        if missing:
            fails.append(f"[doc-quarantine] {label} missing native-control items {missing}")
        if label == "references/entry-policy.md":
            fails.extend(
                f"[doc-quarantine] {failure}"
                for failure in entry_policy_failures(label, content)
            )
            fails.extend(
                f"[doc-quarantine] {failure}"
                for failure in gate_failures(label, content)
            )
    return fails


CASES = [
    ("materialize personal", lambda: t_materialize_edition("personal", GOLDEN_PERSONAL)),
    ("materialize company", lambda: t_materialize_edition("company", GOLDEN_COMPANY)),
    ("idempotent + sentinel", t_idempotent_and_sentinel),
    ("safe 0.1->0.2 upgrade", t_safe_upgrade),
    ("edited-proposal sentinel", t_edited_proposal_sentinel),
    ("git check-ignore", t_git_check_ignore),
    ("link + copy mode", t_link_and_copy_mode),
    ("copy-mode finalize/rerun (real order)", t_copy_finalize_sync),
    ("installed vs missing skill", t_installed_vs_missing_skill),
    ("link/Junction trust boundary", t_link_boundary_safety),
    ("native-control doc coverage", t_native_quarantine_docs),
    ("negative validators", t_negative_validators),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="AIOS materializer black-box smoke test.")
    parser.add_argument("--all", action="store_true", help="Run every case (default).")
    parser.parse_args(argv)

    if not MATERIALIZE.exists():
        print(f"FATAL: materializer not found at {MATERIALIZE}", file=sys.stderr)
        return 2
    actual_template_version = template_version()
    if actual_template_version != EXPECTED_VERSION:
        print(
            f"FATAL: release template version {actual_template_version}, "
            f"expected hard-coded {EXPECTED_VERSION}",
            file=sys.stderr,
        )
        return 2

    total_fails: list[str] = []
    for name, fn in CASES:
        print(f"[RUN] {name}")
        fails = fn()
        if fails:
            for f in fails:
                print(f"  [FAIL] {f}")
            total_fails.extend(fails)
        else:
            print(f"  [PASS] {name}")

    print("\n" + "=" * 48)
    if total_fails:
        print(f"SMOKE TEST FAILED: {len(total_fails)} failure(s)")
        return 1
    print(f"SMOKE TEST PASSED: {len(CASES)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
