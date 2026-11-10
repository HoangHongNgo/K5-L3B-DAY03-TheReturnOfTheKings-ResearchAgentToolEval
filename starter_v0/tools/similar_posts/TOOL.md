---
name: similar_posts
track: core
kind: live_api
provider: RapidAPI Twitter API45
requires_env: [RAPIDAPI_KEY, RAPIDAPI_TWITTER_HOST]
inputs: [reference_text, reference_screenname, search_type, limit, timeline_limit]
outputs: [query, items]
side_effect: false
---
# similar_posts

Finds X/Twitter posts resembling a supplied reference post. It derives a search
query from the reference text and reranks candidates with a hybrid of reference
term coverage (45%), Jaccard overlap (35%), and matching word pairs (20%). Exact
duplicates and candidates scoring below 0.15 are excluded. Each item includes a
`similarity_score` and an explainable `similarity_components` breakdown.

Alternatively, `reference_screenname` builds a topic profile from up to
`timeline_limit` recent posts, searches once using recurring profile terms, and
excludes the reference account. This mode uses two RapidAPI requests total.
