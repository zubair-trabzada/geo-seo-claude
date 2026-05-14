<!-- Updated: 2026-03-08 -->
# README Audit Rubric (GitHub SEO + Conversion)

Use this rubric to grade repository README quality for discoverability,
comprehension, and conversion.

## Scoring Categories (100 points)

| Category | Weight | What Good Looks Like |
|----------|--------|----------------------|
| Opening Clarity | 20 | First section explains value, audience, and use case quickly |
| Information Architecture | 20 | Logical headings, no major section gaps, easy scan flow |
| Install + Quickstart | 20 | Minimal runnable path, explicit prerequisites, copy-paste steps |
| Proof + Credibility | 15 | Examples, outputs, screenshots, constraints, version context |
| CTA + Community | 15 | Contribute/report/support guidance and clear next actions |
| Readability + Accessibility | 10 | Clean heading hierarchy, descriptive links, image alt text |

## Mandatory Checks

- Exactly one H1.
- No heading level jumps greater than one.
- Installation path exists.
- License reference exists.
- At least one contribution/support path exists.
- Image alt text coverage for README markdown images.

## Severity Mapping

- `Critical`:
  - no clear project purpose in opening section.
  - missing installation instructions.
  - broken structure that blocks understanding.
- `Warning`:
  - weak or missing CTA.
  - insufficient proof/examples.
  - weak heading hierarchy or low readability.
- `Pass`:
  - baseline met with no severe gaps.
- `Info`:
  - optional enhancements.

## Confidence Labels

- `Confirmed`: directly observed in README content.
- `Likely`: probable based on pattern, needs minor verification.
- `Hypothesis`: recommendation needing additional context.

## Output Contract

For each finding include:

- `Finding`
- `Evidence`
- `Impact`
- `Fix`
- `Severity`
- `Confidence`
