---
name: similar_posts
track: core
kind: live_api
provider: RapidAPI Twitter API45
requires_env: [RAPIDAPI_KEY, RAPIDAPI_TWITTER_HOST]
inputs: [reference_text, search_type, limit]
outputs: [query, items]
side_effect: false
---
# similar_posts

Finds X/Twitter posts resembling a supplied reference post. It derives a search
query from the reference text and reranks the returned candidates using Jaccard
term similarity. Exact text duplicates and candidates with no shared meaningful
terms are excluded. Each returned item includes a `similarity_score`.
