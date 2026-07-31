---
name: cards
version: 1.1.0-codex
description: "Create Instagram, Threads, or X social media carousel cards from a URL, Markdown/text notes, or a short content brief. Use this skill whenever the user asks for IG cards, social cards, carousel images, carousel posts, content cards, or publish-ready PNG cards. The workflow plans the card story, edits bundled HTML templates, previews them, and exports 2x PNG images with Playwright."
user-invocable: true
last-updated: 2026-07-05
author: Codex conversion
tags:
  - social-media
  - instagram
  - carousel
  - design
  - image-generation
---

# Cards

Use this skill to turn a source idea, URL, article, Markdown note, or short brief into a polished set of social media image cards.

The bundled templates live in `assets/`:

- `assets/blue-dark/{cover,content-text,content-image,cta}.html`
- `assets/orange-light/{cover,content-text,content-image,cta}.html`

The exporter is `scripts/screenshot.mjs`. It screenshots every `.html` file in an output folder except `preview.html`, then removes the HTML files and leaves the final PNGs.

## Trigger Phrases

Use this skill when the user says things like:

- `$cards <URL or file path>`
- `Create IG carousel cards from this article`
- `Turn this Markdown note into social cards`
- `Make a 4:5 carousel post`
- `Create publish-ready PNG cards for Threads or X`

`$cards` is a user-facing shorthand, not a shell command. Treat it as "use the cards skill".

## Output Location

Create each card set under:

```text
output/YYYY-MM-DD-short-topic/
```

Inside the folder, create numbered HTML files while drafting:

```text
01-cover.html
02-content.html
03-content.html
04-cta.html
preview.html
```

After export, the folder should contain numbered PNGs:

```text
01-cover.png
02-content.png
03-content.png
04-cta.png
```

## Workflow

### 1. Understand the Source

If the user provides a URL, browse or fetch it when tools are available. If the user provides a file path, read the file. If the user provides only a short idea, ask at most one concise clarification only when the topic, audience, or desired angle is truly unclear.

Summarize the source into:

- Main promise
- Audience
- 3-5 key points
- Suggested CTA

### 2. Choose Style and Format

Default choices:

- Style: `blue-dark`
- Format: 4:5, `1080x1350`, best for Instagram carousel
- Handle: use `output/.handle` if present; otherwise ask only if the user clearly cares about attribution. If not, use `@yourhandle` as a neutral placeholder.

Offer alternatives only when useful:

- `blue-dark`: stronger contrast, tech/business/tutorial feel
- `orange-light`: lighter, warmer, clearer for simple educational posts
- 1:1: `1080x1080`, better for X/Threads cross-posting

### 3. Plan the Carousel

For most requests, produce 4 cards:

1. `cover`: strong headline plus subtitle
2. `content-text`: key points or steps
3. `content-text` or `content-image`: supporting details, example, chart, screenshot, or visual
4. `cta`: short closing and follow/action prompt

Use more cards only when the source genuinely needs it. Keep each card scannable.

Copywriting rules:

- Headline: ideally under 18 Chinese characters, or two short lines in English
- Subtitle: 1-2 short lines
- Bullet points: 3-4 bullets per card
- Body text: concise, practical, and natural
- Avoid dense paragraphs on cards

### 4. Create HTML Cards

Copy the relevant template files from `assets/{style}/` into the output folder and rename them with numeric prefixes.

Edit the HTML directly:

- Replace title, subtitle, bullet text, descriptions, CTA, and handle.
- Keep the `.card` root element; the screenshot script depends on it.
- For image cards, use a local image path and set images to fit cleanly. Prefer `object-fit: contain` for screenshots or charts and `object-fit: cover` for decorative visuals only when cropping is acceptable.
- For 1:1 cards, change `.card` height from `1350px` to `1080px` in every generated card.
- Do not leave placeholder text in final cards.

### 5. Build Preview

Create `preview.html` in the output folder with iframes for every generated card. This lets the user or Codex inspect spacing before export.

Preview rules:

- Show cards in order.
- Scale iframes visually, but do not change the card dimensions inside each card file.
- Check for clipped text, awkward wrapping, missing images, and low contrast.

### 6. Export PNG

From the skill directory, install dependencies if needed:

```powershell
npm install
npx playwright install chromium
```

Then export:

```powershell
node "C:\Users\user\.codex\skills\cards\scripts\screenshot.mjs" "C:\path\to\output\YYYY-MM-DD-short-topic"
```

The script captures each card at `deviceScaleFactor: 2`, so the PNGs are 2x resolution.

### 7. Final Response

Tell the user:

- Where the PNG files were saved
- Which style and size were used
- Any source limitation, if content was inferred rather than read directly

When useful, include local image previews in Markdown with absolute paths:

```markdown
![card preview](C:\absolute\path\01-cover.png)
```

## Quality Bar

Before finishing:

- Verify every intended PNG exists.
- Check that each PNG has nonzero file size.
- Confirm there is no leftover placeholder copy.
- Confirm the carousel has a clear beginning, middle, and CTA.
- Keep required license notes from original source materials when redistributing.
