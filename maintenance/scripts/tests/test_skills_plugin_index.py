import json
import tempfile
import unittest
from pathlib import Path

from plugin_meta.generate.generate_skills_plugin_index import BEGIN, END, render


class SkillsPluginIndexTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "skills/plugins").mkdir(parents=True)
        self.readme = self.root / "skills/README.md"
        self.readme.write_text(f"before\n{BEGIN}\nold\n{END}\nafter\n", encoding="utf-8")
        self.tool = {
            "skills_plugin_index": {"root": "skills/plugins", "output_path": "skills/README.md"},
            "plugins": [{"path": "tools/_plugin/ignored"}],
        }

    def plugin(self, directory, name, description):
        manifest = self.root / "skills/plugins" / directory / ".claude-plugin/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps({"name": name, "description": description}), encoding="utf-8"
        )
        self.tool["plugins"].append({"path": f"skills/plugins/{directory}"})
        return manifest

    def test_render_order_escaping_and_idempotence(self):
        self.plugin("z space", "z", "last")
        self.plugin("a", "a[name]", "one\n*two*")
        _, result = render(self.root, self.tool)
        self.assertIn("[a\\[name\\]](plugins/a/): one \\*two\\*", result)
        self.assertIn("[z](plugins/z%20space/): last", result)
        self.assertLess(result.index("[a\\[name"), result.index("[z]"))
        self.assertTrue(result.startswith("before\n"))
        self.assertTrue(result.endswith("\nafter\n"))
        self.readme.write_text(result, encoding="utf-8")
        self.assertEqual(render(self.root, self.tool)[1], result)

    def test_registration_and_manifest_errors(self):
        manifest = self.plugin("a", "a", "description")
        (self.root / "skills/plugins/unregistered").mkdir()
        with self.assertRaisesRegex(ValueError, "unregistered"):
            render(self.root, self.tool)
        (self.root / "skills/plugins/unregistered").rmdir()
        manifest.write_text("{", encoding="utf-8")
        with self.assertRaises(ValueError):
            render(self.root, self.tool)
        manifest.unlink()
        with self.assertRaisesRegex(ValueError, "plugin.json"):
            render(self.root, self.tool)

    def test_crlf_entities_and_link(self):
        manifest = self.plugin("a", "a", "&amp;")
        self.readme.write_bytes(f"before\r\n{BEGIN}\r\nold\r\n{END}\r\nafter\r\n".encode())
        _, result = render(self.root, self.tool)
        self.assertIn(r"\&amp;", result)
        self.assertTrue(result.startswith("before\r\n"))
        self.assertTrue(result.endswith("\r\nafter\r\n"))
        manifest.unlink()
        manifest.symlink_to(self.readme)
        with self.assertRaisesRegex(ValueError, "link"):
            render(self.root, self.tool)

    def test_bad_markers(self):
        for text in (BEGIN, f"{END}\n{BEGIN}", f"{BEGIN}\n{BEGIN}\n{END}"):
            with self.subTest(text=text):
                self.readme.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "markers"):
                    render(self.root, self.tool)


if __name__ == "__main__":
    unittest.main()
