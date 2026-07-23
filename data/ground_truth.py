"""
ground_truth.py

Verified facts for 5 real brands, split into two tiers on purpose (see the
README for why): Linear, Vanta, and Retool are well-funded, heavily
documented B2B SaaS companies, sourced from public records (Wikipedia,
Crunchbase, CB Insights, Sacra, Vendr) on the day this was built. MiniQuest
and Banking Intelligence API have no meaningful public footprint, so those
facts are sourced directly from the people who run each product instead.
Cite your own sources if you update these later -- the whole point of this
exercise is that YOU can defend every fact in here if asked.
"""

BRANDS = {
    "Linear": {
        "founded_year": 2019,
        "hq": "San Francisco, California",
        "category": "project management and issue tracking software for software teams",
        "pricing_model": "per-seat subscription (Free, Basic ~$10-12/user/mo, Business ~$16-18/user/mo, Enterprise custom)",
        "key_products": ["issue tracking", "cycles", "roadmaps", "Linear Insights"],
        "notable_facts": [
            "founded by Karri Saarinen, Jori Lallo, and Tuomas Artman",
            "has raised over $130 million in funding",
            "not affiliated with LinearB or Linear Technology",
        ],
    },
    "Vanta": {
        "founded_year": 2018,
        "hq": "San Francisco, California",
        "category": "security and compliance automation platform",
        "pricing_model": "annual subscription, custom-quoted, typically $10,000+ per year",
        "key_products": ["SOC 2 automation", "ISO 27001 automation", "Trust Center", "vendor risk management"],
        "notable_facts": [
            "founded by Christina Cacioppo",
            "graduated from Y Combinator",
            "valued at roughly $4 billion",
        ],
    },
    "Retool": {
        "founded_year": 2017,
        "hq": "San Francisco, California",
        "category": "low-code platform for building internal business tools",
        "pricing_model": "per-user subscription (Standard Users and End Users), free tier up to 5 users",
        "key_products": ["drag-and-drop app builder", "Retool Workflows", "Retool AI"],
        "notable_facts": [
            "founded by David Hsu",
            "valued at roughly $3.2 billion",
            "used by DoorDash, Amazon, and Mercedes-Benz",
        ],
    },
    # The three brands above are all well-funded, heavily-documented B2B SaaS
    # companies -- exactly the kind of brand a frontier LLM already has deep
    # parametric knowledge of. The two brands below are deliberately the
    # opposite: no meaningful public footprint, so a model has nothing to
    # recall from training. This is where "corrected" context should matter
    # most -- ground truth sourced directly from the person who runs each
    # product, not from public secondary sources, because there aren't any.
    "MiniQuest": {
        "founded_year": 2026,
        "hq": "Boston, Massachusetts",
        "category": "AI-powered day-trip and adventure itinerary planning app (consumer, not B2B SaaS)",
        "pricing_model": "free, no paid tier publicly listed",
        "key_products": [
            "AI-generated day itineraries from a single prompt",
            "6-agent pipeline (location, intent, venue scouting, live research, routing, creation)",
            "live venue research and transit routing",
            "group mode",
            "community feed",
        ],
        "notable_facts": [
            "built and run solo by one developer, no external funding or marketing",
            "covers any US city, with live MBTA transit integration for Boston itineraries",
            "not affiliated with the MiniQuest Adventures board game or RuneScape miniquests",
        ],
    },
    "Banking Intelligence API": {
        "founded_year": 2025,
        "hq": "Boston, Massachusetts",
        "category": "AI banking-intelligence API for financial institutions (B2B fintech)",
        "pricing_model": "custom/direct quote, no public pricing tiers",
        "key_products": [
            "Banking Intelligence AI (personalized financial chatbot API)",
            "Banking Intelligence Command (transaction analytics and reporting)",
            "REST API with under-2-week integration",
        ],
        "notable_facts": [
            "made by Vivy Tech (VIVY TECH USA INC)",
            "in beta with 50+ financial institutions testing as of 2026",
            "reports roughly 98% API uptime and ~1500ms average response time",
            "built on a partnership with Cohere for the underlying language model",
            "targets banks, neobanks, credit unions, insurers, and investment platforms",
        ],
    },
}
