import pytest

from tools.config_oracle import replay

pytestmark = pytest.mark.slow


@pytest.mark.parametrize("r", replay.REPLAYS, ids=lambda r: f"replay-{r.number}")
def test_replay_is_detected_as_specified(r, tmp_path):
    result = replay.run_replay(r, tmp_path)
    assert not result.masked_by_cannot_validate, result.statuses
    assert result.detected, result.statuses


def _head_param(r):
    if r.number == 4:
        return pytest.param(r, id="head-4", marks=pytest.mark.xfail(
            strict=True, reason="needs preproc_conditional_expression_tail lowering (milestone 2)"))
    return pytest.param(r, id=f"head-{r.number}")


@pytest.mark.parametrize("r", [_head_param(r) for r in replay.REPLAYS])
def test_current_parser_passes_the_same_cases(r):
    """Positive control: at HEAD these cases have no discrepancy of the replayed kind.
    A control whose every record is cannot-validate proves nothing, so that fails too."""
    result = replay.run_replay(r, None)
    assert not result.masked_by_cannot_validate, result.statuses
    assert not result.detected, result.statuses
