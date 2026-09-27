from pathlib import Path

from tools.query_coverage import loader


def test_every_header_under_src_is_stamped():
    stamped = {p.as_posix() for p in loader.stamped_files(loader.REPO_ROOT)}
    headers = {p.relative_to(loader.REPO_ROOT).as_posix() for p in (loader.REPO_ROOT / "src").rglob("*.h")}
    assert headers, "src/ has no headers? the glob is wrong"
    assert headers <= stamped
    assert "src/unicode_id.h" in stamped


def test_build_lock_is_exclusive(tmp_path):
    with loader.build_lock(tmp_path):
        assert (tmp_path / ".oracle-build.lock").is_dir()
        try:
            with loader.build_lock(tmp_path, timeout=0.2):
                raise AssertionError("second holder acquired the lock")
        except TimeoutError:
            pass
    assert not (tmp_path / ".oracle-build.lock").exists()
