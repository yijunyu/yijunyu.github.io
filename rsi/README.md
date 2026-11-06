# rsi — one-line install

`tilecov` is a single Rust binary that **measures** a benchmark tree and **drives
the improvement loop**: it re-measures, compares against the campaign's stored
ledger, refuses a regression, prints the goal/KPI/progress block, and names the
next mechanism.

## Install (one line)

```sh
curl -fsSL https://yijunyu.github.io/rsi/install.sh | sh
```

Installs `tilecov` to `~/.local/bin` (created if missing) and prints the `PATH`
line if it is not already there. Verify:

```sh
tilecov version      # tilecov 0.1.0
```

Published assets: `bin/tilecov-darwin-arm64`. To install elsewhere or from a
mirror, put the variable on the **`sh` side of the pipe** — `VAR=x curl … | sh`
sets it for `curl` only, so the script would still install to the default:

```sh
curl -fsSL https://yijunyu.github.io/rsi/install.sh | TILECOV_PREFIX="$HOME/bin" sh
curl -fsSL https://yijunyu.github.io/rsi/install.sh | TILECOV_BASE=https://example.org/rsi sh
```

If there is no asset for your platform the installer fails and says so — it does
not leave a broken binary behind.

## Run a round

```sh
tilecov round --baseline <campaign>/state.json --goal "<the campaign's goal>"
```

```
goal      raise the measured coverage, every item backed by its grader
KPI       tilecov aggregate  230/239 0.9623
progress  0.9623   [+0 items vs baseline]
open      1 mechanisms, next: targets (9 open, needs hardware)
blocked?  no -- 0 reachable open item(s), 9 hardware-only
```

Exit `1` with `REJECT` when the ledger went backwards; the stored baseline is
not overwritten, so a rejected round cannot launder a claim into the next one.

`tilecov` reads the tree from its checkouts: set `TILECOV_ROOT=/path/to/repo`
when running it against a different checkout, otherwise it uses the path baked
in at build time. Other commands: `ledger [--json]`, `kpi`, `measure [-o P]`,
`version`.

## Attach the skill to your agent

The skill is one markdown file and the loop above is what it tells the agent to
do. Fetch it straight into the directory your agent loads:

| agent | where the skill goes | command |
|---|---|---|
| **dsh** (DeepSeek Harness) | `~/.dsh/skills/flashrsi/SKILL.md` | `mkdir -p ~/.dsh/skills/flashrsi && curl -fsSL https://yijunyu.github.io/rsi/flashrsi/SKILL.md -o ~/.dsh/skills/flashrsi/SKILL.md` |
| **Claude Code** | `.claude/skills/flashrsi/SKILL.md` (project) | `mkdir -p .claude/skills/flashrsi && curl -fsSL https://yijunyu.github.io/rsi/flashrsi/SKILL.md -o .claude/skills/flashrsi/SKILL.md` |
| **Codex** | `AGENTS.md` at the repo root | `curl -fsSL https://yijunyu.github.io/rsi/flashrsi/SKILL.md >> AGENTS.md` |
| **grok build** | its own instructions path | fetch the file and point the agent at it: `curl -fsSL https://yijunyu.github.io/rsi/flashrsi/SKILL.md -o flashrsi-SKILL.md` |
| **pi-agent** | its own instructions path | same: `curl -fsSL https://yijunyu.github.io/rsi/flashrsi/SKILL.md -o flashrsi-SKILL.md` |

The `dsh`, Claude Code and Codex rows use those tools' documented skill /
instructions locations. The **grok build** and **pi-agent** rows are deliberately
generic: I have not verified their instructions paths, so they get the file and a
pointer rather than a guessed directory — set the path their docs specify.

## Notes

- The binary is a port of a Python reference implementation; parity is graded by
  `score.py` in the source repository (12/12 ledger axes, 5/5 manifest sections,
  byte-identical table and KPI line).
- Only `darwin-arm64` is published here right now. Building another platform
  needs the source tree (`cargo build --release -p tilecov_rs --bin tilecov`).
- The installer verifies the download by running `tilecov version`; a download
  that does not run is reported as a failure, not as success.
