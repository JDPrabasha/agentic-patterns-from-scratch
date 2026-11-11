# Recorded runs

Facilitators: during your rehearsal, copy a few traces from `runs/` into this folder and commit
them (for example `labB-bad-description.jsonl`, `labD-plan.jsonl`). If a team's key or the
network fails during the lab, they can follow along with:

    uv run scripts/replay.py examples/<file>.jsonl --delay 0.3

Traces contain only the fictional shop data and the model's replies; check them before you
commit anyway.
