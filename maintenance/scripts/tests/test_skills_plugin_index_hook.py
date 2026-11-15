import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import repo_git
from precommit.skills_plugin_index import validate
from plugin_meta.generate.generate_skills_plugin_index import BEGIN, END, render
from plugin_meta.util.ai_tools_config import load_tool


class HookTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skills = self.root / "skills"
        self.skills.mkdir()
        for repo in (self.root, self.skills):
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.email", "test@example.invalid")
            self.git(repo, "config", "user.name", "Test")
        (self.root / ".gitmodules").write_text(
            '[submodule "skills"]\n path = skills\n url = ../skills\n'
        )
        (self.root / "registry").mkdir()
        (self.root / "registry/ai-tools.yaml").write_text(
            "tools:\n  claude-code:\n    skills_plugin_index:\n      root: skills/plugins\n"
            "      output_path: skills/README.md\n    plugins:\n      - path: skills/plugins/a\n"
        )
        manifest = self.skills / "plugins/a/.claude-plugin/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"name": "a", "description": "a"}))
        (self.skills / "README.md").write_text(f"{BEGIN}\n{END}\n")
        _, content = render(
            self.root, load_tool("claude-code", self.root / "registry/ai-tools.yaml")
        )
        (self.skills / "README.md").write_text(content)
        self.git(self.skills, "add", ".")
        self.git(self.skills, "commit", "-qm", "initial")
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-qm", "initial")

    def git(self, repo, *args):
        return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)

    def test_readme_and_partial_stage(self):
        readme = self.skills / "README.md"
        readme.write_text(readme.read_text() + "extra\n")
        self.git(self.skills, "add", "README.md")
        validate(self.root, "skills")
        readme.write_text(readme.read_text() + "unstaged\n")
        with self.assertRaisesRegex(ValueError, "unstaged"):
            validate(self.root, "skills")

    def test_stale_and_deleted_manifest(self):
        manifest = self.skills / "plugins/a/.claude-plugin/plugin.json"
        manifest.write_text(json.dumps({"name": "a", "description": "changed"}))
        self.git(self.skills, "add", ".")
        with self.assertRaisesRegex(ValueError, "stale"):
            validate(self.root, "skills")
        manifest.unlink()
        self.git(self.skills, "add", "-u")
        self.assertIn(
            "plugins/a/.claude-plugin/plugin.json",
            repo_git._staged_in(self.skills, include_deleted=True),
        )
        self.assertNotIn("plugins/a/.claude-plugin/plugin.json", repo_git._staged_in(self.skills))
        with self.assertRaises(ValueError):
            validate(self.root, "skills")

    def test_umbrella_rejects_uncommitted_skills(self):
        self.git(self.root, "add", "registry/ai-tools.yaml")
        registry = self.root / "registry/ai-tools.yaml"
        registry.write_text(registry.read_text() + "\n")
        self.git(self.root, "add", "registry/ai-tools.yaml")
        validate(self.root, "umbrella")
        readme = self.skills / "README.md"
        readme.write_text(readme.read_text() + "change\n")
        self.git(self.skills, "add", "README.md")
        with self.assertRaisesRegex(ValueError, "commit skills"):
            validate(self.root, "umbrella")

    def test_git_commit_hook_rejects_stale_readme(self):
        hook = self.skills / ".git/hooks/pre-commit"
        scripts = Path(__file__).resolve().parents[1]
        hook.write_text(
            f"#!{sys.executable}\nimport sys\nsys.path.insert(0, {str(scripts)!r})\n"
            f"from pathlib import Path\nfrom precommit.skills_plugin_index import validate\n"
            f'validate(Path({str(self.root)!r}), "skills")\n'
        )
        hook.chmod(0o755)
        manifest = self.skills / "plugins/a/.claude-plugin/plugin.json"
        manifest.write_text(json.dumps({"name": "a", "description": "changed"}))
        self.git(self.skills, "add", ".")
        result = subprocess.run(
            ["git", "commit", "-qm", "stale"], cwd=self.skills, capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale", result.stderr)
