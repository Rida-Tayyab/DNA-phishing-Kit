# Findings — Phishing Kit DNA Fingerprinter

## Headline result

The classifier hits **82.9% top-1 accuracy** on families that have 5 or more kit instances in the dataset. That's the number I'm most proud of — it means the DNA fingerprint actually works when there's enough data for a family to form a real cluster in vector space.

When the model is confident (top-5 neighbours agree 4/5 or 5/5), accuracy jumps to **84.5%**. So the confidence score isn't decorative — it's a real signal you can trust. Overall accuracy across the whole dataset (including rare families) is 57.5%, which is lower because of the next finding.

## The clone discovery

While digging through the dataset I found 421 kit families where every single instance has an *identical* feature fingerprint — 1,955 kit instances total, all zero-distance matches in the vector space.

What this means: these aren't 421 families with similar code, they're families where the exact same kit was copied and redeployed over and over. Family `53` alone has 206 kits with byte-for-byte identical PHP — same line count, same structure, everything.

This tells you something real about how phishing kits actually spread. They're not hand-built per attack. Someone builds a kit once, sells or shares it, and it gets deployed across hundreds of different domains by different people, completely unchanged. The DNA fingerprint approach works *because* this cloning happens — if every kit were unique, there'd be nothing to cluster.

## Why confidence calibration matters

When the classifier is confident, it's right more often (84.5% vs 57.5% baseline). That's not just a nice stat — it means the system knows when it knows. In a real security tool, that's the difference between something an analyst can trust to auto-flag versus something that needs manual review every time. A model that's equally "confident" whether it's right or wrong is useless. This one isn't.

## Email vs Telegram — the exfiltration split

46% of kits send stolen credentials via email, 44% via Telegram. Almost an even split, and that's interesting on its own — it's basically a coin flip between an "old school" approach (mail()) and a "modern" approach (Telegram bot API). 

Because it's such a clean binary split, it became one of the strongest individual features in the whole fingerprint — two kits sharing the same exfiltration method is a meaningful signal toward them being the same family, even before looking at anything else.

## What I'd fix with more time

The first thing I'd fix is the duplication problem. Right now 28% of the dataset (1,955 of 6,831 kits) is exact clones, which means my evaluation set technically includes near-duplicate training examples. I handled this for evaluation by excluding the queried kit's own hash from its neighbour search, but a cleaner fix would be deduplicating the dataset before building the index in the first place — keep one representative per exact-duplicate cluster, and weight that cluster by how many times it appeared. That would give a more honest sense of how the classifier performs on genuinely distinct kits rather than getting credit for finding obvious copies.

The second thing is small families. Anything with under 5 instances only hits 21.7% accuracy because there's no real cluster to find — the nearest neighbours end up being whatever's geometrically closest by accident, not a real match. With more time I'd look into few-shot approaches or pull in extra signal (hosting patterns, registration dates) to help with these rare cases.