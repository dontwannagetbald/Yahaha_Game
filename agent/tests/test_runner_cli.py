from __future__ import annotations

import json
import subprocess
from pathlib import Path


def write_input(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "prompt": "做一个霓虹机器人生存游戏",
                "chat_history": [{"role": "user", "content": "想做个机器人小游戏"}],
                "uploaded_assets": [],
            },
            ensure_ascii=False,
        )
    )


def test_runner_help_exposes_conversation_and_generate_commands(tmp_path: Path):
    completed = subprocess.run(
        ["python3", "-m", "app.runner", "--help"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "conversation" in completed.stdout
    assert "generate" in completed.stdout


def test_runner_generate_writes_bundle(tmp_path: Path):
    input_path = tmp_path / "request.json"
    output_dir = tmp_path / "bundle"
    write_input(input_path)

    completed = subprocess.run(
        [
            "python3",
            "-m",
            "app.runner",
            "generate",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "manifest.json" in completed.stdout
    assert (output_dir / "manifest.json").exists()


def test_runner_rejects_missing_openai_key(tmp_path: Path):
    input_path = tmp_path / "request.json"
    output_dir = tmp_path / "bundle"
    write_input(input_path)

    completed = subprocess.run(
        [
            "python3",
            "-m",
            "app.runner",
            "generate",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--provider",
            "openai-compatible",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "OPENAI_COMPATIBLE_API_KEY" in completed.stderr
