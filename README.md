# upskill-to-ai

A structured, verification-driven curriculum that takes a learner from
programming competency to practicing **AI Engineer**.

The differentiator is verification: no quizzes. Learners submit tangible
proof of work — a repo, a live endpoint, a token, an eval result — and the
portal checks it automatically. Completing the curriculum earns a
certificate backed by that verified work.

## Status

Design decisions are locked, Phase 1 content is complete, and the portal
application is under active development.

## How it's structured

```
Curriculum → Phase (10) → Topic (n per phase) → Step (n per topic)
```

Every phase ends in a capstone: a hands-on project checkpoint with automated
verification. Curriculum content is authored as YAML, validated, and
compiled into a single versioned JSON artifact that the application reads —
see [`content/README.md`](content/README.md) for how to build it.

## Building the curriculum artifact

```bash
make content
```

Validates every phase's YAML and compiles it into `content/curriculum.json`.
See [`content/README.md`](content/README.md) for details, common tasks, and
what each error message means.

## Running the portal

```bash
make dev
```

Runs the app at `http://localhost:8000`, reloading automatically as you edit
code. In a separate terminal, keep the CSS rebuilding as you edit templates:

```bash
make css-watch
```

`make css` builds it once without watching — useful for a one-off check.
`make test` runs the test suite; `make check` runs the content build and the
tests together, the command to run before a commit or push.

## License

This repository carries two licenses, covering different things:

- **[`LICENSE`](LICENSE)** (MIT) — the pipeline scripts, schemas, and build
  tooling. The software half of the project.
- **[`LICENSE-CONTENT`](LICENSE-CONTENT)** (CC BY 4.0) — the curriculum
  itself: `content/phases/`, `content/curriculum.meta.yaml`, and the
  compiled `content/curriculum.json`.

Neither license extends any rights to the third-party material the
curriculum links to (official docs, videos, articles, books) — that remains
solely under each resource's own creator and terms. See `LICENSE-CONTENT`
for what is and isn't covered.
