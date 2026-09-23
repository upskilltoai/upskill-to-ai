"""The single source of truth for the curriculum's content shape.

`content/schemas/*.json` are generated from these models (see
`scripts/generate_schemas.py`) instead of hand-written — without this, the
hand-written JSON Schema and the portal's own Python types would be two
definitions of the same data, free to drift apart the moment both exist.

Used three places:

* `scripts/compile_curriculum.py` — directly, to validate each authored
  YAML document.
* `scripts/generate_schemas.py` — directly, to produce
  `content/schemas/*.json` purely for editor autocomplete; the compiler
  itself doesn't read those files.
* The portal (`app/curriculum/`, from Stage B onward) — directly, to parse
  `curriculum.json` into typed objects instead of raw dicts.

Field-by-field, these mirror `content/schemas/phase.schema.json` and
`topic.schema.json` exactly — this file replaces how those are authored, not
what they mean. Where a JSON Schema constraint has no direct Pydantic
equivalent (unique list items, the `variants` ↔ `variant_dimension`
pairing), a `model_validator` reproduces it, so nothing already guaranteed
is silently lost in the move.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"
Slug = Annotated[str, Field(pattern=_SLUG)]


class Objective(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uuid: uuid.UUID
    order: int = Field(ge=1)
    text: str = Field(min_length=1)


class Resource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, min_length=1)
    url: str = Field(pattern=r"^https://")
    note: str | None = None


class Variant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: Slug
    label: str = Field(min_length=1)
    # Required, not optional: a variant tab shows only this text and its
    # links, so without it the tab can't explain what makes this provider's
    # take different from the one in the next tab.
    description: str = Field(min_length=1)
    resources: list[Resource] = Field(min_length=1)


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uuid: uuid.UUID
    order: int = Field(ge=1)
    action: Literal["watch", "read", "practice", "explore"]
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    duration_minutes: int | None = Field(default=None, ge=1)
    optional: bool = False
    resources: list[Resource] | None = Field(default=None, min_length=1)
    variant_dimension: Literal["provider", "coding_tool"] | None = None
    variants: list[Variant] | None = Field(default=None, min_length=2)

    @model_validator(mode="after")
    def _variants_and_dimension_travel_together(self) -> Step:
        # JSON Schema's `dependentRequired` said the same thing: each of
        # `variants`/`variant_dimension` requires the other. (Whether a step
        # mixes `resources` *and* `variants` is checked separately, in the
        # compiler — deliberately, so the error names the offending step.)
        has_variants = self.variants is not None
        has_dimension = self.variant_dimension is not None
        if has_variants != has_dimension:
            raise ValueError(
                "`variants` and `variant_dimension` must both be set, or neither"
            )
        return self


class Topic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uuid: uuid.UUID
    slug: Slug
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    estimated_minutes: int = Field(ge=1)
    is_capstone: bool = False
    objectives: list[Objective] = Field(min_length=1)
    steps: list[Step] = Field(min_length=1)


class HandsOnVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirements: list[Slug] | None = None


class _PhaseFields(BaseModel):
    """Fields identical between the authored and compiled phase shapes.

    Not used directly — `Phase` and `CompiledPhase` below extend this and
    each add the one field where they genuinely differ. See `Curriculum`
    for why two phase shapes exist at all.
    """

    model_config = ConfigDict(extra="forbid")

    uuid: uuid.UUID
    slug: str = Field(pattern=r"^phase[0-9]+$")
    name: str = Field(min_length=1)
    short_description: str = Field(min_length=1)
    description: str = Field(min_length=1)
    order: int = Field(ge=1)
    hands_on_verification: HandsOnVerification | None = None


class Phase(_PhaseFields):
    """The *authored* shape — `content/phases/phaseN/_phase.yaml`, exactly
    what a human writes. `topics` is a plain list of slugs; the compiler
    replaces this with full `Topic` objects when building the artifact
    (see `CompiledPhase`), and adds `estimated_minutes` (summed from
    those topics) — neither of which a phase file ever contains itself.
    """

    topics: list[Slug] = Field(min_length=1)

    @model_validator(mode="after")
    def _topics_are_unique(self) -> Phase:
        # JSON Schema's `uniqueItems: true` on `topics` — nothing else in the
        # pipeline currently catches a slug accidentally listed twice.
        if len(self.topics) != len(set(self.topics)):
            raise ValueError("`topics` contains a duplicate slug")
        return self


class CompiledPhase(_PhaseFields):
    """The shape inside `curriculum.json`, after compilation — `topics` is
    full `Topic` objects (not slugs), and `estimated_minutes` exists (it
    doesn't in `Phase`, since the compiler computes it, an author never
    writes it).
    """

    topics: list[Topic] = Field(min_length=1)
    estimated_minutes: int = Field(ge=1)


class Curriculum(BaseModel):
    """The compiled artifact's own shape — `content/curriculum.json` as a
    whole, not one phase or topic within it. Nothing has formally described
    this before now: `phase.schema.json`/`topic.schema.json` only ever
    covered one authored document at a time, never the merged result. Used
    by the compiler to sanity-check its own output before writing the file,
    and by the portal to load and validate that same file at startup.
    """

    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    generated_at: str
    phases: list[CompiledPhase] = Field(min_length=1)
