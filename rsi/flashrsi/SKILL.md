---
name: flashrsi
version: 3
source: https://yijunyu.github.io/rsi/flashrsi/SKILL.md
description: Continue the FlashRSI tilecov campaign in this repository, or specify it from scratch. Use when the user says "flashrsi go" (resume the loop), "flashrsi spec" (specify KPIs, build the loop, instrument progress, then run it), or otherwise asks to raise the measured tile-rs coverage goal through repeated benchmarked harness improvements — including "keep going without stopping", which arms a persisted goal so the loop continues across automatic rounds instead of waiting for another `flashrsi go`.
---

# FlashRSI tilecov loop

## Expansion of `flashrsi spec`

`flashrsi spec` expands to, verbatim:

> specify the KPI's for the goal in flashrsi, and create the feedback loop, print the goal/KPI/progress ratio at each iteration of the loop, and flashrsi go

Carry out all four parts in order.

### 1. Specify the KPIs for the goal

A KPI is a row with a **goal**, a `name`, a `target`, a `current`, a unit, and **the script that reads it**. Write them to the campaign config, not to chat. A KPI with no reader is not specified — it stays prose, is printed as `UNRESOLVED`, and never becomes scope by inference. This repository has paid twice for prose-to-scope guessing; the rule is that only a committed script may resolve a target.

The goal itself is the campaign's declared one, read from the campaign config. Where `.claude/goal.json` carries a matching `goal` + `kpi` pair, resolve the KPI from its structured fields (`name`, `board`, `condition`, `measured`) and carry its prose `target` through as context only.

If the campaign's `ACCEPTED_SCOPE.md` or `CLOSE.md` marks a subset out of scope, the **accepted** target — not the raw denominator — is the goal. The ledger's `achievable of achievable` line is a denominator, not a decision: never copy it into an objective, and never arm a goal whose remaining items the accepted scope already declares out of scope.

### 2. Create the feedback loop

The loop is the campaign's measurement apparatus, pinned and frozen for its lifetime: corpus, graders, denominator, train/dev/test split, and baseline. Grade → accept/reject → snapshot → next mechanism. If an instrument or the denominator has to change, close the campaign and open a new one; never re-mint a frozen split. A loop that can move while the search runs cannot tell "the kernel improved" from "the ruler changed".

### 3. Print the goal/KPI/progress ratio at every iteration

Every iteration prints the same block, **before** the edit and again **after** it, so the delta is evidence rather than a claim:

```
goal      <one line, the campaign goal>
KPI       <name>  <current>/<target> <unit>
progress  <current/target>   [<+/-delta> vs previous iteration]
open      <n> mechanisms, next: <the one being attempted>
```

`progress` is `current/target` for a coverage KPI (12/42 → 0.286) and the measured ratio where the KPI is ratio-shaped. Read the numbers from `tilecov round`; never from the previous message. **An iteration that rejects its candidate still prints the block** — an unchanged ratio is the result. If a block cannot be printed, repair the measurement before continuing the loop.

### 3b. Run the round through the binary, not through prose

The block above is produced by `tilecov round`, not re-derived each round. The
procedure — measure, compare to the campaign's stored ledger, refuse a
regression, print the block, name the next mechanism — is deterministic over
data the binary already holds, and performing it in prose costs tokens and lets
the comparison drift:

```sh
tilecov round --baseline benchmarks/tilecov/campaigns/<campaign>/state.json \
              --goal "<the campaign's declared, measured goal>"
```

- It exits **1 and prints `REJECT`** when the ledger covers fewer items or opens
  more than the baseline. A round that regressed cannot be credited; do not
  report it as progress.
- It exits **0** on progress or on no change. An unchanged number is still the
  round's result.
- It writes the new baseline back, so the next round compares against a stored
  measurement rather than against the previous message.
- Report the block it prints. Do not recompute it, and do not add a second
  opinion about whether the delta is "really" progress.

It is installed with `curl -fsSL https://yijunyu.github.io/rsi/install.sh | sh`,
or built in-tree with `cargo build --release -p tilecov_rs --bin tilecov`
(`target/release/tilecov`). It locates the tree at run time — `--root <dir>`,
then `$TILECOV_ROOT`, then walking up for `benchmarks/tilecov/` — so running it
inside a checkout needs no flags. The Python toolchain stays as the parity
oracle (`benchmarks/tilecov/rustport/score.py` grades the port) until that score
is trusted; the round path is the Rust one.

### 3a. Arm a CONTINUING goal — part of `spec`, not only of `go`

**This is the default, not an option.** Once the KPIs resolve from the ledger (step 1) and the
loop prints the block (step 3), `spec` ends by calling `create_goal` for the campaign. Specifying
a campaign and then waiting for a human to type `go` again is the per-turn loop this skill exists
to replace: the spec is the expensive part, and it should buy autonomous rounds, not one.

The goal armed here is the **continuing** one described under "Non-stop operation" below — same
objective text, same permanence clause, `max_goal_rounds` unset or >= 100000, one goal per
campaign. `spec` therefore ends with an armed goal and the loop already running: there is no
state in which a well-specified campaign sits idle waiting for a prompt.

Three conditions, and they are the same three that gate `go`:

- the KPI resolves from a committed reader script — never arm a goal you have not measured;
- the loop prints the metric block — a campaign whose instrument cannot print is not specified;
- the objective text is the *measured* target, so "achieved" is the ledger's answer.

If any of the three is false, `spec` is not finished: fix the measurement, do not arm. When they
hold, arm and go — the same response.

### 4. Then `flashrsi go`

Specifying is not the deliverable. Once the KPIs resolve and the loop prints, enter the loop below and run it until the measured goal is achieved — that is the expansion of `flashrsi go`, and it follows immediately.

**Do not let `spec` become a planning session.** If the KPI already resolves and the loop already prints, `spec` verifies both against the ledger in a few commands and goes straight to iteration 1; re-deriving an existing benchmark from scratch is not specification, it is stalling.

### 3c. File instrument anomalies while testing

A round can find a defect in the **ruler** rather than an uncovered item: a gate
failing for an environmental reason, a published number disagreeing with the
ledger, an example pointing at an empty split. Those are not coverage items and
must never be counted as progress — but they must not be lost either.

```sh
tilecov feedback --add "<what happened>" --kind bug|anomaly|ask --where "<file:line>"
tilecov feedback --resolve <id>       # when it is fixed or explicitly deferred
```

Every round prints `feedback N open instrument report(s)`. That line is the
mechanism: a finding filed once and never printed again does not get fixed, so
the count rides on the block next to the KPI. Fix them, or resolve them with the
reason recorded, before closing a campaign.

**And send it where someone will see it.** The local log is a queue, not a
notification: on another machine it is written into that machine's checkout and
the maintainer never learns of it. `tilecov feedback --link` prints a prefilled
issue URL on the public tracker; post it, or paste the same text into whatever
channel the campaign uses. A finding that stays local has not been reported.

In a multi-agent setting, say where you sent it in the report (`issue: <url>`),
so the next agent does not file the duplicate.

## Expansion of `flashrsi go`

`flashrsi go` expands to, verbatim:

> continue the flashrsi loop, don't stop, until the goal is achieved

Read that expansion as three obligations, not one:

- **continue the loop** — carry out the next local iteration. This is authorization to act, not a request for a status report, a plan, or a proposal.
- **don't stop** — an accepted, verified change ends that iteration, not the run. Pick the next open mechanism and go again.
- **until the goal is achieved** — "the goal" is the campaign's declared, *measured* target: the tilecov aggregate at full coverage, every item supported by its existing grader and regression controls. "Achieved" means the ledger says so, never that the work felt finished or that the remaining items look hard.

### Non-stop operation: arm a PERMANENT goal, then never wait for a human between rounds

The loop above is driven by the human typing `flashrsi go` again and again. It does not have to be.
The harness has a **persisted goal**: `create_goal` keeps this session working across automatic
continuation rounds, so the next iteration starts by itself. Use it.

**Every `flashrsi` invocation that is a *loop* (not a one-off question) must do this, in order:**

1. **Resolve the KPI from the ledger first** — never arm a goal whose target you have not measured.
   If the reader script is broken, fix the measurement before arming anything.
2. **`create_goal`** with the campaign's declared objective, resolved at arm time from the campaign
   config plus the accepted-scope record and filled with the *measured* target — never a literal
   copied from prose. Two shapes:
   - coverage campaign: "raise the accepted tilecov target from `<current>/<target>` to the
     campaign's declared accepted target, every item backed by its grader";
   - device campaign: "reach `<measured>/<target> <unit>` for `<KPI>` on `<part>`, with >=2 identical
     repeats".

   Do not arm at all when the accepted scope already covers the declared goal — complete it or
   report it instead. Every objective also carries an **explicit permanence clause** (stays active
   across rounds; never blocked or completed for a transient interruption; re-probe missing
   resources each round). Leave `max_goal_rounds` unset, or set it to >= 100000. One goal per
   campaign — if a campaign closes, complete the old goal and create a new one.
3. **Run one iteration**, edit + grade + re-measure, and **print the metric block** (section 3 above)
   in the response to *every* round, including continuation rounds. The block is the only thing
   a reader sees while the loop runs unattended, so it is not optional and it is never a summary
   of the previous round — re-read the numbers from the ledger each time.
4. **Do not ask for permission to continue.** Continuation is the default. Asking "shall I keep
   going?" converts a non-stop loop back into a per-turn loop and wastes the round.
5. **End the round with the next iteration's first action already chosen**, so the continuation
   has something concrete to do. "Next: <one named mechanism>" is part of the block.

**The goal is permanent by default. Arm it so that it cannot lapse:**

- `create_goal` **without** `max_goal_rounds`, or with a very large cap (>= 100000). A small cap
  silently ends the loop and is the most common way a "non-stop" campaign quietly stops.
- Put the permanence **into the objective text**: say explicitly that the goal stays active across
  rounds and must not be marked blocked or complete because of a transient interruption. The
  objective is re-read every round; the loop follows it.

**Stop conditions** (a permanent loop still stops):

- the *measured* target is reached -> `update_goal` action `complete`;
- the user says stop, pauses, or changes the goal -> `update_goal` `pause`/`edit`.

**A transient blocker is NOT a stop condition.** Hardware unavailable, tunnel down, CI red, a
credential expired — these change *what this round does*, never whether the loop continues:

- keep the goal `active`; do **not** call `update_goal` with `blocked` because a device or a
  network is missing. Blocking ends the autonomous run and is reserved for a condition the user
  has explicitly confirmed is terminal;
- instead **re-probe** the blocked resource at the start of every round (one cheap command), and
  spend the round on work that does not need it: instrumentation, grader/threshold calibration
  with synthetic controls, correcting overfitted rules against multi-point evidence, cross-checks
  of the toolchain, and the regression gate;
- print the blocker inside the metric block (`blocked? no — <resource> down N rounds`), so the
  outage is visible every round without ending the loop;
- if a round genuinely has nothing left that the missing resource is not required for, say so in
  one line and still re-probe next round. Manufacturing busywork is wrong; ending the loop is
  worse, because the resource usually comes back.

Difficulty, uncertainty, or "the remaining work looks hard" is never a reason to stop.

**What "non-stop" does not mean.** It does not mean unbounded spinning. An iteration that cannot
move the number must still produce evidence (a rejected candidate is a result), and three rounds
of the same unchanged number with no new evidence is a signal that the *classification* is wrong
(section 5), not that the loop should run faster. Re-classify, then continue.

The loop below is the method; this paragraph is the stop condition.

Read `benchmarks/tilecov/README.md` and the current campaign config before choosing work. `HANDOFF.md` may be stale; confirm any in-flight claim against current artifacts. Then get the measured state and the open items from `tilecov round` (section 3b), which re-measures the tree and names the next mechanism. Do not assume a historical count is current, and do not run the Python instruments on the round path.

For each iteration:

**The bookkeeping is the binary's job.** Everything deterministic over data the
binary already holds — preserve the campaign's pinned baseline, re-measure the
full ledger with the same instruments, compare, refuse a regression, record the
before/after, name the next mechanism — is `tilecov round` (section 3b). Do not
redo it in prose, and do not re-derive the numbers from the previous message.

The agent's job is what the binary cannot do:

1. **Make one change that addresses a mechanism, not an artifact.** Take the
   axis the block named, and make a harness or implementation change that can
   generalise beyond a single artifact, recording the failure trace and the
   intended prediction. Keep dev and test tasks out of edit selection.
2. **Keep the controls real.** Run the task grades, the negative controls,
   `benchmarks/tilecov/selftest.py` and `benchmarks/tilecov/check.sh` whenever
   the change touches the instrument. A candidate that weakens a control is
   rejected whatever the number did.
3. **Classify the obstacle, then replan.** The binary names the axis; naming the
   *obstacle* is judgement, and it decides what the next iteration attacks.
   - Write the classification down (a paragraph in the iteration record is enough, a doc when it changes the campaign's direction) and name the **one** obstacle the next iteration attacks.
   - A tier name is not a classification. `whole_kernel_knob` reads like an absent producer; checking its artifacts one by one showed all five refuse at `pto.get_block_idx`, which is this repository's compiler work. Verify the tier against the artifact before accepting the obstacle it implies.
   - Replanning may move work between classes, split one item into several, or conclude that the next step is a *decision* rather than an edit. What it may not do is re-label an obstacle to make it look reachable: check-and-reclassify, never re-label-to-unblock.
   - **Batch the next iteration when it is safe.** The plan is a list of tasks, not a single task: if several of them are independent — disjoint files or regions, separate acceptance tests, no shared instrument change — carry them in ONE iteration and grade them together, rather than spending an iteration per item. Batching is the default when the tasks do not interact; it stops being safe when they share a serialization point (the same match arm, the same refusal text, the same wrapper table) or when one of them changes the instrument, because then a failure in one hides the cause in another.
   - If the classification leaves no class this repository can move, say so with the four external inputs named, and stop rather than manufacturing an iteration.

Use `benchmarks/tilecov/tilers_coverage.py` for tasks and grading and `benchmarks/tilecov/run_rsi.py` for FlashRSI rollouts in an isolated `TILECOV_REPO` worktree. Inspect their current options before launching. The `tile` CLI is the first tool for accelerator-kernel lowering and verification; read the repository's `tile-rs` skill when that work arises.

Do not inflate the score by weakening an oracle, silently dropping unsupported operations, changing the denominator within a campaign, or calling a compile or manifest entry verified. Keep hardware-dependent target items in the goal. Record a missing device as a concrete limit while continuing independent software work. Stop the loop only when the measured goal is fully covered, the user asks to stop, or a real external blocker leaves no meaningful work; report the exact remaining items and evidence in the latter case.

## Device-dependent campaigns (embedded targets, accelerator boards)

When the KPI needs hardware, the loop spends most rounds unable to measure. The following are the
lessons that cost the most rounds to learn; they are part of the method, not anecdotes.

### 1. Get the device's own log before theorising about the device

A board stops answering. From the host you can see: the tunnel is down, the port refuses, the relay
logs say nothing. **These observations cannot distinguish "no power", "no network", "stuck in the
wrong boot image".** Do not spend rounds enumerating those hypotheses from the host side.

Ask for the device's own evidence — removable media, serial console, on-device log file — and read
it. In the campaign that produced this section, the decisive file was `wifi-ensure.log` on the SD
card: its last lines showed the association dropping, `udhcpc: no lease`, and an empty IP. The
device was healthy; the phone acting as its hotspot had gone to sleep. One `tail` would have
replaced hundreds of host-side inferences.

Corollary: keep a **recovery card** in the repo — the exact files to inspect, what "good" looks like
verbatim, and what to edit — so the human can act without the agent present, and gate it in the
preflight so it cannot drift.

### 2. A blocked resource changes the round, not the loop

Re-probe with one cheap command at the start of every round; print the outage in the metric block
(`blocked? no — <resource> down N rounds`). Spend the round on work the missing resource is not
needed for. Never call `update_goal` with `blocked` for a device or network that may come back.

### 3. Harden the grader against the device's own failure modes

Hardware produces **bad runs** at a few percent: all-zero dumps, truncated files, `ok=8 fail=0` with
garbage output, timings with `NaN`. A grader that treats those as a verdict will report "the
implementation is wrong" when the run was wrong — and will teach the wrong lesson for the rest of
the campaign.

- A bad run is **`UNRESOLVED`, not `FAIL`**: no conclusion was reached.
- A gate must demand **≥2 identical repeats** (hash the output). A single `ok==total` cannot
  distinguish "ran correctly" from "ran and wrote garbage".
- Every "cannot conclude" input path must return `UNRESOLVED` rather than raising: truncation and
  missing files are **normal**, and a traceback in the one device window wastes it.
- A grader that can pass on corrupted input is worse than one that fails: it makes the KPI lie.
  Prefer the direction that refuses.

### 4. Negative-control every gate, and then distrust redundant conditions

A check is not specified until a deliberate edit makes it fail. Write the negative control and run
it. Two concrete traps, both hit in practice:

- the condition was satisfied by **another occurrence** of the same string (removing one left the
  check green);
- a value was accepted under a **fuzzy alternative** (`">1"` matched while the literal `-gt 1` was
  gone).

Tighten to literal, count occurrences, and re-run the negative control until it fails for the
intended reason.

### 5. Measure what the label policy can and cannot change

When a KPI filters on a provenance string (who generated the artifact), widening the accepted set
is **inert** until the ledger actually contains a row with that provenance. Check the ledger census
(generators present, gates present) before treating a policy decision as a blocker. In the campaign
that produced this section, the "pending decision" was inert: no row at all carried any of the
candidate labels, and not one `generated` row existed.

### 6. Never assume an input's shape or identity — invert it and self-verify

Three rounds were spent fitting "residual laws" between a generator and a vendor artifact, which
collapsed once the artifact's true shape was solved for: the generator had been byte-identical all
along, fed the wrong parameters. Build the inversion into a script, and make it **self-verify**
(regenerate and compare byte-for-byte) so a wrong assumption fails immediately instead of producing
three plausible tables.

### 7. The instrument needs tests before the campaign trusts it

Assume zero. `cargo test` reporting `0 tests` on the tool that prints the KPI is a finding, not a
nuisance: a silently broken instrument can make the number *rise*. Pin the KPI's **semantics** in
unit tests, its **end-to-end pipeline and denominator** in a golden integration test over the real
ledger, and assert monotonic non-regression (a floor, not equality) so a legitimate improvement does
not look like a failure — a gate that cries wolf stops being read.
