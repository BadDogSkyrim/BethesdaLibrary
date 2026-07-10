# Documentation Conventions

Style rules for writing in this library. Keep entries here short and worked-example.

## Game-specific tags

When a fact applies to **only one game** (or only one edition of Skyrim), prefix the sentence or list item with a code-span tag. The code formatting renders with a subtle background tint on both GitHub and MkDocs Material, so the tag stands out without extra theming.

If a fact applies to both Fallout 4 and Skyrim, **don't tag it** — that's the default audience for this library.

### Tag set

| Tag | Meaning |
|---|---|
| `` `[FO4]` `` | Fallout 4 only |
| `` `[Skyrim]` `` | Skyrim, both LE and SE |
| `` `[SSE]` `` | Skyrim Special Edition only |
| `` `[LE]` `` | Skyrim Legendary Edition only |

Combine tags when a fact applies to a specific subset, e.g. `` `[SSE]` `[FO4]` `` for things shared by 64-bit-pointer Havok files. List the tags in alphabetical order so they're greppable.

### Where to put the tag

- **Inline at the start of a sentence or list item:**
  - `[FO4]` The face skeleton is a separate file (`facebones.hkx`) merged at runtime.
  - `[SSE]` Uses 64-bit pointers; LE files are not loadable.
- **Not at the end** of a sentence — that hides the scope behind the rest of the line.
- **Not on section headings** — if an entire `##` section is game-specific, name it accordingly (`## Fallout 4 Differences`) rather than tagging the heading.

### When *not* to tag

- Cross-game facts (NIF chunk layout, generic Havok concepts, glTF basics, etc.).
- Facts already living under a clearly-scoped section like `## Fallout 4 Differences` or `## Skyrim-only Bones` — the section header carries the scope.
- Tool docs where the tool itself is single-game (the tool's overview already establishes the scope).

## Other conventions

(Additions go here as they come up — naming, code-block languages, link style, etc.)
