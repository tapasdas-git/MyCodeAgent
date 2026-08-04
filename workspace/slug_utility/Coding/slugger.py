from __future__ import annotations


def slugify(text: str) -> str:
    slug_parts: list[str] = []

    for character in text:
        if character.isalnum():
            slug_parts.append(character.lower())
            continue

        if slug_parts and slug_parts[-1] != "-":
            slug_parts.append("-")

    return "".join(slug_parts).strip("-")
