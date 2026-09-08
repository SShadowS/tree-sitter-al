#!/bin/bash
#
# FIXTURE / detector, not a utility. Pins one property of tools/ts-lock.sh:
#
#   A HOLDER MUST NOT RELEASE A LOCK IT NO LONGER OWNS.
#
# "We are exiting" does not imply "we still hold the lock". An earlier version
# released unconditionally, and it cost real mutual exclusion: a killed
# background task left zombie ts-lock shells in their wait loops, one of them
# later exited, its trap deleted the lock directory belonging to a DIFFERENT and
# actively running holder, and the next waiter acquired mid-run. The violation
# came from the RELEASE path, which is the side nobody audits.
#
# This runs the scenario against an ISOLATED lock directory (TS_LOCK_DIR), so it
# never touches the real one and can be run while other streams are working.
#
#   ./tools/gate-fixtures/ts-lock-release-guard.sh
#     exit 0  the exiting holder left the new owner's lock alone
#     exit 1  it deleted a lock it did not own
#
# Used by tools/gate_selftest.py, which also runs it against a ts-lock.sh
# reverted to the unconditional release, to prove the detector itself works.

set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
LOCK="${TMPDIR:-/tmp}/ts-lock-release-guard.$$"
rm -rf "$LOCK"

fail() { echo "ts-lock-release-guard: FAIL - $*" >&2; rm -rf "$LOCK"; exit 1; }

# Holder A takes the lock and holds it briefly.
TS_LOCK_DIR="$LOCK" TS_LOCK_OWNER="holder-A" \
    "$HERE/../ts-lock.sh" bash -c 'sleep 4' >/dev/null 2>&1 &
holder_a=$!

# Wait for A to actually own it.
#
# Anchor on `owner`, which EVERY version of ts-lock.sh writes -- not on `token`,
# which only the fixed one does. Waiting on token made this detector time out
# against the pre-fix script and report "holder A never acquired the lock": a
# detector failing for the wrong reason, which is worth no more than one that
# does not fail at all.
for _ in $(seq 1 50); do
    [ -f "$LOCK/owner" ] && break
    sleep 0.1
done
[ -f "$LOCK/owner" ] || fail "holder A never acquired the lock"

# Simulate what a stale-breaker does: the lock is now someone else's.
printf '%s' "some-other-holder-token" > "$LOCK/token"
printf '%s' "holder-B" > "$LOCK/owner"

wait "$holder_a" 2>/dev/null

# THE ASSERTION. A has exited. The lock now belongs to B, so it must still be
# there. If A's trap removed it, B is running unprotected and the next waiter
# will acquire on top of it.
if [ ! -d "$LOCK" ]; then
    fail "the exiting holder deleted a lock owned by someone else"
fi
held=$(cat "$LOCK/token" 2>/dev/null || echo '<gone>')
[ "$held" = "some-other-holder-token" ] \
    || fail "the lock survived but its token changed to '$held'"

rm -rf "$LOCK"
echo "ts-lock-release-guard: PASS - exiting holder left the new owner's lock intact"
exit 0
