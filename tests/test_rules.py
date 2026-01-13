from pathlib import Path
from sorter.rules import DEFAULT_RULES


def test_spreadsheets_category():
    assert DEFAULT_RULES.category_for_path(Path("a.xls")) == "Spreadsheets"
    assert DEFAULT_RULES.category_for_path(Path("a.xlsx")) == "Spreadsheets"
    assert DEFAULT_RULES.category_for_path(Path("a.csv")) == "Spreadsheets"


def test_documents_category():
    assert DEFAULT_RULES.category_for_path(Path("a.pdf")) == "Documents"
    assert DEFAULT_RULES.category_for_path(Path("a.docx")) == "Documents"
    assert DEFAULT_RULES.category_for_path(Path("a.pptx")) == "Documents"


def test_other_category_for_unknown_extension():
    assert DEFAULT_RULES.category_for_path(Path("a.unknownext")) == "Other"
