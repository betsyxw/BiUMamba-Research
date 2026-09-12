import fs from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";

const dir = "outputs/BiUMamba_Paper_Evidence_Freeze_20260912_v1/paper_tables/workbook_previews";
const files = (await fs.readdir(dir)).filter(x => x.endsWith(".png")).sort();
const tileW = 440, tileH = 320, cols = 3, rows = Math.ceil(files.length / cols);
const composites = [];
for (let i = 0; i < files.length; i++) {
  const input = path.join(dir, files[i]);
  const thumb = await sharp(input).resize({ width: tileW - 20, height: tileH - 48, fit: "inside", withoutEnlargement: true }).png().toBuffer();
  const meta = await sharp(thumb).metadata();
  const x = (i % cols) * tileW + 10 + Math.floor((tileW - 20 - meta.width) / 2);
  const y = Math.floor(i / cols) * tileH + 38 + Math.floor((tileH - 48 - meta.height) / 2);
  composites.push({ input: thumb, left: x, top: y });
  const label = Buffer.from(`<svg width="${tileW}" height="38"><rect width="100%" height="100%" fill="#16324F"/><text x="12" y="25" font-family="Arial" font-size="17" font-weight="700" fill="white">${files[i].replaceAll("_", " ").replace(".png", "")}</text></svg>`);
  composites.push({ input: label, left: (i % cols) * tileW, top: Math.floor(i / cols) * tileH });
}
const out = "outputs/BiUMamba_Paper_Evidence_Freeze_20260912_v1/audit/WORKBOOK_ALL_SHEETS_CONTACT_SHEET.png";
await sharp({ create: { width: cols * tileW, height: rows * tileH, channels: 3, background: "#E9EEF5" } }).composite(composites).png().toFile(out);
console.log(out);
