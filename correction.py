"""
correction.py

Turns a verified ground_truth dict into a short canonical profile -- the
text you'd inject as context if a registry entry existed and an agent
retrieved it. This is condition 3's context block.
"""


def to_canonical_profile(name: str, gt: dict) -> str:
    lines = [
        f"{name} -- verified profile",
        f"Founded: {gt['founded_year']}",
        f"Headquarters: {gt['hq']}",
        f"Category: {gt['category']}",
        f"Pricing model: {gt['pricing_model']}",
        f"Key products: {', '.join(gt['key_products'])}",
    ]
    for fact in gt["notable_facts"]:
        lines.append(f"Verified fact: {fact}")
    return "\n".join(lines)
