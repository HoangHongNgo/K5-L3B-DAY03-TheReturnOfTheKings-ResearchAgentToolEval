---
name: deduplicate
track: core
kind: local_formatter
provider: none
requires_env: []
inputs: [items]
outputs: [items, item_count, removed_count]
side_effect: false
---
# deduplicate

Removes repeated research results while preserving the first occurrence. Items
are duplicates when their normalized URLs match (tracking query strings and
fragments are ignored) or their normalized titles match. Items without either
field are retained. Invalid input returns an error object.
