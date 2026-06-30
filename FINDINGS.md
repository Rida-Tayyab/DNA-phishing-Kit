# Findings — Phishing Kit DNA Fingerprinter

## Headline result

The classifier hits **88.0% top-1 accuracy** on families that have 5 or more kit instances in the dataset. That's the number I'm most proud of — it means the DNA fingerprint actually works when there's enough data for a family to form a real cluster in vector space.

When the model is confident (top-5 neighbours agree 4/5 or 5/5), accuracy reaches **86.2%**. So the confidence score isn't decorative — it's a real signal you can trust. Overall accuracy across the whole dataset (including rare families) is 59.0%, which is lower because of the small-family limitation described below.

## A normalization bug I found and fixed

While verifying the clone finding below, I noticed something didn't add up — a duplicate check on the raw FAISS vectors showed 99.4% of all kits had a near-zero-distance match, including kits from completely unrelated families (e.g. `m1` matching `newPost`, two kits I'd already manually inspected and knew had different exfiltration code).

Tracing it back, the bug was in how the hybrid vector was built. The 384-dim text embedding from sentence-transformers comes out L2-normalized (norm ≈ 1.0) by default. But my 55-dim structured feature vector — things like `php_line_count` and `total_files` — was being passed in raw, unnormalized, with a vector norm in the thousands. When I concatenated the two and called `faiss.normalize_L2()` on the combined vector, the huge structured-feature magnitude completely swamped the text embedding, shrinking its contribution to roughly 1/17,000th of the final vector. Effectively the "DNA fingerprint" was almost entirely just a handful of raw numeric features, with no real text signal at all — which is why unrelated kits with similar file counts were colliding.

The fix: compute min-max normalization stats (`col_min`, `col_max`) across the full structured feature matrix once, save them to `normalization_stats.json`, and apply that exact same scaling both when building the index and when classifying a new kit at inference time. After rebuilding the index with properly normalized vectors, accuracy on families with 5+ kits went from 82.9% to 88.0%, and the duplicate-distance distribution shifted to make sense — same-family pairs (`dhl-cryptre-news ↔ dhl-cryptre-news`, `SEUR_ES ↔ SEUR_ES`) now dominate the near-duplicate matches instead of random cross-family collisions.

## The clone discovery

While digging through the dataset I found 421 kit families where every single instance has an *identical* feature fingerprint — 1,955 kit instances total, all zero-distance matches in the vector space.

What this means: these aren't 421 families with similar code, they're families where the exact same kit was copied and redeployed over and over. Family `53` alone has 206 kits with byte-for-byte identical PHP — same line count, same structure, everything.

This tells you something real about how phishing kits actually spread. They're not hand-built per attack. Someone builds a kit once, sells or shares it, and it gets deployed across hundreds of different domains by different people, completely unchanged. The DNA fingerprint approach works *because* this cloning happens — if every kit were unique, there'd be nothing to cluster.

## Why confidence calibration matters

When the classifier is confident, it's right more often (86.2% vs 59.0% baseline). That's not just a nice stat — it means the system knows when it knows. In a real security tool, that's the difference between something an analyst can trust to auto-flag versus something that needs manual review every time. A model that's equally "confident" whether it's right or wrong is useless. This one isn't.

## Email vs Telegram — the exfiltration split

46% of kits send stolen credentials via email, 44% via Telegram. Almost an even split, and that's interesting on its own — it's basically a coin flip between an "old school" approach (mail()) and a "modern" approach (Telegram bot API). 

Because it's such a clean binary split, it became one of the strongest individual features in the whole fingerprint — two kits sharing the same exfiltration method is a meaningful signal toward them being the same family, even before looking at anything else.

## What I'd fix next

The duplication issue is now properly understood rather than hidden — the deduplication problem was real (421 families really are exact clones, 1,955 instances total) but I confirmed it isn't inflating the index itself thanks to the normalization fix above. The remaining open item there: my evaluation excludes the queried kit's own hash from its neighbour search, but a cleaner long-term fix would be deduplicating the dataset before indexing — keep one representative per exact-duplicate cluster and weight it by how many times it appeared — to get an even more honest sense of performance on genuinely distinct kits.

The bigger limitation now is small families. Anything with under 5 instances only hits 18.1% accuracy because there's no real cluster to find — the nearest neighbours end up being whatever's geometrically closest by accident, not a real match. With more time I'd look into few-shot approaches or pull in extra signal (hosting patterns, registration dates) to help with these rare cases.