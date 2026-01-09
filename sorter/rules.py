from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuleSet:
    """
    category -> set of extensions (lowercase, including leading dot).
    """
    categories: dict[str, set[str]]
    default_category: str = "Other"

    def category_for_path(self, path: Path) -> str:
        ext = path.suffix.lower()
        for category, exts in self.categories.items():
            if ext in exts:
                return category
        return self.default_category


DEFAULT_RULES = RuleSet(
    categories={
        "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".svg"},
        "Videos": {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".m4v"},
        "Audio": {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"},
        "Documents": {
            ".pdf", ".doc", ".docx", ".txt", ".rtf", ".md",
            ".xls", ".xlsx", ".csv",
            ".ppt", ".pptx",
        },
        "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
        "Code": {
            ".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yml", ".yaml",
            ".sql", ".php", ".cs", ".cpp", ".c", ".h", ".java",
        },
    },
    default_category="Other",
)
