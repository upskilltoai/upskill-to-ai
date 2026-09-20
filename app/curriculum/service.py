"""Looks up phases and topics, by slug, from an already-loaded `Curriculum`.

Split from `loader.py` on purpose: loading happens once, at startup;
looking things up happens on every request that renders a page. Each
function takes the `Curriculum` instance as a plain argument rather than
importing a module-level global, so a test can hand it a small hand-built
`Curriculum` instead of depending on the real `content/curriculum.json`.

Add a new lookup here whenever a future page needs one — a step, being
part of a `Topic`'s own `steps` list, doesn't need its own lookup yet,
since nothing in the build plan renders a step on its own page.
"""

from __future__ import annotations

from content_model import CompiledPhase, Curriculum, Topic


def get_phase(curriculum: Curriculum, phase_slug: str) -> CompiledPhase | None:
    for phase in curriculum.phases:
        if phase.slug == phase_slug:
            return phase
    return None


def get_topic(curriculum: Curriculum, phase_slug: str, topic_slug: str) -> Topic | None:
    phase = get_phase(curriculum, phase_slug)
    if phase is None:
        return None
    for topic in phase.topics:
        if topic.slug == topic_slug:
            return topic
    return None
