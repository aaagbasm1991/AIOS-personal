# Social Cards Skill

Create publish-ready carousel images for Instagram, Threads, or X from a URL, Markdown note, or short content brief.

## What It Does

- Plans a short card story from source material.
- Uses bundled HTML templates for consistent layout.
- Supports 4:5 Instagram carousel format and optional 1:1 square format.
- Exports high-resolution PNG files with Playwright.

## Folder Structure

```text
cards/
├── SKILL.md
├── README.md
├── assets/
│   ├── blue-dark/
│   └── orange-light/
└── scripts/
    └── screenshot.mjs
```

## Templates

Each style includes four template types:

- `cover.html`
- `content-text.html`
- `content-image.html`
- `cta.html`

Available styles:

- `blue-dark`: strong contrast, suitable for tech, business, and tutorial content
- `orange-light`: warmer and clearer for lightweight educational content

## Usage Examples

```text
$cards https://example.com/article
```

```text
$cards C:\path\to\notes.md
```

```text
Create a 4-card Instagram carousel explaining this idea.
```

## Export

Install dependencies when needed:

```powershell
npm install
npx playwright install chromium
```

Export PNG files:

```powershell
node scripts/screenshot.mjs "C:\path\to\output\YYYY-MM-DD-short-topic"
```

The output folder should contain files like:

```text
01-cover.png
02-content.png
03-content.png
04-cta.png
```

## License

Use according to the license terms of the original source materials. Keep required license notes when redistributing.
