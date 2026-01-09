from pathlib import Path

from sorter import SortOptions, build_move_plan, apply_move_plan, undo_from_log


def main():
    # Use a SMALL test folder first.
    root = Path(r"C:\Temp\SortMe")
    log_path = root / "_sort_logs" / "last_sort.json"

    options = SortOptions(recursive=True, include_hidden=False)

    plan = build_move_plan(root, options)
    print(f"Planned moves: {len(plan)}")
    for item in plan[:30]:
        print(f"[{item.category}] {item.src} -> {item.dst}")

    if plan:
        records = apply_move_plan(root=root, plan=plan, log_path=log_path)
        print(f"\nMoved: {len(records)} files")
        print(f"Log saved to: {log_path}")

        # Uncomment to undo immediately:
        # restored = undo_from_log(log_path)
        # print(f"Restored: {restored}")


if __name__ == "__main__":
    main()
