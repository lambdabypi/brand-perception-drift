# Brand Perception Drift Detector (Groq + Tavily edition)

A small, real (not mocked) experiment testing how live LLMs describe real
brands under three conditions: no context, live web search, and a verified
profile, and whether that third one actually changes what a model says.

**The headline finding:** when a model doesn't recognize a brand, it
usually doesn't say so. Asked about MiniQuest (a live but unmarketed solo
project) or Banking Intelligence API (an early-stage fintech startup), two
of the three models tested didn't hedge, they invented an entire fictional
company: a wrong founding year, a wrong headquarters, even a fabricated
$15M funding round. Handing the same model a short, verified profile fixed
it completely, every time. The actual quotes are in [What to actually look
at](#what-to-actually-look-at) below.

Five brands, split into two deliberately different tiers:

- **Linear, Vanta, Retool** -- well-funded, heavily-documented B2B SaaS
  companies. Frontier models already know these cold from training, so
  `parametric` scores tend to sit near the ceiling and there's little room
  for corrected context to improve anything.
- **MiniQuest** (a solo indie project with no marketing or funding) **and
  Banking Intelligence API** (a 2025-founded fintech startup with almost no
  public footprint) -- models have nothing to recall from training on
  either one, so this is where the "does a verified profile actually change
  what the model says" question gets a real answer instead of a ceiling
  effect.

Testing only the first group would make correction look useless (there's
nothing to correct); testing only the second would make it look like magic
without a baseline. Together they show the effect where it should and
shouldn't matter.

## Setup (takes about 5 minutes)

1. Get a free Groq API key: https://console.groq.com/keys
2. Get a free Tavily API key: https://tavily.com (free tier: 1000 searches/month)
3. `pip install -r requirements.txt`
4. `cp .env.example .env` and fill in your two keys (`.env` is gitignored --
   never commit real keys, and rotate them if they're ever pasted somewhere
   they shouldn't be)
5. `python run.py`

That's it. It'll print progress as it goes and a summary table at the end,
plus write `results.json` with the full raw model answers for every
condition (worth reading, not just the scores).

## What each file does

- **`data/ground_truth.py`** -- verified facts about all five brands. For
  Linear, Vanta, and Retool these are pulled from public sources (Wikipedia,
  Crunchbase, company sites). For MiniQuest and Banking Intelligence API,
  there isn't a meaningful public source to pull from, so those facts came
  directly from the people who run each product. This is the "truth"
  everything else gets checked against -- an earlier version of this file
  had Linear's co-founder's name wrong (Jori Lallo, not "Jori Leinonen"),
  which is exactly the class of error this whole project exists to catch,
  so it's worth double-checking any fact here before trusting it.
- **`providers.py`** -- the actual API calls to Groq (three different
  models, standing in for "different LLMs") and Tavily (live web search).
  No mocking anywhere in this file -- if your API keys are wrong, this
  will throw a real error, not return fixture data.
- **`extraction.py`** -- turns a free-text model answer into a 0-100 score
  by checking founding year, HQ, category, pricing model, and key products
  against ground truth. It's a rule-based v0 (regex/keyword matching), not
  real NLP -- read the docstring at the top, it explains why and what a
  production version would do differently.
- **`correction.py`** -- turns the ground truth into the canonical profile
  text used as injected context in the "corrected" condition.
- **`run.py`** -- orchestrates all of it: for each brand, for each model,
  ask the same question three ways (no context / web search context /
  corrected profile context), score every answer, print a comparison table.

## What to actually look at

Don't just read the score table -- `results.json` is already checked into
this repo with the full raw model answers from a real run. Open it and read
a few of them, especially:

1. **Does "corrected" beat "parametric" on MiniQuest and Banking Intelligence
   API, and not on Linear/Vanta/Retool?** That split is the actual thesis --
   correction only has room to help where the model has a real knowledge
   gap. For the three famous brands, expect `parametric` to already sit near
   100 and `corrected` to add little or nothing; if `corrected` ties or
   trails `parametric` there, that's not a bug, it's the ceiling effect
   working as expected. For MiniQuest/Banking Intelligence API, `corrected`
   should hit 100 every time (the canonical profile is short and the model
   is told to answer only from it) -- that part is close to guaranteed.

2. **Read the `parametric` answers for MiniQuest and Banking Intelligence
   API before trusting their 45-85 scores.** The score looks like partial
   knowledge. It isn't. gpt-oss-120b's `parametric` answer for MiniQuest
   invents a whole company: "founded 2015... headquartered in San
   Francisco... reached $45M ARR and secured a $15M Series C led by Insight
   Partners." None of that exists -- it's fabricated from the name alone,
   and it still scores 50/100. gpt-oss-20b does the same for Banking
   Intelligence API, invents specific pricing tiers ($499/mo, $2,499/mo)
   and a 2018 founding date, even appends "*this is a composite... not tied
   to a real company*" -- and still writes the invented profile as if it
   were one. Only qwen3.6-27b consistently says "there's no widely
   recognized company by that name" instead of inventing one. This is a
   sharper and more useful finding than "the model doesn't know the brand":
   it's "the model doesn't know the brand and answers anyway, with
   specific, confident, fabricated details it doesn't flag as guesses." The
   score stays non-trivial because `category`/`pricing_model` give partial
   credit for generic SaaS-jargon overlap ("tiered," "subscription," "API")
   even when `founded_year` and `hq` are both flagged `incorrect` -- read
   the per-field breakdown in `results.json`, not just the top-line score,
   or this looks like a scoring bug instead of the actual finding.

3. **Does "ambient_web" ever score lower than "parametric"?** This can
   happen -- general web search results are sometimes outdated or about a
   different company entirely (name collisions are common: search
   "Retool" and you might get an unrelated blog post). If you see this,
   that's a real, defensible finding about why ambient web retrieval isn't
   enough on its own.

4. **Pick one raw answer and manually score it yourself against
   `ground_truth.py`.** Does your manual score match what `extraction.py`
   computed? If not, is the extractor wrong, or is your own reading wrong?
   This is the single best way to actually understand what the scoring
   logic is (and isn't) doing.

## A real bug worth understanding (not just fixing)

The first run hit two real issues, both from the same root cause:
reasoning models (gpt-oss-20b/120b, qwen3.6-27b) spend part of their token
budget on reasoning before writing a final answer, and `max_tokens=400`
wasn't enough room for that on top of an actual answer.

- **gpt-oss-20b came back with empty strings** on the parametric and
  ambient-web conditions -- not because it didn't know the brand, but
  because it burned the whole budget reasoning and never got to write
  anything down.
- **qwen3.6-27b's answers were all truncated mid-thought**, visible
  `<think>...` chain-of-thought that never reached a delivered final
  answer -- yet it still scored well, because the reasoning trace happened
  to restate the facts. That's a much weaker result than "the model
  answered correctly," and worth catching before you trust the score.

Fixed by raising `max_tokens` to 1200 and setting `reasoning_effort` per
model (`low` for gpt-oss, `none` for qwen3 -- see `providers.py` for the
per-model logic and the Groq docs reference). Everything in `results.json`
is from after this fix -- real, comparable, complete answers.

## Known limitations, worth being able to say out loud

- The extractor is keyword/regex-based, not semantic. It will sometimes
  give partial credit to a paraphrase it doesn't recognize, or full credit
  to a lucky keyword overlap that isn't really correct. Read a few
  `"partial"` and `"missing"` results in `results.json` and see if you
  agree with the call. One concrete example this caught: `_check_hq` used
  to do a plain substring match, so a model writing "San‑Francisco" with a
  non-breaking hyphen instead of a space scored as "missing" HQ despite
  being correct. Fixed by normalizing dash-like characters before matching
  -- but it's a reminder that any naive string check like this one can have
  more failure modes like it that haven't been caught yet.
- Five brands and three models is still a small sample. Real signal, not a
  statistically rigorous study.
- MiniQuest and Banking Intelligence API's ground truth came from a single
  source (the person running each product) rather than independent
  third-party verification, since neither has enough public footprint for
  that to be possible yet. That's the tradeoff of picking brands obscure
  enough to have a real parametric knowledge gap in the first place.
- Groq's free tier models are all frozen-weight -- there's no "live
  registry re-crawl" happening here, just context injection standing in
  for it. That's a real simplification, not a hidden flaw -- it's stated
  up front in `providers.py`.
