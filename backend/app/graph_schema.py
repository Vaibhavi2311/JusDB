
from enum import Enum
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    PROJECT = "PROJECT"
    TECHNOLOGY = "TECHNOLOGY"
    CONCEPT = "CONCEPT"
    LOCATION = "LOCATION"
    DOCUMENT = "DOCUMENT"
    DATE = "DATE"


class RelationType(str, Enum):
    WORKS_AT = "WORKS_AT"
    FOUNDED = "FOUNDED"
    USES = "USES"
    PART_OF = "PART_OF"
    LOCATED_IN = "LOCATED_IN"
    WORKS_ON = "WORKS_ON"
    RELATED_TO = "RELATED_TO"
    CREATED = "CREATED"
    OCCURRED_ON = "OCCURRED_ON"
    MENTIONS = "MENTIONS"


class Entity(BaseModel):
    name: str = Field(min_length=1)
    entity_type: EntityType
    description: str = ""
    source_chunk_id: str


class Relation(BaseModel):
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    relation_type: RelationType
    evidence_sentence: str = Field(min_length=1)
    evidence_chunk_id: str


class ExtractedGraph(BaseModel):
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
