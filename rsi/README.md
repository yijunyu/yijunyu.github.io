# rsi — one-line install

`tilecov` is a single Rust binary that **measures** a benchmark tree and **drives
the improvement loop**: it re-measures, compares against the campaign's stored
ledger, refuses a regression, prints the goal/KPI/progress block, and names the
next mechanism.

## What this is

`tilecov` measures a **ledger-shaped benchmark** and drives the loop against it.
The tile-rs coverage ledger (230/239, nine hardware targets) is the **reference
demo** — a real workload with a countable denominator, exclusions that have
counterparts, and items that refuse. It is not a product target, and it is
probably not your goal.

What transfers to another goal: a measurement with a committed reader, a `round`
that refuses a regression and names the next mechanism, a feedback queue for
defects in the ruler, and a self-updating skill. What does not transfer is the
denominator — every new goal needs its own, resolved by its own script rather
than restated in prose.

## Install (one line)

```sh
curl -fsSL https://yijunyu.github.io/rsi/install.sh | sh
```

Installs `tilecov` to `~/.local/bin` (created if missing) and prints the `PATH`
line if it is not already there. It refreshes a skill you already have but will
not create one for an agent you did not install into, so on a fresh machine it
tells you the skill is missing rather than claiming 0 updates -- the binary alone
leaves an agent without instructions. Verify:

```sh
tilecov version      # tilecov 0.5.0
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

`tilecov` finds the tree at **run time** — nothing is baked in at build time:

1. `--root <checkout>` (global, may go before or after the command)
2. `$TILECOV_ROOT`
3. walking up from the current directory, looking for `benchmarks/tilecov/`

So running it inside a checkout needs no flags. Outside one it fails with the
search path named instead of guessing:

```
tilecov: cannot find the benchmark tree from /tmp upwards (looked for benchmarks/tilecov/).
  Pass --root <checkout> or set TILECOV_ROOT=<checkout>.
```

Other commands:

| command | what |
|---|---|
| `ledger [--json\|--canonical]` | the item ledger; `--canonical` emits the portable shape any other goal can produce |
| `round --ledger P` | drive the loop over **any** goal's canonical ledger, from any directory |
| `kpi` | the one-line KPI |
| `measure [-o P]` | re-measure the tree into a manifest |
| `round --json` | the round block as one object, for a driver that should not parse prose |
| `doctor` | is this install sane? binary version, repo root, manifest, git HEAD, every installed skill copy, and a real POST to the telemetry endpoint |
| `verify-release [--rebuild]` | is the published artifact the one this source tree builds? compares the running binary, the served bytes, and a fresh build |
| `version` | the binary version |

`round` also prints a **ruler** line every round — host, repo root, branch, HEAD,
and the skill path/version/hash it measured with — and `--strict` refuses with
exit **5** when the tree and the stored ledger are at different revisions, so a
delta is never silently computed across two trees.

## Feedback: defects in the ruler

A round can find an instrument defect rather than an uncovered item. That is not
coverage and must not be scored as such, but it must not be lost either:

```sh
tilecov feedback --add "<what happened>" --kind bug|anomaly|ask --where "<file:line>"
tilecov feedback --resolve <id>
```

`tilecov round` prints `feedback N open instrument report(s)` on every block, so
the backlog is visible next to the KPI instead of buried in a document.

The local log is a queue, not a notification — on another machine it lands in
that machine's checkout and nobody upstream sees it. Send it:

```sh
tilecov feedback --link
```

prints a prefilled issue URL on https://github.com/yijunyu/yijunyu.github.io/issues
(labels `feedback`, title and body built from the open entries). No token needed.
Record the URL you posted in your report so the next agent does not duplicate it.

## Telemetry (opt-in, anonymous)

Off unless **both** are set:

```sh
export TILECOV_TELEMETRY=1
export TILECOV_TELEMETRY_URL=https://your-collector.example/feedback
```

It posts `schema, tool, version, command name, duration_ms, exit, os, arch` —
never arguments, paths, branch, ledger numbers or hashes. The POST is spawned and
not awaited, so a dead collector never slows or fails a command.

There is no default sink: GitHub Pages cannot accept a POST, so the endpoint is
yours to run. With the flag set and no URL, nothing is sent.

## Keeping the skill current

The skill is versioned and the manifest pins the version and its sha256:

```sh
tilecov skill            # which instances exist here and at what version
tilecov skill --check    # exit 1 if any installed copy is behind the manifest
tilecov skill --update   # verify the digest, then refresh every instance present
```

`install.sh` runs `--update` at the end, so installing or upgrading the binary
refreshes the skill too. Symlinked instances report `managed` and are not written
through.

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
