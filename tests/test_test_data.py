from pathlib import Path

TEST_DATA = Path(__file__).resolve().parent.parent / "test_data"

EXPECTED_FILES = [
    "norwegian_lecture.pdf",
    "english_lecture.pdf",
    "mixed_language_notes.txt",
    "scanned_lecture.pdf",
]


def test_sample_files_exist_and_are_not_empty():
    for name in EXPECTED_FILES:
        path = TEST_DATA / name
        assert path.is_file(), f"missing {path}"
        assert path.stat().st_size > 0, f"empty {path}"
