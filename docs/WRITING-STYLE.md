# Writing Style

People read this library, and AI tools use it as context. Both kinds of reader need the same thing: facts that are exact and consistent. These rules come from [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/). We use only the rules that make meaning clearer. We do not use its limits on sentence length or vocabulary.

## 1. One term, one meaning

Use one term for each thing, and use it every time. A reader who sees a new word assumes that it is a new thing. Do not use one word for two things, either.

| Use | Not |
|---|---|
| shape key | morph, blend shape (except when you give another tool's name for it) |
| connect point | attach point, snap point, socket |
| block | node, record, object (when you mean a NIF block) |
| plugin | mod file, ESP (when you mean all plugin types) |

Add terms to this table when you find a conflict.

## 2. Say who acts

Name the actor: the engine, the Creation Kit, PyNifly, xEdit, or the modder. It matters whether something happens at runtime, at build time, or by hand.

> **No:** The prefix is replaced at runtime.
>
> **Yes:** The engine replaces the prefix at runtime.

## 3. Name the subject

Use the noun instead of "it" or "this" when the meaning could be unclear. Start each section by naming what it is about. A reader or a search tool often sees one section without the rest of the page.

> **No:** This lists the points other NIFs can attach to.
>
> **Yes:** `BSConnectPoint::Parents` lists the points other NIFs can attach to.

## 4. Separate facts from guesses

State known facts plainly ("The engine ignores this field"), and don't hedge them with "should" or "would". Put any doubt in a sentence of its own ("Not tested on LE"). When two sources disagree, say so; don't pick one without saying so.

## 5. Define terms at first use

Spell out abbreviations the first time they appear on each page: "an OMOD (Object Modification) record". You don't need to define NIF, BSA, ESP, or the game names.

## 6. Steps

- Use a numbered list. Start each step with a verb.
- Put one action in each step. A menu path (Block → Insert → `NiNode`) counts as one action.
- Put the condition first: "If the mod is skinned, set Skinned to true."

## 7. Troubleshooting

Make the heading the symptom, the way the reader sees it. Then list the causes, with the fix for each one if we know it.

```markdown
### The mod does not attach in the game

- The names do not match. ...
```
