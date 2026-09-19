"""The single source of truth for the curriculum's content shape.

`content/schemas/*.json` are generated from these models (see
`scripts/generate_schemas.py`) instead of hand-written — without this, the
hand-written JSON Schema and the portal's own Python types would be two
definitions of the same data, free to drift apart the moment both exist.

Used two places:

* `scripts/compile_curriculum.py` — indirectly, via the generated schema
  files it already validates against.
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


class Phase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uuid: uuid.UUID
    slug: str = Field(pattern=r"^phase[0-9]+$")
    name: str = Field(min_length=1)
    short_description: str = Field(min_length=1)
    description: str = Field(min_length=1)
    order: int = Field(ge=1)
    topics: list[Slug] = Field(min_length=1)
    hands_on_verification: HandsOnVerification | None = None

    @model_validator(mode="after")
    def _topics_are_unique(self) -> Phase:
        # JSON Schema's `uniqueItems: true` on `topics` — nothing else in the
        # pipeline currently catches a slug accidentally listed twice.
        if len(self.topics) != len(set(self.topics)):
            raise ValueError("`topics` contains a duplicate slug")
        return self
