
import json
import re
from pathlib import Path


ALIAS_FILE = Path(__file__).with_name("entity_aliases.json")


def normalize_name(name: str) -> str:
    """
    Standardize spacing, case and punctuation.
    """
    name = name.strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^\w\s]", "", name)
    return name


def load_aliases():
    """
    Load manually approved entity aliases.
    """
    if not ALIAS_FILE.exists():
        return {}

    with open(ALIAS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def resolve_entity_name(name: str, entity_type: str) -> str:
    """
    Return the canonical name for an entity.

    Entity type is included so different types are
    not accidentally merged.
    """
    aliases = load_aliases()
    normalized_name = normalize_name(name)

    for canonical_name, alias_list in aliases.items():

        all_names = [canonical_name] + alias_list

        for alias in all_names:
            if normalize_name(alias) == normalized_name:
                return canonical_name

    return name.strip()


def create_entity_key(name: str, entity_type: str) -> str:
    """
    Create a stable key for the canonical entity.
    """
    canonical_name = resolve_entity_name(name, entity_type)

    return (
        entity_type.upper()
        + ":"
        + normalize_name(canonical_name)
    )
