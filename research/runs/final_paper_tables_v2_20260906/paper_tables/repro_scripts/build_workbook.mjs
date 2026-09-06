import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(process.argv[2]);
const tablesDir = path.join(root, "paper_tables");
const csvDir = path.join(tablesDir, "csv");
const outputDir = path.join(tablesDir, "workbook");
const renderDir = path.join(outputDir, "rendered");
const outputPath = path.join(outputDir, "BiUMamba_Final_Paper_Tables_v2.xlsx");

function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (ch === '"') quoted = false;
      else cell += ch;
    } else {
      if (ch === '"') quoted = true;
      else if (ch === ',') { row.push(cell); cell = ""; }
      else if (ch === '\n') { row.push(cell.replace(/\r$/, "")); rows.push(row); row = []; cell = ""; }
      else cell += ch;
    }
  }
  if (cell.length || row.length) { row.push(cell.replace(/\r$/, "")); rows.push(row); }
  return rows.filter(r => !(r.length === 1 && r[0] === ""));
}

async function csvRows(file) {
  return parseCsv(await fs.readFile(file, "utf8"));
}

function colName(n) {
  let s = "";
  while (n > 0) { n--; s = String.fromCharCode(65 + (n % 26)) + s; n = Math.floor(n / 26); }
  return s;
}

const navy = "#17365D";
const blue = "#4472C4";
const lightBlue = "#D9EAF7";
const paleBlue = "#F4F8FC";
const lightGray = "#F2F2F2";
const line = "#D9E1F2";
const amber = "#FFF2CC";
const red = "#F4CCCC";
const green = "#E2F0D9";

function styleTitle(sheet, lastCol, title, subtitle) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${lastCol}1`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: navy,
    font: { bold: true, color: "#FFFFFF", size: 16 },
    verticalAlignment: "center",
    horizontalAlignment: "left",
  };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 32;
  sheet.getRange(`A2:${lastCol}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${lastCol}2`).format = {
    fill: lightBlue,
    font: { italic: true, color: navy, size: 10 },
    verticalAlignment: "center",
    wrapText: true,
  };
  sheet.getRange(`A2:${lastCol}2`).format.rowHeight = 30;
}

function styleHeader(range) {
  range.format = {
    fill: blue,
    font: { bold: true, color: "#FFFFFF", size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "inside", style: "thin", color: line },
  };
  range.format.rowHeight = 34;
}

function styleBody(range) {
  range.format = {
    verticalAlignment: "center",
    wrapText: true,
    borders: {
      insideHorizontal: { style: "thin", color: line },
      insideVertical: { style: "thin", color: line },
    },
  };
}

function setWidths(sheet, rows, maxWidth = 42) {
  if (!rows.length) return;
  for (let c = 0; c < rows[0].length; c++) {
    let width = Math.max(10, ...rows.slice(0, 60).map(r => String(r[c] ?? "").length + 2));
    width = Math.min(maxWidth, width);
    sheet.getRange(`${colName(c + 1)}:${colName(c + 1)}`).format.columnWidth = width;
  }
}

const wb = Workbook.create();
const overview = wb.worksheets.add("Overview");

const tableSpecs = [
  { sheet: "T1 Reproduced", file: "Table1a_Synapse_reproduced.csv", title: "Table 1a — Synapse reproduced results", note: "Mean ± sample SD across seeds 42, 3407, and 2026. Frozen 14/4/12 patient split and isolated test; nnU-Net uses its model-specific training protocol.", maxWidth: 38 },
  { sheet: "T1 Reported", file: "Table1b_Synapse_reported_baselines.csv", title: "Table 1b — Original-paper reported baselines", note: "Reported by the original papers; not reproduced under our setting. Do not describe these rows as a fully fair direct comparison.", maxWidth: 55 },
  { sheet: "T2 Scan", file: "Table2_scan_design_ablation.csv", title: "Table 2 — Scan-design ablation", note: "Full300 and Screen50 are separate protocols. All rows are exploratory single-seed results; Screen50 is not directly comparable with Full300.", maxWidth: 48 },
  { sheet: "T3 Fusion", file: "Table3_fusion_ablation.csv", title: "Table 3 — Fusion ablation", note: "Fixed sum is the final design. Adaptive-gate variants are negative/diagnostic results and are not final contributions.", maxWidth: 48 },
  { sheet: "T4 Cross Dataset", file: "Table4_cross_dataset_results.csv", title: "Table 4 — Cross-dataset results", note: "Accuracy uses three-seed patient-level means. Synapse and ACDC are comparable; BUSI shows a significant dataset-dependent limitation.", maxWidth: 50 },
  { sheet: "T5 Pretraining", file: "Table5_pretraining_ablation.csv", title: "Table 5 — Pre-training ablation", note: "The 25% formal block reports three-seed validation. The isolated-test block is seed42 exploratory and must not be presented as a three-seed conclusion.", maxWidth: 48 },
  { sheet: "T6 Efficiency", file: "Table6_efficiency.csv", title: "Table 6 — Unified efficiency", note: "Strict RTX 4090 inference: AMP off, 20 warm-ups, 200 timed iterations. E2_modify_2 lowers memory and estimated operations but has higher measured latency in all three settings.", maxWidth: 46 },
];

const sheetRanges = [];
for (let index = 0; index < tableSpecs.length; index++) {
  const spec = tableSpecs[index];
  const rows = await csvRows(path.join(csvDir, spec.file));
  const sheet = wb.worksheets.add(spec.sheet);
  const lastCol = colName(rows[0].length);
  const lastRow = 4 + rows.length;
  styleTitle(sheet, lastCol, spec.title, spec.note);
  sheet.getRange(`A4:${lastCol}${lastRow}`).values = rows;
  styleHeader(sheet.getRange(`A4:${lastCol}4`));
  if (rows.length > 1) {
    styleBody(sheet.getRange(`A5:${lastCol}${lastRow}`));
    for (let r = 5; r <= lastRow; r++) {
      if (r % 2 === 1) sheet.getRange(`A${r}:${lastCol}${r}`).format.fill = paleBlue;
    }
  }
  setWidths(sheet, rows, spec.maxWidth);
  sheet.freezePanes.freezeRows(4);
  const tableName = `PaperTable${index + 1}`;
  sheet.tables.add(`A4:${lastCol}${lastRow}`, true, tableName).style = "TableStyleMedium2";
  const all = sheet.getRange(`A4:${lastCol}${lastRow}`);
  all.conditionalFormats.add("containsText", { text: "Red", format: { fill: red, font: { color: "#9C0006", bold: true } } });
  all.conditionalFormats.add("containsText", { text: "Significant patient-level Dice decrease", format: { fill: red, font: { color: "#9C0006", bold: true } } });
  all.conditionalFormats.add("containsText", { text: "Final", format: { fill: green, font: { color: "#006100", bold: true } } });
  sheetRanges.push([spec.sheet, `A1:${lastCol}${Math.min(lastRow, spec.sheet === "T6 Efficiency" ? 10 : lastRow)}`]);
}

// Cell-level source map.
const sourceRows = await csvRows(path.join(tablesDir, "source_map", "table_cell_source_map.csv"));
const sourceSheet = wb.worksheets.add("Source Map");
const sourceLastCol = colName(sourceRows[0].length);
const sourceLastRow = 4 + sourceRows.length;
styleTitle(sourceSheet, sourceLastCol, "Cell-level table provenance", "Every reported numeric cell is linked to a frozen source CSV, selector, source column(s), transformation, and source SHA-256.");
sourceSheet.getRange(`A4:${sourceLastCol}${sourceLastRow}`).values = sourceRows;
styleHeader(sourceSheet.getRange(`A4:${sourceLastCol}4`));
styleBody(sourceSheet.getRange(`A5:${sourceLastCol}${sourceLastRow}`));
sourceSheet.tables.add(`A4:${sourceLastCol}${sourceLastRow}`, true, "SourceMapTable").style = "TableStyleMedium2";
setWidths(sourceSheet, sourceRows, 52);
sourceSheet.getRange("G:G").format.columnWidth = 38;
sourceSheet.getRange("J:J").format.columnWidth = 24;
sourceSheet.freezePanes.freezeRows(4);
sheetRanges.push(["Source Map", `A1:${sourceLastCol}35`]);

// Audit summary.
const auditJson = JSON.parse(await fs.readFile(path.join(tablesDir, "audits", "TABLE_CROSSCHECK_REPORT.json"), "utf8"));
const auditSheet = wb.worksheets.add("Audit");
styleTitle(auditSheet, "F", "Table 1–6 cross-check", "Independent verification re-opened the source CSVs, verified hashes, re-applied transformations, and checked target-table cells.");
auditSheet.getRange("A4:B9").values = [
  ["Check", "Result"],
  ["Overall status", auditJson.overall_status],
  ["Mapped numeric cells", auditJson.mapped_numeric_cells],
  ["Passed", auditJson.passed],
  ["Failed", auditJson.failed],
  ["Latest Step 20 / 20.5 merged", auditJson.step20_present && auditJson.step20_5_present ? "Yes" : "No"],
];
styleHeader(auditSheet.getRange("A4:B4"));
styleBody(auditSheet.getRange("A5:B9"));
auditSheet.getRange("B5:B9").format.horizontalAlignment = "center";
auditSheet.getRange("B5").conditionalFormats.add("containsText", { text: "PASS", format: { fill: green, font: { color: "#006100", bold: true } } });
const coverage = Object.entries(auditJson.tables).map(([name, c]) => [name, c.PASS ?? 0, c.FAIL ?? 0]);
auditSheet.getRange(`A12:C${12 + coverage.length}`).values = [["Table", "Cells passed", "Cells failed"], ...coverage];
styleHeader(auditSheet.getRange("A12:C12"));
styleBody(auditSheet.getRange(`A13:C${12 + coverage.length}`));
auditSheet.getRange("A22:F25").merge();
auditSheet.getRange("A22").values = [["Interpretation guardrails: Table 1 and Table 4 use different declared aggregation levels; original-paper baselines remain separate; Screen50 is not directly compared with Full300; FractalDB isolated-test rows are seed42 exploratory; whole-model FLOPs are estimated, not exact."]];
auditSheet.getRange("A22:F25").format = { fill: amber, wrapText: true, verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: "#BF9000" } };
auditSheet.getRange("A:A").format.columnWidth = 32;
auditSheet.getRange("B:C").format.columnWidth = 18;
auditSheet.getRange("D:F").format.columnWidth = 18;
auditSheet.freezePanes.freezeRows(4);
sheetRanges.push(["Audit", "A1:F25"]);

// Overview, added last but used as the workbook landing sheet.
styleTitle(overview, "H", "BiUMamba — final manuscript Tables 1–6", "Generated from paper_final_results_v2_verified. Use the CSV sheets as the paper source of truth; use Source Map and Audit for traceability.");
overview.getRange("A4:B11").values = [
  ["Release field", "Value"],
  ["Table panels", tableSpecs.length],
  ["Primary table numbers", 6],
  ["Cross-check status", auditJson.overall_status],
  ["Cross-check failures", auditJson.failed],
  ["Mapped numeric cells", null],
  ["Step 20 merged", auditJson.step20_present ? "Yes" : "No"],
  ["Step 20.5 merged", auditJson.step20_5_present ? "Yes" : "No"],
];
overview.getRange("B9").formulas = [["='Audit'!B6"]];
styleHeader(overview.getRange("A4:B4"));
styleBody(overview.getRange("A5:B11"));
overview.getRange("B7:B11").format.horizontalAlignment = "center";
overview.getRange("B7").conditionalFormats.add("containsText", { text: "PASS", format: { fill: green, font: { color: "#006100", bold: true } } });
overview.getRange("A14:H14").merge();
overview.getRange("A14").values = [["Publication-safe reading rules"]];
overview.getRange("A14:H14").format = { fill: blue, font: { bold: true, color: "#FFFFFF" }, verticalAlignment: "center" };
overview.getRange("A15:H22").merge();
overview.getRange("A15").values = [[
  "• Table 1a: reproduced Synapse macro-organ results; Table 1b: original-paper values only.\n" +
  "• Table 4: patient-level three-seed means used for paired statistical interpretation.\n" +
  "• BUSI shows a significant decrease in Dice/NSD and increase in HD95; keep it as a limitation.\n" +
  "• E2_modify_2 lowers peak memory and estimated FLOPs, but strict measured latency is higher on Synapse, ACDC, and BUSI.\n" +
  "• The 25% FractalDB formal validation result is Red. The 50% and 100% isolated-test results are seed42 exploratory."
]];
overview.getRange("A15:H22").format = { fill: amber, wrapText: true, verticalAlignment: "top", borders: { preset: "outside", style: "thin", color: "#BF9000" } };
overview.getRange("A:A").format.columnWidth = 30;
overview.getRange("B:B").format.columnWidth = 24;
overview.getRange("C:H").format.columnWidth = 16;
overview.freezePanes.freezeRows(2);
sheetRanges.push(["Overview", "A1:H22"]);

await fs.mkdir(renderDir, { recursive: true });

// Compact machine-readable inspection before export.
console.log((await wb.inspect({ kind: "table", range: "Overview!A1:H22", include: "values,formulas", tableMaxRows: 25, tableMaxCols: 10 })).ndjson);
console.log((await wb.inspect({ kind: "table", range: "T1 Reproduced!A1:M7", include: "values,formulas", tableMaxRows: 10, tableMaxCols: 15 })).ndjson);
console.log((await wb.inspect({ kind: "table", range: "T6 Efficiency!A1:T10", include: "values,formulas", tableMaxRows: 12, tableMaxCols: 22 })).ndjson);
console.log((await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 500 }, summary: "final formula error scan" })).ndjson);

for (const [sheetName, range] of sheetRanges) {
  const preview = await wb.render({ sheetName, range, scale: sheetName === "Source Map" ? 0.65 : 0.9, format: "png" });
  const safeName = sheetName.replaceAll(" ", "_");
  await fs.writeFile(path.join(renderDir, `${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(wb);
await fs.mkdir(outputDir, { recursive: true });
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, renderedSheets: sheetRanges.map(x => x[0]) }));
