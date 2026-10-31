---
name: ugc-video-creator
description: Create authentic handheld creator-led UGC product videos in SuperComputer from separate character, product and location references. Use for spoken product reviews, try-ons, unboxings and UGC ads, or revisions to their prompts. Develop the prompt internally and generate the video when requested; return only a prompt when that is the requested deliverable.
---

# UGC Video Creator

Turn separate character, product and location references and a short idea into an authentic creator-led phone video. The look is believable, expressive and lively, with motivated handheld movement. Preserve the user's product, identity, intent and requested delivery.

Read the supplied references. Character means identity and outfit; location establishes space, light and photographic character; product establishes the actual object. Describe what is visible, not a generic substitute.

## SuperComputer workflow

1. Use the references already present in this chat. Confirm their roles from actual files or available asset handles. Ask only for a genuinely missing essential input.
2. Pass character, location and product as SEPARATE references to the video model. Do not first composite the person into the location or use a pre-composited character-in-location still as the required starting frame. Do not require a generated storyboard. Use a model/route that accepts the needed separate references; if unavailable, explain the limitation instead of silently baking them together.
3. Develop the detailed prompt internally using the structure below. Show a short proposed action and the exact spoken line so the user can judge the creative idea. Keep user-facing requests and explanations short. Default to English speech and copy unless the user requests another language.
4. For a requested video, use the available video tools and their actual model capabilities. Respect the user's chosen model, duration, aspect and reference roles. Show the real generation approval, then generate after the required approval. Do not change permanent approval settings. If the request is prompt-only, return one copyable prompt and do not generate.
5. Open and assess the returned video before selecting it: does the person belong in the scene, does the action read, are the product and speech clear? A completed job is not creative approval. Change only the actual issue and keep the original for comparison.

## Prompt-only output

When the user asks only for a prompt, deliver ONE complete prompt in a code block with at most one short introduction. Add a practical limitation only when it materially affects execution. For a video request, do not stop after writing the prompt.

## Prompt skeleton — 5 blocks, in this order

1. **Technical + world rules** — camera style, aspect, camera-invisibility rule, location description with lighting.
2. **Character block** — appearance locked to the reference image + blinking clause + product named.
3. **Timestamped beats** — `HOOK (0–2s):` then `(2–4s):` etc. Each beat = camera behavior + physical action + spoken line.
4. *(optional)* CTA beat as the final timestamp.
5. **Style footer** — speech energy, emotional arc, lighting summary, skin clauses, phone-quality clauses.

Timestamps are pacing targets, not exact guarantees from a generative model. Default total = 15s, subject to the selected tool's supported duration. If the user gives a duration (e.g. "overall 9 seconds"), re-budget every beat — don't just trim the last one; compress speech first, cut a beat second.

## Non-negotiable realism clauses

Use these scene-appropriate controls when relevant; they guide generation and do not guarantee a result:

**Camera invisibility** — generators love putting a phone in the subject's hand:
> The recording phone IS the camera and stays outside its own frame. In selfie mode one of her hands holds it out of frame; her other hand handles the product. Do not add a second visible recording phone or camera.

**Natural blinking** — avoid a held, artificial stare:
> She blinks naturally and regularly throughout, soft micro-expressions — never a fixed unblinking stare.
Optionally seed one specific blink into a beat ("one relaxed blink", "blinking rapidly for a beat in surprise").

**Real skin** — match the scene without artificial smoothing or exaggerated texture:
> Natural unretouched skin, subtle real texture and small facial asymmetries. Match the location lighting. Avoid waxy smoothing, forced pore detail, exaggerated redness and cosmetic highlight blooms; allow physically plausible sunlight and highlights.

**Phone quality** — match the requested capture style:
> A believable phone image with restrained natural sensor texture, responsive framing and no beauty filter. Keep the chosen scene's colour and contrast. Do not add heavy noise, compression or constant focus hunting as an effect.
(Night variant: add "night grain, slight noise in shadows".)

Keep constraints specific to the shot. Capitalisation and repeated negatives do not establish a quality guarantee; judge the returned image and movement.

## Camera logic

Choose one physical camera setup and assign the hands correctly:
- Selfie: one hand holds the off-frame recording phone, leaving one for the product.
- Friend filming: the friend operates the off-frame handheld camera; the creator has both hands available. Small following movements and reframes are motivated by the action.
- Propped phone: the camera stays still; both creator hands are free. A placement or pickup is an explicit action, not an invisible camera switch.

Every reposition needs a physical cause. Possible actions, not a mandatory sequence:

- **Handheld → static:** "props the phone on [ledge/sink/table/ground], frame bumps and wobbles as she lets go, autofocus hunts for a beat, then locks static."
- **Ground POV pickup:** camera flat on floor, lens up → face leans into view from above → hand grabs it → "frame swings wildly, motion blur, flashes of floor/clothes/window" → settles into selfie framing.
- **Inside-bag POV:** dark muffled frame, light through zipper gap, zipper sound, light floods in, she looks down into the lens.
- **Low static:** propped on a curb/bag/books for the whole video; subject moves relative to it (steps back for outfit check, crouches close for macro).
- **Ending:** subject reaches toward the lens — "frame goes shaky for a split second before cutting."

Use restrained imperfections when the camera or person actually moves. A handheld operator can follow or pan naturally; do not describe an invisible dolly or crane in a self-filmed take. Prefer one clear hook, one product action and a readable ending over a continuous stack of shakes, focus hunts and cuts.

## Hook library (0–2s)

The hook is a visual event plus an emotional spike, not a greeting. Possible patterns; choose one that fits the person, product and tone:

| Hook | Key wording |
|---|---|
| Scream reveal | screams — "OH MY GOD, THEY CAME!!" — camera shaking hard from her hands |
| Jump into frame | suddenly jumps into frame from the side, landing close to the lens |
| Product reveal | brings the product briefly close to the lens, then lowers it so we see the creator's reaction |
| Enter close to camera | steps into a close phone frame already doing something with the product; a clear visible action, not a greeting |
| Bag POV | camera inside her bag; she unzips it and looks down into the lens |
| Giant PR box | drags a box as big as her torso across the floor, visibly straining, shocked at the size |
| Hand over mouth | eyes wide in shock, claps hand over mouth, breaks into a giggle |
| Walking remark | already wearing the product, walking and talking into the handheld lens about its visible look |

Use throws, drops or durability demonstrations only when specifically requested and the intended claim is supported. Do not turn a visual stunt into a product-performance claim. Screaming, mock shock and oversized props are optional character choices, never the default definition of lively UGC.

## Speech rules

- 15s of video fits roughly 4–6 SHORT lines. When a user says "too much speech," cut adjectives and whole sentences, not just words — the visuals already sell chrome/charms/color.
- Casual spoken register with real pauses: "Okay wait—", "Come ON.", "Stop it.", "I'm obsessed."
- CAPS on the single stressed word per line: "they MATCH my skirt", "made for the CLUB".
- Describe delivery next to the line: gasps dramatically, short laugh shaking her head, mock-shocked, giddy.
- Feature language must come from the actual product reference. Do not add chrome, rimless construction, charms or any other feature that is absent. Do not invent personal-use history, protection ratings, durability, comfort, popularity or other unsupported claims.
- Add a CTA only when the user supplies the destination and relevant facts. Do not invent a link in bio, available colours or stock scarcity. A brief confident finish can replace a CTA.

## Emotional arcs

Name the arc in the footer so the generator plays a progression, not one frozen expression: shock → laughter → joy (durability), excitement → obsession (unboxing), calm confidence → sly reveal (daily-wear + "I bought more"), mock-shock → selling energy (CTA). Pair every emotion with a body action: jumping and clapping, hand on chest, happy shimmy, finger-guns, hip pop, playful spin, outfit check (gesture head-to-toe + little turn).

## Lighting presets

Read the actual location reference and the user's request. Use its light direction, shadow hardness, contrast and colour as visual guidance for the person and product. Preserve the selected look rather than importing studio light from a character sheet. The following are optional lighting descriptions, not defaults or required effects:

**Sunny day:** golden sunlight pouring between buildings / through the window, sunbeams on the floor or asphalt, crisp long shadows, dust motes drifting, soft sun flare kissing the edge of the lens, warm rim light glowing through her hair, flyaways catching the sun, chrome flaring bright in the sun. Footer: "strong sunny daylight contrast."
**Night club:** deep red light washing over everything, red reflections on hair and sliding across chrome, red highlights on the face. Footer: "night contrast, night grain, slight noise in shadows."
Skin, clothes and product must respond to the same scene light. Keep natural skin detail and plausible highlights; do not add separate beauty lighting or force a matte mask over real sunlight.

## Asset reference mode (@handles)

When the user shares a screenshot of named assets (@girl-1, @glasses-black, @location-4, @ljhf6...):

- Replace the character paragraph with `Character: @name.` — keep the blinking clause and lighting-on-hair lines.
- Replace the location description with `Location: @name` + the lighting cues actually visible in that reference. Do not claim that an image reference carries no lighting information.
- Replace product descriptions with `Prop: @name` and use the @handle at every action mention ("She puts on @glasses-blue", "holds @glasses-orange up to the lens").
- Keep beats, speech, and footer untouched. Copy handle spelling exactly, including odd ones (@ljhf6).
- Use only verified handles/files available in the chat. If a needed reference is missing, ask for it or use an accurate description; never invent an asset handle. Pass the actual separate image references to the model as well as naming their roles in the prompt.

## Iteration requests — change only what's named

The workflow is rapid remixing. When the user says:
- **"change the girl/boy"** → rewrite ONLY the character block from the new image (hair, eyes, marks, outfit); re-check outfit-referencing speech lines still make sense ("matches my skirt" → "goes with everything").
- **"rewrite location"** → new scene + prop surfaces only (ledge → sink → step); actions and speech stay.
- **new product color** → swap color words + the one matching-line ("literally Tiffany blue" → "all black, glossy finish").
- **"shorter" / "N seconds"** → re-budget all timestamps, compress speech first.
- **a physical correction ("he puts it on the ground", "no other phone")** → fix exactly that beat, keep the rest verbatim, apply the correction to the current prompt without rewriting unrelated behaviour or global rules.

Deliver the full rewritten prompt every time — never a diff or "change line 3."

## Troubleshooting (symptom → clause to add)

| Generation problem | Fix |
|---|---|
| Second phone appears in subject's hand | Camera-invisibility rule at the TOP, repeated in the hook beat ("holding only the sunglasses") |
| Dead unblinking stare | Blinking clause in character block + one explicit blink inside a beat |
| Plastic or detached-looking person | Check scene lighting, shadows, perspective and texture against the separate location and character references; avoid studio relighting or exaggerated pores |
| Wrong capture style | Re-establish selfie, friend-filmed handheld or propped-phone setup; preserve intentional colour and contrast |
| Beats rushed or mushed | Fewer beats, wider timestamp windows; drop one try-on |
| Product handling looks wrong | Simplify the action and verify available hands; do not substitute an unsupported durability stunt |
| Profile turns fail at arm's length | Offer friend-filming variant or prop-static framing |
