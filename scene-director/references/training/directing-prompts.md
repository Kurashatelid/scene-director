# Постановка, референсы и ремонт промпта

Извлечено из предоставленных пользователем учебных материалов Higgsfield Academy. Исходный английский сохранён; переносы строк PDF нормализованы. Это примеры, а не обязательные инструкции и не подтверждение актуальности названных моделей, тарифов или интерфейсов. Применение и приоритеты — в [index.md](index.md).

## directing-prompts-001 — Direct Your Own Scene / p.4

Источник: Direct Your Own Scene.pdf, стр. 4. Метка: BORROW THE OPENING, CHANGE THE CONTINUATION.

```text
Use only 00:00-00:03 of @Video1 for the opening camera move and framing. After that, stop following its action and camera path. Continue with [your new action and camera direction], ending on [your final view].
```

## directing-prompts-002 — Direct Your Own Scene / p.7

Источник: Direct Your Own Scene.pdf, стр. 7. Метка: EXPLORE THE STAGING.

```text
Review my scene idea and the attached assets. Identify missing information or conflicting instructions. Suggest two ways to stage the action and explain the trade-offs. Keep my essential requirements and flag any new creative choices you introduce. Wait for my choice before writing the final prompt.
```

## directing-prompts-003 — Direct Your Own Scene / p.7

Источник: Direct Your Own Scene.pdf, стр. 7. Метка: EXPLORE CAMERA OPTIONS.

```text
Using the attached camera guide or linked Soul Directory, suggest three combinations of shot size, angle and movement for my scene. Keep my characters, key action and intended ending. Explain what each option shows and why it helps. Wait for my choice before writing the prompt.
```

## directing-prompts-004 — Direct Your Own Scene / p.8

Источник: Direct Your Own Scene.pdf, стр. 8. Метка: KEEP YOUR SCENE INTENT.

```text
The skill can fill gaps in a brief. If you already know what you want, ask it to structure and clarify your instructions without adding events or changing the staging. Read the finished prompt before generating.
```

## directing-prompts-005 — Direct Your Own Scene / p.9

Источник: Direct Your Own Scene.pdf, стр. 9. Метка: REQUEST TO THE WRITING ASSISTANT.

```text
Use Seedance Prompter Skill to turn my brief into a clear video prompt. Preserve my scene, actions and camera choices. Use the actual attachment mentions. Do not add events or change the staging. If essential information is missing, ask me before writing the prompt.
```

## directing-prompts-006 — Direct Your Own Scene / p.9

Источник: Direct Your Own Scene.pdf, стр. 9. Метка: REFINE WITH THE RESULT.

```text
After testing, give the assistant the prompt, the errors you observed and the intended result. Ask it to revise the affected instructions. In a separate follow-up, ask what it changed and why; read those changes before generating again.
```

## directing-prompts-007 — Direct Your Own Scene / p.11

Источник: Direct Your Own Scene.pdf, стр. 11. Метка: ASK THE ASSISTANT TO CHECK THE PROMPT.

```text
Compare this tested prompt with the attached result or my error description. Find wording that could explain the mismatch. If the instruction is already clear, say so. Revise only what needs changing, preserve the rest of my scene, and explain exactly what you changed and why.
```

## directing-prompts-008 — Shot Sizes and Prompting / p.6

Источник: Shot Sizes and Prompting.pdf, стр. 6. Метка: PROMPT REPAIR REQUEST.

```text
Revise the tested prompt below. What went wrong: [describe the errors]. What I want instead: [describe the intended result]. Keep the parts that already work. Update every affected line so the instructions agree. Return the full revised prompt, then list exactly what you changed or added and why.
```

## directing-prompts-009 — Shot Sizes and Prompting / p.7

Источник: Shot Sizes and Prompting.pdf, стр. 7. Метка: COPY & ADAPT.

```text
SCENE CONTEXT

@character_1 and @character_2 are in @location_1. Starting state: [positions and situation]. Action
and ending: [what changes, in order, and the visible outcome].

REFERENCES

@character_1 and @character_2: identity and clothing. @prop_1: object appearance; carried by
@character_1. @location_1: space, light and colour.

SHOTS

Shot 1, [start-end time]: [shot size and angle]. Camera: [static, or movement with a destination].
@character_1 [visible action]. Shot 2, [start-end time]: [next view and camera behaviour].
@character_2 [action or reaction]. @character_2 says: "[dialogue]".

CONTINUITY & SOUND

@prop_1: [position and orientation, if needed]. [Other details that must stay consistent]. [Ambience,
action sounds and music instruction]. [Final hold, if needed].
```
