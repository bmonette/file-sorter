from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from sorter import SortOptions, build_move_plan, apply_move_plan, undo_from_log


class FileSorterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("File Sorter")
        self.minsize(980, 600)

        # State
        self.folder_var = tk.StringVar(value=str(Path.home()))
        self.recursive_var = tk.BooleanVar(value=True)
        self.hidden_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Select a folder, then click Preview.")

        self._plan = []  # list[MovePlanItem]
        self._log_path: Path | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        # ===== Top: folder + options =====
        top = ttk.Frame(root)
        top.pack(fill="x")

        ttk.Label(top, text="Folder:").grid(row=0, column=0, sticky="w")
        folder_entry = ttk.Entry(top, textvariable=self.folder_var)
        folder_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))

        browse_btn = ttk.Button(top, text="Browse…", command=self._on_browse)
        browse_btn.grid(row=0, column=2, sticky="e")

        opts = ttk.Frame(root)
        opts.pack(fill="x", pady=(10, 6))

        ttk.Checkbutton(opts, text="Recursive (include subfolders)", variable=self.recursive_var).pack(
            side="left"
        )
        ttk.Checkbutton(opts, text="Include hidden files", variable=self.hidden_var).pack(
            side="left", padx=(16, 0)
        )

        # ===== Buttons =====
        btns = ttk.Frame(root)
        btns.pack(fill="x", pady=(6, 10))

        self.preview_btn = ttk.Button(btns, text="Preview", command=self._on_preview)
        self.preview_btn.pack(side="left")

        self.sort_btn = ttk.Button(btns, text="Sort (Move Files)", command=self._on_sort, state="disabled")
        self.sort_btn.pack(side="left", padx=(10, 0))

        self.undo_btn = ttk.Button(btns, text="Undo Last Sort", command=self._on_undo, state="disabled")
        self.undo_btn.pack(side="left", padx=(10, 0))

        # ===== Preview table =====
        table_frame = ttk.Frame(root)
        table_frame.pack(fill="both", expand=True)

        columns = ("category", "src", "dst")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("category", text="Category")
        self.tree.heading("src", text="From")
        self.tree.heading("dst", text="To")

        self.tree.column("category", width=110, anchor="w", stretch=False)
        self.tree.column("src", width=420, anchor="w")
        self.tree.column("dst", width=420, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # ===== Status bar =====
        status = ttk.Label(root, textvariable=self.status_var, anchor="w")
        status.pack(fill="x", pady=(10, 0))

        # grid config for top row
        top.columnconfigure(1, weight=1)

    def _set_busy(self, busy: bool, status: str | None = None) -> None:
        if status is not None:
            self.status_var.set(status)

        state = "disabled" if busy else "normal"
        self.preview_btn.config(state=state)
        # Sort and Undo depend on state; handle separately after operations

    def _clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _on_browse(self) -> None:
        path = filedialog.askdirectory(title="Select a folder to sort")
        if path:
            self.folder_var.set(path)
            self.status_var.set("Folder selected. Click Preview to see planned moves.")
            self._plan = []
            self._log_path = None
            self._clear_table()
            self.sort_btn.config(state="disabled")
            self.undo_btn.config(state="disabled")

    def _get_sort_options(self) -> SortOptions:
        return SortOptions(
            recursive=self.recursive_var.get(),
            include_hidden=self.hidden_var.get(),
        )

    def _compute_log_path(self, root: Path) -> Path:
        return root / "_sort_logs" / "last_sort.json"

    def _on_preview(self) -> None:
        root = Path(self.folder_var.get()).expanduser()

        def work():
            try:
                self._set_busy(True, "Building preview…")
                plan = build_move_plan(root, self._get_sort_options())
                log_path = self._compute_log_path(root)

                self.after(0, lambda: self._show_preview(root, plan, log_path))
            except Exception as e:
                self.after(0, lambda: self._show_error("Preview failed", e))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=work, daemon=True).start()

    def _show_preview(self, root: Path, plan, log_path: Path) -> None:
        self._plan = plan
        self._log_path = log_path

        self._clear_table()
        for item in plan:
            self.tree.insert(
                "",
                "end",
                values=(item.category, str(item.src), str(item.dst)),
            )

        if len(plan) == 0:
            self.status_var.set("No moves planned. (Folder may already be sorted, empty, or excluded by options.)")
            self.sort_btn.config(state="disabled")
        else:
            self.status_var.set(f"Planned moves: {len(plan)}. Click Sort to move files.")
            self.sort_btn.config(state="normal")

        # Undo available if a prior log exists
        self.undo_btn.config(state="normal" if log_path.exists() else "disabled")

    def _on_sort(self) -> None:
        if not self._plan:
            messagebox.showinfo("Nothing to do", "No planned moves. Click Preview first.")
            return

        root = Path(self.folder_var.get()).expanduser()
        log_path = self._log_path or self._compute_log_path(root)

        if not messagebox.askyesno(
            "Confirm Sort",
            f"This will MOVE {len(self._plan)} files into category folders inside:\n\n{root}\n\nContinue?",
        ):
            return

        def work():
            try:
                self._set_busy(True, "Sorting (moving files)…")
                records = apply_move_plan(root=root, plan=self._plan, log_path=log_path)

                self.after(0, lambda: self._after_sort(root, log_path, len(records)))
            except Exception as e:
                self.after(0, lambda: self._show_error("Sort failed", e))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=work, daemon=True).start()

    def _after_sort(self, root: Path, log_path: Path, moved_count: int) -> None:
        self.status_var.set(f"Moved {moved_count} files. Log saved: {log_path}")
        self.undo_btn.config(state="normal")
        # Refresh preview so table reflects new state
        self._plan = []
        self.sort_btn.config(state="disabled")
        self._clear_table()

    def _on_undo(self) -> None:
        root = Path(self.folder_var.get()).expanduser()
        log_path = self._log_path or self._compute_log_path(root)

        if not log_path.exists():
            messagebox.showinfo("No log found", "No previous sort log found to undo.")
            self.undo_btn.config(state="disabled")
            return

        if not messagebox.askyesno(
            "Confirm Undo",
            f"This will undo the last sort using:\n\n{log_path}\n\nContinue?",
        ):
            return

        def work():
            try:
                self._set_busy(True, "Undoing last sort…")
                restored = undo_from_log(log_path)

                self.after(0, lambda: self._after_undo(log_path, restored))
            except Exception as e:
                self.after(0, lambda: self._show_error("Undo failed", e))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=work, daemon=True).start()

    def _after_undo(self, log_path: Path, restored: int) -> None:
        self.status_var.set(f"Restored {restored} files. (Log kept at {log_path})")
        # After undo, preview likely useful again
        self._plan = []
        self.sort_btn.config(state="disabled")
        self._clear_table()

    def _show_error(self, title: str, exc: Exception) -> None:
        self.status_var.set(f"{title}: {exc}")
        messagebox.showerror(title, str(exc))


if __name__ == "__main__":
    app = FileSorterApp()
    app.mainloop()
