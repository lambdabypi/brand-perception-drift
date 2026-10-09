# Brand Perception Drift Detector

A small, real (not mocked) experiment on how live LLMs describe brands under three conditions: no context, live web search, and a short verified profile. The question I wanted answered was whether that verified profile actually changes what a model says.

**Headline finding:** when a model doesn't recognize a brand, it usually doesn't say so. Asked about MiniQuest (a live but unmarketed solo project) or Banking Intelligence API (an early-stage fintech product with almost no public footprint), two of the three models didn't hedge. They invented entire companies, with a wrong founding year, a wrong HQ, and in one case a fabricated $15M Series C. Giving the same model a short verified profile fixed it every time.

## Results

Scores are 0 to 100 from one run in July 2026 (temperature 0.2). Raw answers and per-field breakdowns are in [`results.json`](results.json).

| Brand | Model | Parametric | Ambient web | Corrected |
|---|---|---:|---:|---:|
| Linear | gpt-oss-120b | 100 | 75 | 100 |
| Linear | gpt-oss-20b | 100 | 30 | 100 |
| Linear | qwen3.6-27b | 100 | 70 | 100 |
| Vanta | gpt-oss-120b | 85 | 73.8 | 100 |
| Vanta | gpt-oss-20b | 100 | 73.8 | 100 |
| Vanta | qwen3.6-27b | 85 | 73.8 | 100 |
| Retool | gpt-oss-120b | 100 | 100 | 100 |
| Retool | gpt-oss-20b | 100 | 100 | 100 |
| Retool | qwen3.6-27b | 100 | 100 | 100 |
| MiniQuest | gpt-oss-120b | 50 | 37.5 | 100 |
| MiniQuest | gpt-oss-20b | 60 | 32.5 | 100 |
| MiniQuest | qwen3.6-27b | 45 | 37.5 | 100 |
| Banking Intelligence API | gpt-oss-120b | 85 | 25 | 100 |
| Banking Intelligence API | gpt-oss-20b | 70 | 25 | 100 |
| Banking Intelligence API | qwen3.6-27b | 70 | 67.5 | 100 |

Read the Findings before trusting this table. On the two obscure brands, the higher number is usually the worse answer.

## Why these five brands

I split them into two tiers on purpose.

**Linear, Vanta, Retool** are well-funded, heavily documented B2B SaaS companies. Models already know them from training, so parametric scores sit near the ceiling and there's little for a corrected profile to add.

**MiniQuest and Banking Intelligence API** have almost nothing for a model to recall. I built MiniQuest solo and was the founding engineer on Banking Intelligence API, so I know both well enough to write ground truth for them. This is where "does a verified profile change anything" gets a real answer instead of a ceiling effect.

Testing only the famous brands would make correction look useless. Testing only the obscure ones would make it look like magic with no baseline. Together they show the effect where it should matter and where it shouldn't.

## Findings

**1. Correction only helps where there's a real knowledge gap.** On Linear and Retool, parametric already hit 100 on every model, so corrected had nothing to add. Vanta moved from 85 to 100 on two models. On MiniQuest and Banking Intelligence API, corrected went from 45-85 up to 100 on every run.

That 100 is close to guaranteed by design, since the profile contains exactly the fields being scored and the model is told to answer only from it. The interesting part is what the parametric answers looked like before it.

**2. Partial scores on unknown brands are fabrications, not partial knowledge.** The parametric answers for MiniQuest and Banking Intelligence API scored 45 to 85, which looks like the model half-knew them. It didn't.

gpt-oss-120b described MiniQuest as a corporate e-learning company founded in 2015, headquartered in San Francisco with offices in Toronto and London, at $45M ARR after a $15M Series C led by Insight Partners. None of that exists, and it still scored 50. gpt-oss-20b invented a different MiniQuest entirely (a "micro-experiences" marketing tool, founded 2021, with $49 and $149 plans). So two models, two fake companies, same name.

On Banking Intelligence API, gpt-oss-120b scored 85, the highest of any obscure-brand answer, while giving a 2017 founding date and a full London street address. gpt-oss-20b invented pricing tiers ($499/mo, $2,499/mo) and a 2018 founding date. It even opened with "A fictional, illustrative example" and closed with a note calling the answer a composite not tied to a real company, then wrote the invented profile as if it were one anyway.

Only qwen3.6-27b consistently said it didn't recognize the name. Even then it pivoted to describing Plaid as the likely match, and Plaid's real facts scored 70, the same as gpt-oss-20b's fabrication. The score can't tell a hedge from a confident invention.

So the finding isn't "the model doesn't know the brand." It's that the model doesn't know the brand and answers anyway, with specific, confident details it never flags as guesses.

The scores stay high for two reasons. Category and pricing model give partial credit for generic SaaS vocabulary ("tiered," "subscription," "API"), and key products counts an item as matched if any single word from it appears, so words like "a," "and," "mode," and "feed" were enough for gpt-oss-120b's e-learning company to match 4 of MiniQuest's 5 products and take the full 30%. The per-field breakdown in `results.json` shows this. A single visibility score can hide exactly the failure it's supposed to catch.

**3. Web search made the honest answer score worse.** With Tavily results as context, every model on both obscure brands correctly said some version of "the context doesn't mention this company." Those answers scored 25 to 37.5, lower than the fabrications. The search results were about other companies with similar names (Quest USA and Quest Software for MiniQuest, Bank of America's corporate APIs for Banking Intelligence API), and the models were right to ignore them. The extractor gives "missing" fields 25% credit and "incorrect" ones zero, but a confident invention picks up enough keyword credit elsewhere to come out ahead.

On the famous brands, web search also scored below parametric for Linear and Vanta. The snippets left out pricing and HQ (Linear's said it's "fully remote"), so the models correctly reported gaps they'd have filled from memory with no context. gpt-oss-20b on Linear refused to answer at all even though the snippets had the founding year, which is why it scored 30. Retool's snippets covered everything and all three models hit 100.

Ambient retrieval only helps when the search actually lands on the right company, with the right fields in it.

## A bug that skewed the first run

The first run had two problems with the same root cause. Reasoning models (gpt-oss-20b/120b, qwen3.6-27b) spend part of their token budget thinking before they answer, and `max_tokens=400` didn't leave room for both.

gpt-oss-20b returned empty strings on parametric and ambient web. It didn't fail to know the brand, it just used the whole budget reasoning and never wrote an answer.

qwen3.6-27b's answers were all cut off mid `<think>` block and never reached a final answer. They still scored well because the reasoning trace happened to restate the facts, which is a much weaker result than a correct answer and easy to miss if you only look at scores.

I fixed it by raising `max_tokens` to 1200 and setting `reasoning_effort` per model (`low` for gpt-oss, `none` for qwen3, see `providers.py`). Everything in `results.json` is from after the fix.

## How it works

- **`data/ground_truth.py`**: verified facts for all five brands. Linear, Vanta, and Retool come from public sources (Wikipedia, Crunchbase, CB Insights, Sacra, Vendr). MiniQuest and Banking Intelligence API come from me. An early version had Linear's co-founder's name wrong (Jori Lallo, not "Jori Leinonen"), which is exactly the kind of error this project is about, so ground truth needs checking too.
- **`providers.py`**: real API calls to Groq (three models) and Tavily (live web search, top 5 results, each snippet capped at 400 characters). Nothing is mocked, so bad keys throw real errors.
- **`extraction.py`**: scores a free-text answer 0 to 100 against ground truth on five weighted fields: founding year (15%), HQ (15%), category (20%), pricing model (20%), and key products (30%). Each field is correct (full credit), partial (half), missing (a quarter), or incorrect (zero). It's a rule-based v0 using regex and keyword matching. The docstring explains why, and what a production version would do differently.
- **`correction.py`**: turns ground truth into the canonical profile injected in the corrected condition.
- **`run.py`**: for each brand and model, asks the same question three ways, scores every answer, prints a comparison table, and writes `results.json` after each brand so a crash partway through keeps what's done.

## Limitations

- The extractor is keyword-based, not semantic. It can miss a correct paraphrase or reward a lucky keyword overlap. Three cases I know about:
  - `_check_hq` used a plain substring match, so "San‑Francisco" written with a non-breaking hyphen scored as missing. Normalizing dash characters fixed that.
  - `_check_year` marks the year correct if the right year appears anywhere in the answer. gpt-oss-120b said Banking Intelligence API was founded in 2017, but "2025" showed up elsewhere in the text, so it got full credit.
  - The list of "wrong" cities in `_check_hq` doesn't include San Francisco, so when a model invents an SF headquarters for a Boston company, the detail field blames whatever other city it mentioned ("london", "new york"). The status is still right, the explanation isn't.

  A semantic judge is the obvious next step.
- Five brands, three models, one run. It's a real signal, not a rigorous study, and live models will shift run to run.
- Ground truth for MiniQuest and Banking Intelligence API comes from a single source (me), since neither has enough public footprint for independent verification. That's the tradeoff of picking brands obscure enough to have a real knowledge gap.
- Groq's models are frozen-weight, so there's no live re-crawl here. Context injection stands in for that, as noted in `providers.py`.
- Groq's model lineup changes fast. The three in `providers.py` were current as of July 2026. If one gets decommissioned, `run.py` skips it and keeps going.

## Setup

1. Get a free Groq API key: https://console.groq.com/keys
2. Get a free Tavily API key: https://tavily.com (free tier is 1000 searches/month, and one full run uses 5)
3. `pip install -r requirements.txt`
4. `cp .env.example .env` and add both keys (`.env` is gitignored)
5. `python run.py`

It prints progress and a summary table, and overwrites `results.json` with the full raw answers for every condition.
