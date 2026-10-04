# Dataviz Fix

Use `dataviz-fix` when an existing visualization needs to be rebuilt, revised from feedback until accepted, and then used as evidence for improving the skill stack.

This is the repository's **repair and learning-loop** skill. The other skills choose, style, annotate, critique, or explain a chart. This skill coordinates them around a real artifact.

## User workflow

1. Paste or upload a chart and invoke `dataviz-fix` with any initial instruction.
2. The agent diagnoses the chart, rebuilds it as a real image, inspects the export, and fixes what fails before showing it.
3. Reply naturally with changes such as "keep the chart type", "make the labels larger", or "that title overstates the evidence".
4. Each revision continues from the latest candidate and changes only what the feedback names.
5. Repeat until the chart is right, then say "accept", "final", or an equivalent clear phrase.
6. The agent classifies why the first output missed and changes the owning skill only when the lesson generalizes.

## Skill-learning rule

Acceptance does not automatically mean "add another rule". The workflow first classifies the miss:

- **execution miss** - the rule already existed but was not followed;
- **missing rule** - no reusable guidance covered the correction;
- **ambiguous rule** - existing wording allowed the wrong choice;
- **conflicting rule** - two skills pushed in different directions;
- **tooling** - image handling, rendering, or delivery failed;
- **input data** - the required evidence was absent.

Only missing, ambiguous, or conflicting reusable guidance warrants a prose edit. The lesson is abstracted one level above the example and tested against at least two unrelated charts before it is committed, so one chart's values, nouns, or layout never become a standing rule.
