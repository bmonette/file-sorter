from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .log import MoveRecord, write_sort_log, read_sort_log
from .rules import RuleSet, DEFAULT_RULES


@dataclass(frozen=True)
class MovePlanItem:
    src: Path
    dst: Path
    category: str


@dataclass(frozen=True)
class SortOptions:
    recursive: bool = True
    include_hidden: bool = False
    rules: RuleSet = DEFAULT_RULES


def _is_hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    if os.name == "nt":
        try:
            import ctypes  # noqa: F401
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs == -1:
                return False
            FILE_ATTRIBUTE_HIDDEN = 0x2
            return bool(attrs & FILE_ATTRIBUTE_HIDDEN)
        except Exception:
            return False
    return False


def _unique_destination(dst: Path) -> Path:
    if not dst.exists():
        return dst

    stem = dst.stem
    suffix = dst.suffix
    parent = dst.parent

    i = 2
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def build_move_plan(root: Path, options: SortOptions) -> list[MovePlanItem]:
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Root folder does not exist or is not a directory: {root}")

    known_categories = set(options.rules.categories.keys()) | {options.rules.default_category}

    items: list[MovePlanItem] = []

    iterator = root.rglob("*") if options.recursive else root.glob("*")
    for p in iterator:
        if not p.is_file():
            continue

        if not options.include_hidden and _is_hidden(p):
            continue

        # If already inside a known category folder, skip to avoid nesting
        try:
            rel = p.relative_to(root)
            if rel.parts and rel.parts[0] in known_categories:
                continue
        except Exception:
            pass

        category = options.rules.category_for_path(p)
        target_dir = root / category
        target_dst = target_dir / p.name

        if p.resolve() == target_dst.resolve():
            continue

        items.append(MovePlanItem(src=p, dst=target_dst, category=category))

    items.sort(key=lambda x: (x.category, str(x.src).lower()))
    return items


def apply_move_plan(
    root: Path,
    plan: list[MovePlanItem],
    log_path: Path,
    on_progress: Callable[[int, int, MovePlanItem], None] | None = None,
) -> list[MoveRecord]:
    root = root.resolve()
    records: list[MoveRecord] = []
    total = len(plan)

    for idx, item in enumerate(plan, start=1):
        if on_progress:
            on_progress(idx, total, item)

        src = item.src.resolve()

        dst_dir = (root / item.category).resolve()
        if root not in dst_dir.parents and dst_dir != root:
            raise RuntimeError("Safety check failed: destination outside root")

        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = _unique_destination((dst_dir / item.dst.name).resolve())

        if not src.exists():
            continue

        shutil.move(str(src), str(dst))
        records.append(MoveRecord(src=str(src), dst=str(dst)))

    write_sort_log(log_path=log_path, root=root, records=records)
    return records


def undo_from_log(log_path: Path) -> int:
    log = read_sort_log(log_path)
    restored = 0

    for rec in reversed(log.records):
        src = Path(rec.src)
        dst = Path(rec.dst)

        if dst.exists():
            src.parent.mkdir(parents=True, exist_ok=True)
            final_src = src if not src.exists() else _unique_destination(src)
            shutil.move(str(dst), str(final_src))
            restored += 1

    return restored
