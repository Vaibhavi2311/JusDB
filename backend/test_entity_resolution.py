
from backend.app.entity_resolution import (
    normalize_name,
    resolve_entity_name,
    create_entity_key
)


test_names = [
    "Google",
    "GOOGLE",
    "Google LLC",
    "Google Inc.",
    "Python programming language",
    "Microsoft Corporation"
]


for name in test_names:

    canonical = resolve_entity_name(
        name,
        "ORGANIZATION"
        if "google" in name.lower() or "microsoft" in name.lower()
        else "TECHNOLOGY"
    )

    print("Original:", name)
    print("Canonical:", canonical)
    print()


print(
    "Google key:",
    create_entity_key("Google LLC", "ORGANIZATION")
)

print(
    "Google alias key:",
    create_entity_key("GOOGLE", "ORGANIZATION")
)
