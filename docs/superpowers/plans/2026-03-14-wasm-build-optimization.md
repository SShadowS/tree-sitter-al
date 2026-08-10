# WASM Build Optimization Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get `tree-sitter build --wasm` to complete within GitHub free runner memory limits (7GB RAM + swap).

**Architecture:** Systematically test compilation approaches locally, measuring peak memory, then apply the winning approach to the CI workflow.

**Tech Stack:** tree-sitter CLI 0.26.5, wasi-sdk v25, GitHub Actions

---

## Context

- `src/parser.c` is 90MB / 2.1M lines — an exceptionally large parser
- GitHub free runners: 7GB RAM, ~14GB free disk for swap
- Current CI adds 12GB swap (total ~19GB virtual memory) — still OOMs after ~4 hours
- LLVM optimization passes are the primary memory consumer during WASM compilation
- The `--debug` / `-0` flag disables optimizations and should dramatically reduce memory

## Task 1: Baseline — Measure Current WASM Build Memory Usage

**Files:** None (measurement only)

- [ ] **Step 1: Build WASM with default settings, measure peak memory**

```bash
# On Windows, use PowerShell to measure peak memory
powershell -Command "& {
  \$proc = Start-Process -FilePath 'tree-sitter' -ArgumentList 'build','--wasm','.' -PassThru -NoNewWindow
  \$peak = 0
  while (-not \$proc.HasExited) {
    \$proc.Refresh()
    if (\$proc.PeakWorkingSet64 -gt \$peak) { \$peak = \$proc.PeakWorkingSet64 }
    Start-Sleep -Milliseconds 500
  }
  Write-Host \"Exit code: \$(\$proc.ExitCode)\"
  Write-Host \"Peak memory: \$([math]::Round(\$peak / 1GB, 2)) GB\"
  Write-Host \"Duration: \$((\$proc.ExitTime - \$proc.StartTime).TotalMinutes) minutes\"
}"
```

Record: peak memory (GB), duration, success/failure.

- [ ] **Step 2: Document baseline**

Record results in this plan under "Results" section at bottom.

## Task 2: Test Debug Mode (`-O0`)

- [ ] **Step 1: Build WASM with debug flag, measure peak memory**

```bash
powershell -Command "& {
  \$proc = Start-Process -FilePath 'tree-sitter' -ArgumentList 'build','--wasm','-0','.' -PassThru -NoNewWindow
  \$peak = 0
  while (-not \$proc.HasExited) {
    \$proc.Refresh()
    if (\$proc.PeakWorkingSet64 -gt \$peak) { \$peak = \$proc.PeakWorkingSet64 }
    Start-Sleep -Milliseconds 500
  }
  Write-Host \"Exit code: \$(\$proc.ExitCode)\"
  Write-Host \"Peak memory: \$([math]::Round(\$peak / 1GB, 2)) GB\"
  Write-Host \"Duration: \$((\$proc.ExitTime - \$proc.StartTime).TotalMinutes) minutes\"
}"
```

Record: peak memory (GB), duration, success/failure, output file size.

- [ ] **Step 2: Compare output size**

```bash
ls -lh tree-sitter-al.wasm
```

Record WASM file size vs baseline (if baseline succeeded).

## Task 3: Test CFLAGS `-O1` (Middle Ground)

If Task 2 succeeds but we want a smaller output, test `-O1` as a compromise.

- [ ] **Step 1: Build with CFLAGS="-O1"**

```bash
CFLAGS="-O1" powershell -Command "& {
  \$env:CFLAGS='-O1'
  \$proc = Start-Process -FilePath 'tree-sitter' -ArgumentList 'build','--wasm','.' -PassThru -NoNewWindow
  \$peak = 0
  while (-not \$proc.HasExited) {
    \$proc.Refresh()
    if (\$proc.PeakWorkingSet64 -gt \$peak) { \$peak = \$proc.PeakWorkingSet64 }
    Start-Sleep -Milliseconds 500
  }
  Write-Host \"Exit code: \$(\$proc.ExitCode)\"
  Write-Host \"Peak memory: \$([math]::Round(\$peak / 1GB, 2)) GB\"
  Write-Host \"Duration: \$((\$proc.ExitTime - \$proc.StartTime).TotalMinutes) minutes\"
}"
```

Record: peak memory (GB), duration, success/failure, output file size.

## Task 4: Apply Winning Approach to CI Workflow

Based on results from Tasks 1-3, update the workflow.

- [ ] **Step 1: Update build-wasm.yml with the approach that fits in ~19GB**

Modify the "Build WASM" step. If `-0` (debug) wins:
```yaml
      - name: Build WASM
        run: tree-sitter build --wasm -0 .
```

If `CFLAGS="-O1"` wins:
```yaml
      - name: Build WASM
        run: CFLAGS="-O1" tree-sitter build --wasm .
```

- [ ] **Step 2: Adjust swap size if needed**

If peak memory from testing suggests we can reduce or need to increase swap, update the swap step accordingly.

- [ ] **Step 3: Revert test tag back to `latest`**

Change `test-build` back to `latest` in the workflow.

- [ ] **Step 4: Push and trigger workflow to verify**

```bash
git add .github/workflows/build-wasm.yml
git commit -m "ci: optimize WASM build to fit in GHA runner memory"
git push
gh workflow run build-wasm.yml
```

## Task 5: Cleanup

- [ ] **Step 1: Delete test release and tag**

```bash
gh release delete test-build --yes
git push origin :refs/tags/test-build
```

- [ ] **Step 2: Delete test branch**

```bash
git push origin --delete test-build-workflow
git branch -D test-build-workflow
```

---

## Results

| Approach | Peak Memory | Duration | WASM Size | Success |
|----------|-------------|----------|-----------|---------|
| Default (`-O2`) | | | | |
| Debug (`-O0`) | | | | |
| CFLAGS `-O1` | | | | |

## Decision

[To be filled after testing]
