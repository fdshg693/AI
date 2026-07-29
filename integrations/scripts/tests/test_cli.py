from __future__ import annotations

from pathlib import Path

import pytest

from skill_deploy.cli import build_parser


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def make_skill(repo_root: Path, relative: str) -> Path:
    path = repo_root / relative
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text("dummy", encoding="utf-8")
    return path


def run_cli(argv: list[str]):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def setup_basic_config(config_dir: Path, repo_root: Path) -> None:
    make_skill(repo_root, "plugins/skills/foo")
    make_skill(repo_root, "plugins/skills/bar")
    write(
        config_dir / "case.yaml",
        """
        sets:
          all-plugins:
            - plugins/skills/*
        """,
    )
    write(
        config_dir / "targets.yaml",
        """
        targets:
          - name: my-target
            dest: out
            items:
              - "@all-plugins"
        """,
    )


def test_plan_prints_grouped_copies_without_writing(
    config_dir: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    setup_basic_config(config_dir, repo_root)

    exit_code = run_cli(["--config-dir", str(config_dir), "--repo-root", str(repo_root), "plan"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "[my-target]" in out
    assert "foo" in out and "bar" in out
    assert not (repo_root / "out").exists()


def test_apply_actually_copies_files(config_dir: Path, repo_root: Path) -> None:
    setup_basic_config(config_dir, repo_root)

    exit_code = run_cli(["--config-dir", str(config_dir), "--repo-root", str(repo_root), "apply"])

    assert exit_code == 0
    assert (repo_root / "out" / "foo" / "SKILL.md").exists()
    assert (repo_root / "out" / "bar" / "SKILL.md").exists()


def test_only_filters_to_named_target(config_dir: Path, repo_root: Path) -> None:
    make_skill(repo_root, "plugins/skills/foo")
    write(
        config_dir / "targets.yaml",
        """
        targets:
          - name: target-a
            dest: out-a
            items: [plugins/skills/foo]
          - name: target-b
            dest: out-b
            items: [plugins/skills/foo]
        """,
    )

    exit_code = run_cli(
        [
            "--config-dir",
            str(config_dir),
            "--repo-root",
            str(repo_root),
            "apply",
            "--only",
            "target-a",
        ]
    )

    assert exit_code == 0
    assert (repo_root / "out-a" / "foo").exists()
    assert not (repo_root / "out-b").exists()


def test_only_unknown_target_name_errors(
    config_dir: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    make_skill(repo_root, "plugins/skills/foo")
    write(
        config_dir / "targets.yaml",
        """
        targets:
          - name: target-a
            dest: out-a
            items: [plugins/skills/foo]
        """,
    )

    exit_code = run_cli(
        [
            "--config-dir",
            str(config_dir),
            "--repo-root",
            str(repo_root),
            "plan",
            "--only",
            "does-not-exist",
        ]
    )

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "does-not-exist" in err


def test_config_error_returns_1(
    config_dir: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(config_dir / "bad.yaml", "targets: not-a-list")

    exit_code = run_cli(["--config-dir", str(config_dir), "--repo-root", str(repo_root), "plan"])

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "エラー" in err


def test_list_sets_prints_defined_sets(
    config_dir: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(
        config_dir / "case.yaml",
        """
        sets:
          my-set:
            - a
            - b
        """,
    )

    exit_code = run_cli(
        ["--config-dir", str(config_dir), "--repo-root", str(repo_root), "list-sets"]
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "@my-set" in out
    assert "- a" in out


def test_list_sets_no_case_file_prints_message(
    config_dir: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = run_cli(
        ["--config-dir", str(config_dir), "--repo-root", str(repo_root), "list-sets"]
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "定義されていません" in out
