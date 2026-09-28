import pytest

from tools.config_oracle import replay

pytestmark = pytest.mark.slow


@pytest.mark.parametrize("r", replay.REPLAYS, ids=lambda r: f"replay-{r.number}")
def test_replay_is_detected_as_specified(r, tmp_path):
    result = replay.run_replay(r, tmp_path)
    assert not result.masked_by_cannot_validate, result.statuses
    assert result.detected, result.statuses


@pytest.mark.parametrize("r", replay.REPLAYS, ids=lambda r: f"head-{r.number}")
def test_current_parser_passes_the_same_cases(r):
    """Positive control: at HEAD these cases have no discrepancy of the replayed kind.
    A control whose every record is cannot-validate proves nothing, so that fails too."""
    result = replay.run_replay(r, None)
    assert not result.masked_by_cannot_validate, result.statuses
    assert not result.detected, result.statuses


def test_replay_3_structure_on_a_hand_built_tree_witness():
    """Labelled: replay.REPLAY_3_WITNESS_LABEL. The real old parser is caught only by the
    has_error backstop; this shows `structure` catches the same regrouping once the hidden
    MISSING token is gone. The witness must equal the old parser's tree on every node kind
    the defect regroups, and HEAD's own tree for the case must be structurally clean."""
    ds, witness, old = replay.replay3_tree_witness()
    assert witness == old
    got = {(d.check, d.kind, d.path.rsplit("/", 1)[-1]) for d in ds}
    assert ("structure", "extra", "call_statement.-@143-146") in got, got
    assert ("structure", "missing", "end_keyword.-@143-146") in got, got
    r3 = next(r for r in replay.REPLAYS if r.number == 3)
    head = replay.run_replay(r3, None)
    assert [rec.status for rec in head.records if rec.config == "CLEAN22=0"] == ["pass"], head.statuses
