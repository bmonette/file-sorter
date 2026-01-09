from pathlib import Path

from sorter.engine import SortOptions, build_move_plan, apply_move_plan, undo_from_log


def _touch(path: Path, content: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_build_plan_apply_and_undo(tmp_path: Path):
    root = tmp_path / "SortMe"
    root.mkdir()

    # Create a small mixed set
    _touch(root / "pic.jpg")
    _touch(root / "song.mp3")
    _touch(root / "doc.pdf")
    _touch(root / "sheet.xlsx")
    _touch(root / "archive.zip")

    log_path = root / "_sort_logs" / "last_sort.json"

    plan = build_move_plan(root, SortOptions(recursive=True, include_hidden=False))
    assert len(plan) == 5

    records = apply_move_plan(root=root, plan=plan, log_path=log_path)
    assert len(records) == 5
    assert log_path.exists()

    # Verify destinations exist
    assert (root / "Images" / "pic.jpg").exists()
    assert (root / "Audio" / "song.mp3").exists()
    assert (root / "Documents" / "doc.pdf").exists()
    assert (root / "Spreadsheets" / "sheet.xlsx").exists()
    assert (root / "Archives" / "archive.zip").exists()

    # Undo should restore to root
    restored = undo_from_log(log_path)
    assert restored == 5
    assert (root / "pic.jpg").exists()
    assert (root / "song.mp3").exists()
    assert (root / "doc.pdf").exists()
    assert (root / "sheet.xlsx").exists()
    assert (root / "archive.zip").exists()


def test_collision_renaming(tmp_path: Path):
    root = tmp_path / "SortMe"
    root.mkdir()

    # Existing destination file
    images = root / "Images"
    images.mkdir()
    _touch(images / "same.jpg", b"DEST")

    # Source file that would collide
    _touch(root / "same.jpg", b"SRC")

    log_path = root / "_sort_logs" / "last_sort.json"

    plan = build_move_plan(root, SortOptions())
    # only the root same.jpg should be planned (the one already in Images should be skipped)
    assert len(plan) == 1

    apply_move_plan(root=root, plan=plan, log_path=log_path)

    assert (images / "same.jpg").read_bytes() == b"DEST"
    assert (images / "same (2).jpg").read_bytes() == b"SRC"


def test_skip_already_sorted_category_folder(tmp_path: Path):
    root = tmp_path / "SortMe"
    root.mkdir()

    # Put a file already in a category folder
    images = root / "Images"
    images.mkdir()
    _touch(images / "already.jpg")

    plan = build_move_plan(root, SortOptions())
    assert len(plan) == 0
