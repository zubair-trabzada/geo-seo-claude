---
name: geo-distribution-plan
description: >
  Authority-tiered multi-platform content distribution plan. Sits between
  content creation and technical publishing. Builds a Tier 1/2/3 platform
  scoring matrix, tags each platform with AI-training-corpus coverage,
  produces a 14-day cadence (D0 main site → D+1 Tier 1 syndication → D+3
  Tier 2 rewrites → D+7 Tier 3 + social cuts), supplies per-platform rewrite
  constraints (Zhihu, WeChat, Xiaohongshu, CSDN/Juejin, LinkedIn, Medium,
  Substack, Reddit, Hacker News, X Threads, vertical media), and a 7/14/30
  day authority-signal reclaim checklist. Use when user says "distribute",
  "distribution plan", "syndication", "publishing cadence", "channel plan",
  "/geo distribute".
version: 1.0.0
author: geo-seo-claude-plus
tags: [geo, distribution, syndication, channels, cadence, authority]
allowed-tools: Read, Grep, Glob, Bash, WebFetch, Write
---

# GEO Distribution Plan Skill

## Core Insight

`geo-platform-optimizer` answers "*given my page, how do I tune it for each AI engine?*" — it optimizes a single artifact for a single surface. This skill answers a different question: "*given my topic, where do I publish, in what order, with what rewrites, so that AI training corpora and retrieval indexes pick up the topic from multiple high-authority entry points?*"

Two facts make multi-platform distribution non-negotiable for GEO:

1. **AI engines do not retrieve from one source.** A 2025 Profound study found Perplexity averages 4–8 cited sources per answer; ChatGPT search averages 2–4; Gemini and Google AI Overviews routinely pull from 3+ surfaces. A topic that exists on only your domain has at most a 1-in-N chance of being the cited source on any given answer — and that chance drops to zero if a higher-authority surface (Reddit thread, Wikipedia paragraph, top YouTube transcript) covers the same topic better.
2. **The cost of mis-sequenced distribution is canonical confusion.** Dropping the same article verbatim on Medium, LinkedIn, and Substack on day 1 with no canonical or staggering teaches every engine that the canonical answer-location is ambiguous. Engines hedge by citing none of them and falling back to the older incumbent on the topic.

The distribution plan therefore has three jobs: **(a)** pick the right platforms for the topic at the right tier, **(b)** sequence the publish moves over 14 days so each surface reinforces the next without canonical conflict, **(c)** prescribe per-platform rewrites that match each platform's audience and AI-corpus footprint without breaking the topical-cluster signal.

---

## How to Use This Skill

1. Take a **topic** and the **canonical URL** of the source article on the main site.
2. (Optional) Take an audience descriptor (B2B / B2C / dev-tools / consumer / regulated) — used to bias platform tier scoring.
3. (Optional) Take a region (`global / cn / na / eu`) — used to gate Chinese vs. English-first platforms.
4. Run the 7-step workflow below.
5. Emit `~/.geo-prospects/distribution/<domain>-<topic-slug>-<YYYY-MM-DD>.md` with the tier matrix, 14-day cadence, per-platform briefs, and 7/14/30-day reclaim checklist.

This skill must be invoked **only after `geo-citation-pipeline` returns PIPELINE_READY** for the canonical URL. Distribution amplifies whatever AI engines see on the destination — distributing a BLOCKED page wastes the effort.

---

## Platform Tiering Matrix

Each candidate platform is scored on three dimensions and tiered. The tier governs sequencing and rewrite intensity.

### Scoring dimensions

| Dimension | What it measures | Score range |
|---|---|---|
| **Authority weight (A)** | Domain-level authority signal AI engines treat as a trust prior — proxied by Wikipedia citation frequency, DR equivalents, and editorial gating | 1–5 |
| **AI-corpus coverage (C)** | Known or strongly inferred presence of the platform in major AI training sets (Common Crawl, vendor disclosures) and live retrieval indexes | KNOWN / PARTIAL / UNKNOWN |
| **Audience fit (F)** | Match between the platform's audience and the topic's audience descriptor | 1–5 |

`Tier_score = A × F` (range 1–25). Then bump up one tier if `C = KNOWN`, leave alone if `PARTIAL`, drop one tier if `UNKNOWN`.

| Tier | Score range | Role |
|---|---|---|
| **Tier 1 — Authority Hub** | ≥ 16 | Syndicate first; minimal rewrite; full attribution back to canonical |
| **Tier 2 — Authority Amplifier** | 8–15 | Rewrite with distinct opening; cross-link to Tier 1 + canonical |
| **Tier 3 — Reach / Social Cut** | < 8 | Excerpt, snippet, or media cut; teaser link only |

### Pre-scored platform reference

This is the default scoring matrix. Adjust per topic / audience / region.

| Platform | A | Default F | C | Default tier | Region | Audience fit notes |
|---|---|---|---|---|---|---|
| Wikipedia | 5 | 4 | KNOWN | T1 | global | Only for genuinely encyclopedic content; not for promotional posts |
| Reddit (relevant subreddit) | 4 | 4 | KNOWN | T1 | global | Strongest Perplexity / ChatGPT signal; requires community-native voice |
| Hacker News | 4 | 3 | KNOWN | T2 | global | Dev / B2B / startups only; strict no-promotion norms |
| Stack Overflow / Stack Exchange | 5 | 3 | KNOWN | T1 | global | Procedural / Causal dev content only; must answer a real question |
| YouTube (with transcript) | 4 | 4 | KNOWN | T1 | global | Transcripts are heavily indexed by Gemini and ChatGPT search |
| Medium | 3 | 3 | KNOWN | T2 | global | Use canonical tag back to source; topic-tag for distribution |
| Substack | 3 | 3 | PARTIAL | T2 | global | Best for Causal long-form; newsletter signal helps retention metrics |
| LinkedIn (long-form Article) | 4 | 4 | PARTIAL | T2 | global | B2B / professional only; must have a personal hook |
| Quora | 3 | 3 | KNOWN | T2 | global | Definitional + Comparative content only; must answer a real question |
| 36Kr | 4 | 4 | PARTIAL | T1 | cn | Premium B2B / tech / startup outlet |
| Huxiu | 4 | 4 | PARTIAL | T1 | cn | B2B / business / industry analysis |
| Zhihu | 5 | 4 | PARTIAL | T1 | cn | Strongest Chinese AI-search citation source; long-form Q&A |
| WeChat Official Account | 4 | 4 | UNKNOWN | T2 | cn | Closed garden — AI-corpus coverage is unverified; valuable for owned-audience retention |
| Xiaohongshu | 3 | 3 | UNKNOWN | T3 | cn | Consumer / lifestyle / visual; rarely cited by Western engines |
| CSDN | 3 | 4 | PARTIAL | T2 | cn | Developer / technical content |
| Juejin | 3 | 4 | PARTIAL | T2 | cn | Developer / front-end / engineering |
| Industry trade outlets (e.g. TechCrunch, The Verge, Ars Technica, IEEE Spectrum) | 5 | varies | KNOWN | T1 | global | Editorial gate; pursue as pitched contribution, not self-publish |
| G2 / Capterra / Trustpilot | 4 | 3 | KNOWN | T2 | global | Comparative content only; review-based platforms |
| X (Twitter) Threads | 2 | 3 | UNKNOWN | T3 | global | Reach-only; X feed is intermittently in AI corpora |
| Personal blog cross-post | 2 | varies | UNKNOWN | T3 | global | Useful only if the blog has an established audience |

---

## AI-Training-Corpus Coverage Tags

The C dimension carries strategic weight. Tag each platform with one of:

| Tag | Meaning | Source of evidence |
|---|---|---|
| **KNOWN** | Documented in published Common Crawl analyses, major model technical reports, or vendor disclosures | Public research, e.g., Reddit and Wikipedia in Common Crawl; YouTube transcripts in Google's training disclosures |
| **PARTIAL** | Substantial evidence the platform appears in retrieval indexes (live search) even if training inclusion is uncertain | Observed in Perplexity / ChatGPT search citations |
| **UNKNOWN** | No reliable evidence of inclusion in either training or retrieval | Closed gardens (WeChat); platforms with aggressive robots blocking |

**Strategic rule:** UNKNOWN platforms are not worthless — they are valuable for **owned-audience retention** and **conversion** — but they should never anchor a GEO distribution plan. Always pair an UNKNOWN platform with at least one KNOWN platform in the same week to preserve AI-corpus reach.

---

## 14-Day Cadence Template

Default sequence assumes 1 canonical URL + 2–4 Tier 1 platforms + 3–6 Tier 2 platforms + Tier 3 fills the rest.

| Day | Move | Platforms | Rewrite intensity | Canonical handling |
|---|---|---|---|---|
| **D0** | Publish canonical | Main domain | None | Self-canonical; ping IndexNow |
| **D+1** | Tier 1 syndication wave | 1–2 Tier 1 platforms (e.g., Reddit relevant subreddit + Zhihu for CN) | Distinct opening (first 100 words) + native formatting; body may be near-verbatim | `rel="canonical"` to main URL where supported; explicit attribution otherwise |
| **D+2** | Quiet day | — | — | Allow indexing to settle |
| **D+3** | Tier 2 rewrite wave A | 2–3 Tier 2 platforms (e.g., Medium + LinkedIn + 36Kr) | Distinct opening + distinct conclusion; reorganize body into platform-native structure; insert at least one platform-specific example | Canonical tag where available; cross-link to D+1 syndication where relevant |
| **D+5** | Tier 2 rewrite wave B | 1–2 more Tier 2 (e.g., Substack newsletter, Quora answer) | Same as D+3 | Same |
| **D+7** | Tier 3 + social cuts | X thread, LinkedIn post (short-form), Xiaohongshu cut if CN | Pure excerpt or snippet | Teaser link to canonical |
| **D+10** | Authority follow-up | If applicable: pitch to industry editorial outlet, Wikipedia citation if eligible | Editorial workflow | External canonical, ledes the source |
| **D+14** | Reclaim checkpoint #1 | All published surfaces | — | Run the 7/14/30 reclaim checklist |

### Conflict-avoidance rules

- **Never publish two near-verbatim copies on the same day on KNOWN-corpus platforms.** Stagger by at least 24 h.
- **Use `rel="canonical"` to the main URL** on Medium, LinkedIn Articles, Substack (custom-domain accounts), Quora answers — wherever the platform supports it.
- **For platforms that do not support canonical** (Reddit, Zhihu, WeChat, X), require a distinct opening (≥ 100 words) and an explicit attribution line linking to the canonical source.
- **Reddit and Hacker News are not "distribution channels" — they are communities.** Treat them as topic-native posts authored by a human contributor, not as syndication. Auto-cross-posting will be reported as spam.
- **WeChat Official Account content is canonical-only inside WeChat.** Do not also publish the same article on Zhihu the same week — split the topic into a Zhihu Q&A angle and a WeChat editorial angle.

---

## Per-Platform Rewrite Constraints

Each platform has structural and tonal conventions that, if violated, degrade engagement and may suppress AI-corpus inclusion (because low-engagement posts get pushed out of retrieval indexes).

### Zhihu

- **Opening pattern:** Pose a sharp question; do not start with a definition. Question-hook → personal stake → answer.
- **Length:** 1500–4000 Chinese characters for Tier 1 treatment.
- **Format:** First-person voice, conversational, with bolded inline takeaways. Use Zhihu's native image and code blocks; avoid embedded screenshots from the canonical post.
- **CTA:** No external link in the first 30 % of the post. Source attribution at the end as a "推荐阅读" (Recommended reading) link.

### WeChat Official Accounts

- **Opening pattern:** Cover image card + 1-sentence editorial hook + 3-bullet TL;DR ("本文重点").
- **Length:** 800–2500 Chinese characters; readers skim on mobile.
- **Format:** Short paragraphs (2–3 sentences); use 小标题 (sub-headings) every 200–300 characters; insert 1–2 illustrations.
- **CTA:** Soft CTA at the end (关注 / 收藏); external links only via reply-keyword pattern, not inline.

### Xiaohongshu

- **Opening pattern:** Visual-first; the cover image carries the hook text.
- **Length:** 300–800 characters; high emoji density tolerated.
- **Format:** Numbered listicle or before/after structure; topic tags (#) at the end.
- **CTA:** Profile-link follow rather than external link; external links are heavily deprioritized.

### CSDN / Juejin

- **Opening pattern:** Problem statement → environment / version → solution overview.
- **Length:** 1500–5000 characters; code blocks expected.
- **Format:** Working code, version-pinned dependencies, reproducible commands. Diagrams welcome.
- **CTA:** Source repo link at the bottom; canonical link in author bio.

### LinkedIn (long-form Article)

- **Opening pattern:** First-person professional anecdote → reframe to topic → industry insight.
- **Length:** 800–1800 words; readers skim from feed.
- **Format:** Bold subheadings every 150–200 words; one chart or quote-pull per 500 words.
- **CTA:** Comments-prompt question at the end; canonical link at the bottom with "Originally published at …".

### Medium

- **Opening pattern:** TL;DR or one-line subtitle (Medium's subtitle field is critical for distribution).
- **Length:** 1200–2500 words for the algorithm's "long-read" boost.
- **Format:** Pull quotes for tweetable lines; one image every 400–600 words; topic tags (max 5) at publish time.
- **CTA:** Canonical link to source via Medium's "Import a story" or `rel="canonical"`; follow CTA at the bottom.

### Substack

- **Opening pattern:** Editorial cold-open; tease the payoff in the subject line.
- **Length:** 1500–3500 words for Causal long-form; 800–1500 for digest format.
- **Format:** Bold subheads; pullout boxes; image at the top.
- **CTA:** Subscribe button mid-piece; canonical link at the bottom; cross-post toggle on if the source domain is also a Substack publication.

### Reddit

- **Opening pattern:** Genuine question or experience post; no marketing language.
- **Length:** 200–800 words for the post body; expect to defend in comments.
- **Format:** Plain text or light markdown; respect the subreddit's specific rules (no link drops, no surveys, etc.).
- **CTA:** None overt. Link only if asked in comments. Author flair / username should not be obviously promotional.

### Hacker News

- **Opening pattern:** "Show HN" / "Ask HN" prefix where appropriate; otherwise straight title.
- **Length:** Link post or text post under 500 words.
- **Format:** No marketing language; technical specifics in the title. Stay in the comment thread to answer questions.
- **CTA:** None. Post the link; the link is the CTA.

### X (Twitter) Threads

- **Opening pattern:** Hook tweet with a counter-intuitive claim or a number.
- **Length:** 5–12 tweets; each ≤ 280 chars; visuals on tweet 1 and tweet 5+.
- **Format:** Numbered ("1/", "2/") or implied threading; quotable single-line takeaways.
- **CTA:** Final tweet: link + ask for engagement.

### Vertical Media (36Kr, Huxiu, TechCrunch, The Verge, etc.)

- **Opening pattern:** Editorial — pitched via the outlet's contribution flow.
- **Length:** Defined by outlet (typically 800–2000 words).
- **Format:** Outlet's house style, editorial review.
- **CTA:** No CTA — the byline and bio link carry the attribution.

---

## Authority-Signal Reclaim Checklist (7 / 14 / 30 days)

Distribution is incomplete without recapturing the authority signals downstream platforms generate.

### Day 7 checkpoint

- [ ] Count inbound backlinks created in the past 7 days (use Ahrefs/Moz/manual scan or fetch from the linking platforms directly).
- [ ] Catalog new brand mentions on Tier 1 and Tier 2 platforms (linked + unlinked).
- [ ] Verify each Tier 1 syndication has the correct canonical or attribution.
- [ ] Confirm IndexNow ping for each platform-syndicated URL where applicable.
- [ ] Flag any platform where the cross-post is ranking above the canonical for the primary query.

### Day 14 checkpoint

- [ ] Run Stage 6 of `geo-citation-pipeline` (preferred-answer verification) — has any AI engine started citing the topic? Which surface gets cited?
- [ ] Identify which platforms' versions are being cited (you may discover Reddit or Zhihu is the cited surface, not the canonical — that's a signal, not a failure).
- [ ] Confirm no canonical-confusion penalty on the canonical URL (sudden organic-traffic drop or rank loss is the warning sign).
- [ ] Track engagement signals on each platform (upvotes, comments, saves) and rank the platforms by `(engagement × A-tier)` to inform the next plan.

### Day 30 checkpoint

- [ ] Run `/geo compete <domain> <competitors>` — has the competitor matrix changed for this topic?
- [ ] Catalog any earned coverage (industry outlets picked up the topic, podcasts referenced the canonical, etc.).
- [ ] Decide on a second-wave amplification: republish on platforms that missed the first wave, or escalate to a press push.
- [ ] Archive the result into `~/.geo-prospects/distribution/_archive/` for cross-plan trend analysis.

---

## Workflow

### Step 1: Resolve Source Article and Target Topic

1. Capture the canonical URL and the topic phrase.
2. Look up the topic in the latest `~/.geo-prospects/matrices/<domain>-*.md` if present — pull the planned `intent:` and `question:` for downstream use.
3. Confirm `geo-citation-pipeline` returned PIPELINE_READY for the URL — if not, abort with a clear error message and instruct the user to remediate first.

### Step 2: Filter Platforms by Audience Fit and Tier Eligibility

1. Apply the audience descriptor and region inputs to the pre-scored platform reference table.
2. Drop platforms with `F < 3` for the topic's audience.
3. Drop platforms that conflict with the topic content type (e.g., Stack Overflow for a marketing post; Xiaohongshu for an enterprise security topic).
4. Compute `Tier_score = A × F` and apply the C-tag bump/drop.
5. Confirm the final shortlist has at least 2 Tier 1 + 3 Tier 2 + 2 Tier 3 platforms. If not, document the gap.

### Step 3: Tag Each Selected Platform with AI-Corpus Coverage

1. Re-confirm each platform's C tag using the latest evidence (some platforms move from PARTIAL to KNOWN as new disclosures appear).
2. For any UNKNOWN platform retained in the plan, document the strategic reason (owned-audience retention, regional dominance, conversion).

### Step 4: Emit 14-Day Cadence Calendar

1. Slot each selected platform into the appropriate cadence day based on its tier.
2. Resolve scheduling conflicts using the conflict-avoidance rules.
3. Add `geo-citation-pipeline` re-run on day 14 to Stage 6 verify.

### Step 5: Generate Per-Platform Rewrite Briefs

1. For each platform in the plan, produce a brief that includes: opening pattern, length target, format constraints, CTA pattern, and canonical/attribution treatment.
2. For each Tier 2 rewrite, also produce a distinct first-100-word opening proposal (the engineering test of "distinct" is at least 60 % token-distinct from the canonical's first 100 words).
3. Save briefs as inline sections in the output file — do not generate the actual post bodies.

### Step 6: Wire Conflict-Avoidance Directives

1. For each platform that supports canonical, generate the exact `<link rel="canonical">` HTML or platform setting required.
2. For each platform that does not, generate the attribution sentence to paste.
3. Verify no two KNOWN-corpus platforms are scheduled within 24 h of each other.

### Step 7: Schedule 7/14/30-Day Reclaim Audits

1. Generate the three checkpoint TODO blocks (Day 7, Day 14, Day 30) as inline sections in the output.
2. Cross-link the Day 14 block to a `geo-citation-pipeline --verify` re-run command.
3. Cross-link the Day 30 block to a `/geo compete` invocation.

---

## Upstream and Downstream Skill Hooks

### Upstream

| Upstream skill | What this skill consumes |
|---|---|
| `geo-intent-matrix` | Topic, intent, question text for tier biasing |
| `geo-citation-pipeline` | PIPELINE_READY gate — required to proceed |
| `geo-brand-mentions` | Existing platform presence on Tier 1/2 (avoid recommending platforms where the brand already has poor reputation) |
| `geo-platform-optimizer` | Per-AI-engine preferences — used to bias Tier 1 selection (e.g., if the topic is Procedural and dev-focused, Stack Overflow + Hacker News rise in tier score) |

### Downstream

| Downstream skill | What this skill feeds it |
|---|---|
| `geo-citation-pipeline` (Day 14 re-run) | Trigger for Stage 6 verification across all syndicated surfaces |
| `geo-competitor-citation` (Day 30) | Trigger for full gap analysis on the topic |
| `geo-compare` | Distribution wave produces new entity mentions and inbound links — these become inputs to the next monthly delta |

---

## Output Format

Generate `~/.geo-prospects/distribution/<domain>-<topic-slug>-<YYYY-MM-DD>.md`:

```markdown
# GEO Distribution Plan: <Topic>

**Canonical URL:** <url>
**Topic:** <topic>
**Intent (from matrix):** <Definitional / Comparative / Procedural / Causal>
**Audience:** <descriptor>
**Region:** <global / cn / na / eu>
**Pipeline gate:** PIPELINE_READY (verified <YYYY-MM-DD>)
**Plan generated:** <YYYY-MM-DD>

---

## Tier Matrix

| Platform | A | F | C | Tier_score | Final tier | Notes |
|---|---|---|---|---|---|---|
| <platform> | 5 | 4 | KNOWN | 20 | T1 | <one-line> |
| … | | | | | | |

**Shortlist gap:** [None / list of missing tier slots]

---

## 14-Day Cadence

| Day | Platform | Tier | Rewrite intensity | Canonical handling |
|---|---|---|---|---|
| D0 | Main domain | — | None | Self-canonical |
| D+1 | <platform> | T1 | Distinct opening | <rel=canonical / attribution> |
| D+1 | <platform> | T1 | Distinct opening | <…> |
| D+3 | <platform> | T2 | Distinct opening + conclusion | <…> |
| … | | | | |

---

## Per-Platform Rewrite Briefs

### <Platform 1>

- **Opening pattern:** <…>
- **Length:** <…>
- **Format:** <…>
- **CTA:** <…>
- **Canonical/attribution:** <exact HTML or sentence>
- **Distinct first-100-word opening proposal:**

> <proposed opening>

### <Platform 2>

…

---

## Day 7 Reclaim Checkpoint

- [ ] Count inbound backlinks created in past 7 days
- [ ] Catalog new brand mentions on Tier 1 and Tier 2
- [ ] Verify canonical / attribution on each Tier 1 syndication
- [ ] Confirm IndexNow ping for syndicated URLs
- [ ] Flag any cross-post outranking the canonical

## Day 14 Reclaim Checkpoint

- [ ] Run `/geo pipeline <url> --verify` for Stage 6 preferred-answer verification
- [ ] Identify which surface AI engines cite
- [ ] Confirm no canonical-confusion penalty on the canonical URL
- [ ] Rank platforms by (engagement × A-tier)

## Day 30 Reclaim Checkpoint

- [ ] Run `/geo compete <domain> <competitors>` — has the gap matrix changed?
- [ ] Catalog earned coverage (industry outlets, podcasts, conferences)
- [ ] Decide on second-wave amplification
- [ ] Archive plan to `~/.geo-prospects/distribution/_archive/`

---

## Conflict-Avoidance Audit

- [ ] No two KNOWN-corpus platforms scheduled within 24 h of each other
- [ ] Every cross-post on a canonical-supporting platform has `rel="canonical"` to the main URL
- [ ] Every cross-post on a non-canonical platform has explicit attribution
- [ ] Reddit / Hacker News posts are authored in community-native voice (no marketing language)
- [ ] WeChat and Zhihu treatments cover different topic angles, not duplicated content

---

## Plan State

[PLAN_READY / PLAN_INCOMPLETE / BLOCKED]

- **PLAN_READY** — shortlist meets minimum tier coverage, all conflict rules pass
- **PLAN_INCOMPLETE** — missing Tier 1 or Tier 2 coverage; suggested actions listed
- **BLOCKED** — pipeline gate failed; remediate upstream first
```

---

## Quality Gates

- **Pipeline gate:** Never emit a plan when `geo-citation-pipeline` is BLOCKED for the canonical URL.
- **Minimum platform coverage:** Plans must include ≥ 2 Tier 1, ≥ 3 Tier 2 platforms. If coverage cannot be met given the audience/region inputs, downgrade to PLAN_INCOMPLETE and list the missing slots.
- **AI-corpus ratio:** At least 50 % of selected platforms must be tagged KNOWN. UNKNOWN-heavy plans drive owned-audience retention but not AI citation, and the output file must call that out explicitly.
- **Cadence rate limit:** Maximum 2 publish moves per day. The 14-day window provides enough slots that hitting this cap is never necessary.
- **Canonical conflict:** Any two near-verbatim posts on KNOWN-corpus platforms scheduled within 24 h is a hard fail — re-stagger before emitting.
- **Brief specificity:** Every per-platform brief must include the four required elements (opening pattern, length, format, CTA). Missing any element is a plan defect.

---

## Important Notes

- This plan is **strategy, not execution.** It tells you what to publish where and in what order; it does not write the platform-specific posts. Use `geo-content` (or your in-house team) to produce the actual copy from each brief.
- The per-platform rewrite briefs are **constraints, not templates.** Two writers given the same brief should produce visibly different posts that both satisfy the constraints.
- **UNKNOWN platforms are not bad — they are owned.** WeChat Official Accounts and Substack newsletters drive subscriber retention and direct conversion, which over time create the engagement signals that move PARTIAL platforms toward KNOWN status. Keep at least one UNKNOWN platform per plan for owned-audience compounding.
- **Reddit posting is high-risk.** Each subreddit has its own rules; one wrong post can earn a permanent ban and damage the brand on the strongest AI-citation surface. When in doubt, prefer Quora or LinkedIn over Reddit for the same content angle.
- **Wikipedia is mentioned for completeness but rarely actionable in a 14-day window.** Wikipedia eligibility requires established sourcing across multiple independent secondary outlets; treat it as the **outcome of months of distribution**, not a destination in any single plan.
- **Region gating matters.** A `region: cn` plan should not waste tier slots on Western platforms (Medium, Substack) unless the brand has an explicit English-language strategy. A `region: global` plan must include both Eastern and Western Tier 1 entries.
