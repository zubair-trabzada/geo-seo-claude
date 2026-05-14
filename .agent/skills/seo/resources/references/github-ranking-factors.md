<!-- Updated: 2026-03-08 -->
# GitHub Repository Discoverability Factors (Practical Reference)

This reference captures empirically useful factors for GitHub repository
discoverability. GitHub does not publish a full ranking formula.

## High-Signal Metadata

- Repository name clarity and intent match.
- Description specificity and keyword fit.
- Repository topics relevance and completeness (up to 20).
- Homepage URL quality and consistency.
- Social preview quality for share CTR.

## README Signals

- Strong opening summary (what it is, who it is for, why it matters).
- Query-aligned language for target use cases.
- Clear installation and quickstart path.
- Proof of utility (examples, artifacts, screenshots, outcomes).
- Contributor onboarding clarity (CONTRIBUTING, issue templates).

## Trust and Maintenance Signals

- Community profile completion (README, LICENSE, contribution policy,
  code of conduct, security policy).
- Release cadence and recency.
- Clear support path (issues/discussions/support docs).
- Citation metadata (`CITATION.cff`) for academic and professional reuse.

## Activity and Social Signals

- Stars and forks as adoption proxies.
- Contributor activity and issue/PR responsiveness.
- Watchers and discussion activity.

These are directional indicators and should not be treated as direct ranking
weights.

## Measurement Guidance

- Track query-position trends weekly with a fixed query set.
- Track conversion from views to stars/forks.
- Archive traffic snapshots daily or every 48h due GitHub retention limits.
- Run one experiment at a time and evaluate causal impact before stacking
  additional changes.

## Anti-Hallucination Rules

- Never claim definitive ranking weights.
- Distinguish observed evidence from inferred hypothesis.
- Mark API-limited sections as unknown, not failed.
