from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class MoveRecord:
    src: str
    dst: str


@dataclass(frozen=True)
class SortLog:
    created_utc: str
    root: str
    records: list[MoveRecord]


def write_sort_log(log_path: Path, root: Path, records: list[MoveRecord]) -> None:
    payload = SortLog(
        created_utc=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        root=str(root),
        records=records,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "created_utc": payload.created_utc,
                "root": payload.root,
                "records": [asdict(r) for r in payload.records],
            },
            f,
            indent=2,
        )


def read_sort_log(log_path: Path) -> SortLog:
    with log_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    records = [MoveRecord(**r) for r in data.get("records", [])]
    return SortLog(
        created_utc=str(data.get("created_utc", "")),
        root=str(data.get("root", "")),
        records=records,
    )
