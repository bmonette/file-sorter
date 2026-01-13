# File Sorter (Windows)

A safe, fast Windows desktop app to organize messy folders by file type — with **preview, progress, and undo**.

This tool was built as a practical, production-ready utility and is actively used to support a **Fiverr bulk file organization / renaming service**.

---

## ✨ Features

- 📂 Sort files by category (Images, Videos, Audio, Documents, Spreadsheets, Archives, Code, Other)
- 👀 **Preview mode** — see exactly what will move before anything happens
- 🔁 **Undo last sort** using an automatic log
- 📊 **Progress bar** for large folders
- 🛡️ Safe collision handling (no overwrites)
- 🧠 Skips already-sorted category folders to avoid nesting
- 🪟 Windows-friendly Tkinter GUI (no terminal required)

---

## 🗂 Categories

| Category        | Extensions (examples) |
|-----------------|-----------------------|
| Images          | .jpg, .png, .gif, .webp |
| Videos          | .mp4, .mkv, .mov |
| Audio           | .mp3, .wav, .flac |
| Documents       | .pdf, .docx, .txt |
| **Spreadsheets**| .xls, .xlsx, .csv |
| Archives        | .zip, .rar, .7z |
| Code            | .py, .js, .html |
| Other           | everything else |

---

## 🚀 How It Works

1. Select a folder
2. Click **Preview** to see planned moves
3. Click **Sort** to move files into category folders
4. Use **Undo Last Sort** if you want to revert

All moves are logged to:
```
_sort_logs/last_sort.json
```

---

## 🧪 Tests

Core logic is covered by automated tests using **pytest**:

```bash
python -m pytest
```

Tests cover:
- Rule classification (including Spreadsheets)
- Move planning
- Collision renaming
- Apply + undo behavior

---

## 📦 Packaging (Windows)

To build a standalone `.exe`:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name FileSorter app.py
```

The executable will be created in:
```
dist/FileSorter.exe
```

---

## ⚠️ Safety Notes

- Files are **moved**, not copied
- Nothing outside the selected folder is touched
- Existing files are never overwritten
- Undo restores files when possible

Still, always test on a **copy** of important data first.

---

## 🧑‍💻 Author Notes

This app was built with a **ship-first mindset**:
- practical
- predictable
- testable
- safe

It is used in real-world scenarios to handle large, messy folders quickly and reliably.

---

## 📄 License

Private / internal use.  
Not distributed as open source.
