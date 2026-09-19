# Authoring curriculum content

Everything a learner reads lives here as YAML, validated and compiled into `curriculum.json`. This file is the how-to for authoring and maintaining it.

## Build

```bash
make content
```

That is the only command you need. It adds any missing UUIDs, validates everything, and writes `curriculum.json`.

Success looks like:

```
✓ curriculum.json v1
  1 phase(s), 8 topic(s), 33 objective(s), 49 step(s)
  91 unique uuid(s), ~25h of core content
```

Any failure prints `✗` with the file and the problem, and **writes nothing** — the previous good artifact stays in place.

<details>
<summary>The two underlying steps, if you need them separately</summary>

```bash
make uuids      # add uuids to anything new
make compile    # validate and build
```

`make content` runs both in that order. Injection must come first, because compilation requires every entity to have a UUID.
</details>

## Layout

```
content/
├── curriculum.meta.yaml        version number
├── curriculum.json             BUILD OUTPUT — never edit by hand
├── schemas/
│   ├── phase.schema.json       BUILD OUTPUT — generated from ../../content_model.py
│   └── topic.schema.json       BUILD OUTPUT — generated from ../../content_model.py
└── phases/
    └── phase1/
        ├── _phase.yaml         phase metadata + ordered topic slugs
        ├── how-llms-work.yaml  one file per topic, named by slug
        └── …
```

Topic files are named by slug. **Order is not in the filename** — it comes from the `topics:` list in `_phase.yaml`.

## Common tasks

### Change wording or a link

Edit the topic file, then `make content`.

### Add a step

Add an entry to the topic's `steps:` list. Omit `uuid` — injection fills it in.

```yaml
- order: 5
  action: read              # watch | read | practice | explore
  title: Context Windows    # short noun phrase, reads after the action
  description: >-
    What to do and what to take away.
  resources:
    - label: Anthropic — Context windows
      url: https://platform.claude.com/docs/en/build-with-claude/context-windows
```

Renumber the `order` values of any steps after it. Then `make content`.

### Add a step with provider alternatives

Use `variants` when each provider documents the same concept and a learner needs only one:

```yaml
- order: 3
  action: read
  title: Token Pricing Models
  description: >-
    Shared across all variants — the concept is the same.
  variant_dimension: provider     # provider | coding_tool
  variants:
    - key: anthropic              # listed first = default tab
      label: Anthropic
      resources:
        - label: Pricing
          url: https://platform.claude.com/docs/en/about-claude/pricing
    - key: openai
      label: OpenAI
      resources:
        - label: Pricing
          url: https://platform.openai.com/docs/pricing
```

**`resources` or `variants`, never both.** The test: *would reading all of them teach more than reading one?* Yes → `resources`. No → `variants`.

### Add a topic

1. Create `content/phases/phaseN/<slug>.yaml`
2. Add `<slug>` to `topics:` in `_phase.yaml`, in the position you want it
3. `make content`

Forgetting step 2 is an error, not a silent omission.

### Add a phase

1. Create `content/phases/phaseN/` with `_phase.yaml` and its topic files
2. Set `order:` to its position in the curriculum
3. Mark the final topic `is_capstone: true`
4. `make content`

### Add a third provider option

Add another entry to `variants:` on each affected step. No schema change is needed — `key` is a pattern, not a fixed list. In Phase 1 that is five steps across three files.

### Mark a step optional

```yaml
optional: true
```

A display tag only. The step still appears and is still checkable; it just signals "extra depth, skip if short on time". Exclude it from the topic's `estimated_minutes`.

## Errors and what they mean

| Message | Cause | Fix |
|---|---|---|
| `failed validation: at <path>: …` | A field is missing, the wrong type, or an invalid value | Read the path — it points at the exact entry. The actual rule lives in `content_model.py` (`schemas/topic.schema.json` is generated from it, for editor autocomplete) |
| `lists topics with no file: X` | `_phase.yaml` names a slug that has no `X.yaml` | Create the file, or remove the slug |
| `contains topic files not listed in _phase.yaml: X` | `X.yaml` exists but no topic references it | Add the slug to `topics:`, or delete the file |
| `slug is 'X' but the filename says 'Y'` | The `slug:` field and filename disagree | Make them match |
| `step N ('…') declares both resources and variants` | A step is trying to be universal and choice-based at once | Pick one — see the test above |
| `the last topic (X) must set is_capstone: true` | The final topic in `topics:` is not flagged | Add `is_capstone: true`, or reorder so the real capstone is last |
| `X.yaml is marked is_capstone but is not the final topic` | A non-final topic claims to be the capstone | Remove the flag, or move the topic to the end of `topics:` |
| `Duplicate uuid …` | Two entities share a UUID, usually from copy-pasting a step | Delete the UUID from the copy and run `make content` — a fresh one is generated |
| `<dir> has no _phase.yaml` | A phase directory is missing its metadata file | Create it |

## Rules that are easy to forget

- **Never edit `curriculum.json`.** It is generated, and the next build overwrites it.
- **Never hand-edit `schemas/*.json`.** They're generated from `content_model.py` (`make schemas`) — the model is the source of truth, not the file.
- **Never change or remove an existing `uuid`.** Learner progress points at it. Renaming, reordering, and rewriting are all safe; changing the UUID is not.
- **Quote labels containing `: `.** YAML reads a colon-space as a mapping. `label: "ClickHouse — LLM inference latency: TTFT…"` needs the quotes.
- **Update `order:` when inserting.** Nothing renumbers for you.
- **Bump `curriculum_version` in `curriculum.meta.yaml`** when publishing a meaningful content change.
