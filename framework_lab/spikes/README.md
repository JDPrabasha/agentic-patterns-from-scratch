# Survey spikes

One file per framework on the shortlist, each with the same `run()` signature as
`../my_agent.py`. Run a spike without adding its framework to the project:

```bash
uv run --with <package> framework_lab/parity.py --agent framework_lab/spikes/<name>.py --scenario tools
```

Copy the numbers into the trade-off matrix in `../JUSTIFICATION.md`. Only `my_agent.py` goes on
the class scoreboard.
