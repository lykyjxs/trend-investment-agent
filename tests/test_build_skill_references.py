from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "build_skill_references.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_skill_references", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BuildSkillReferencesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MODULE_PATH.is_file(), "reference builder must exist")
        self.module = load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.source_images = self.root / "source-images"
        self.destination = self.root / "references"
        self.source_images.mkdir()

    def write_source_note(self) -> Path:
        note = self.root / "course.md"
        note.write_text(
            "# 完整课程\n\n## NVIDIA 案例\n\n"
            "![[Pasted image selected.png]]\n\n"
            "保留这段结论。\n\n"
            "![[Pasted image omitted.png]]\n",
            encoding="utf-8",
        )
        return note

    def test_preserves_text_and_rewrites_image_embeds(self) -> None:
        note = self.write_source_note()
        (self.source_images / "Pasted image selected.png").write_bytes(b"selected")

        self.module.build_course_reference(
            note,
            self.source_images,
            self.destination,
            ("Pasted image selected.png",),
        )

        generated = (self.destination / "course-notes.md").read_text(encoding="utf-8")
        self.assertIn("# 完整课程", generated)
        self.assertIn("## NVIDIA 案例", generated)
        self.assertIn("保留这段结论。", generated)
        self.assertIn(
            "![案例图](images/Pasted%20image%20selected.png)",
            generated,
        )
        self.assertIn(
            "> 原图文件：Pasted image omitted.png（未随 skill 打包）",
            generated,
        )
        self.assertNotIn("![[", generated)

    def test_copies_only_selected_images_and_removes_stale_generated_files(self) -> None:
        note = self.write_source_note()
        (self.source_images / "Pasted image selected.png").write_bytes(b"selected")
        (self.source_images / "Pasted image omitted.png").write_bytes(b"omitted")
        images = self.destination / "images"
        images.mkdir(parents=True)
        (images / "stale.png").write_bytes(b"stale")

        self.module.build_course_reference(
            note,
            self.source_images,
            self.destination,
            ("Pasted image selected.png",),
        )

        self.assertEqual(
            ["Pasted image selected.png"],
            sorted(path.name for path in images.iterdir()),
        )
        self.assertEqual(b"selected", (images / "Pasted image selected.png").read_bytes())

    def test_fails_before_output_when_a_selected_image_is_missing(self) -> None:
        note = self.write_source_note()

        with self.assertRaisesRegex(FileNotFoundError, "Pasted image selected.png"):
            self.module.build_course_reference(
                note,
                self.source_images,
                self.destination,
                ("Pasted image selected.png",),
            )

        self.assertFalse((self.destination / "course-notes.md").exists())


if __name__ == "__main__":
    unittest.main()
