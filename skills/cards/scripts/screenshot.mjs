import { chromium } from 'playwright';
import { readdirSync, unlinkSync } from 'fs';
import { resolve } from 'path';

const dir = process.argv[2];

if (!dir) {
  console.error('Usage: node screenshot.mjs <folder>');
  process.exit(1);
}

const files = readdirSync(dir)
  .filter((file) => file.endsWith('.html') && file !== 'preview.html')
  .sort();

console.log(`Found ${files.length} HTML files in ${dir}`);

const browser = await chromium.launch();
const context = await browser.newContext({ deviceScaleFactor: 2 });

for (const file of files) {
  const page = await context.newPage();
  await page.goto('file://' + resolve(dir, file));
  await page.waitForTimeout(2500);

  const card = await page.$('.card');
  if (!card) {
    await page.close();
    throw new Error(`Missing .card element in ${file}`);
  }

  const pngName = file.replace('.html', '.png');
  await card.screenshot({ path: resolve(dir, pngName) });
  await page.close();
  console.log(`Saved ${pngName}`);
}

await browser.close();

for (const file of [...files, 'preview.html']) {
  try {
    unlinkSync(resolve(dir, file));
  } catch {}
}

console.log(`Done. Exported ${files.length} PNG files to ${dir}`);
