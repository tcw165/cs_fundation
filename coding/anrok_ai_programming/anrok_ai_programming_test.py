from click.testing import CliRunner

from anrok_ai_programming import main


def test_main_runs_with_no_args() -> None:
    result = CliRunner().invoke(main, [])
    assert result.exit_code == 0
