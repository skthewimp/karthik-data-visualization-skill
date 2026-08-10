# Dataviz Fix

Use `dataviz-fix` when an existing visualization needs to be rebuilt, reviewed by Karthik, revised until accepted, and then used as evidence for improving the skill stack.

This is the repository's **repair and learning-loop** skill. The other skills choose, style, annotate, critique, or explain a chart. This skill coordinates those capabilities around a real artifact and preserves what Karthik corrected.

## User workflow

1. Paste or upload a chart and invoke `dataviz-fix` with any initial instruction.
2. Receive a real regenerated chart, not a critique-only response.
3. Reply naturally with changes such as “keep the chart type”, “make the labels larger”, or “that title overstates the evidence”.
4. Repeat until the chart is right.
5. Say “accept”, “final”, or an equivalent clear phrase.
6. The agent classifies why the first output missed and changes the owning skill only when the lesson generalizes.

Hermes is the first interface because Telegram and WhatsApp already support pasted images, session continuity, and returned chart files. A separate web app is useful later only if side-by-side comparison or a case gallery proves necessary.

## Case packet

Each run is stored under the configured dataviz-fix root and contains:

- the original uploaded chart;
- every rendered iteration;
- user feedback verbatim;
- hashes of the skill files used at the start;
- the accepted artifact;
- a review packet and skill diagnosis.

The bundled `case_manager.py` script creates and updates these files without overwriting prior artifacts.

## Skill-learning rule

Acceptance does not automatically mean “add another rule”. The workflow first classifies the miss:

- **execution miss** - the rule already existed but was not followed;
- **missing rule** - no reusable guidance covered the correction;
- **ambiguous rule** - existing wording allowed the wrong choice;
- **conflicting rule** - two skills pushed in different directions;
- **tooling** - image handling, rendering, inspection, or delivery failed;
- **input data** - the required evidence was absent.

Only missing, ambiguous, or conflicting reusable guidance normally warrants a skill edit. The smallest owning skill is changed; the umbrella skill changes only when the workflow itself failed.

## Hermes installation

On a Hermes host with this repository checked out:

```bash
./sync.sh --no-pull --surface hermes
```

This installs the Claude-compatible skill directories under `~/.hermes/skills/data-science/`. The default `all` install remains Codex plus Claude so local users do not get a new Hermes directory unexpectedly.
