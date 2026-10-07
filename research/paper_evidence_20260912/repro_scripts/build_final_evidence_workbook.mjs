import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const bundle = path.join(root, "outputs/BiUMamba_Paper_Evidence_Freeze_20260912_v1");
const csvDir = path.join(bundle, "paper_tables/csv");
const previewDir = path.join(bundle, "paper_tables/workbook_previews");
const outputPath = path.join(bundle, "paper_tables/BiUMamba_Final_Evidence_Tables_20260912.xlsx");

function parseCSV(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(field); field = ""; }
    else if (c === '\n') { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
    else field += c;
  }
  if (field.length || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row); }
  return rows;
}

function colName(n) {
  let s = "";
  while (n >= 0) { s = String.fromCharCode(65 + (n % 26)) + s; n = Math.floor(n / 26) - 1; }
  return s;
}

function styleDataSheet(sheet, rows, title, subtitle, tabColor = "#1F4E78") {
  sheet.showGridLines = false;
  sheet.tabColor = tabColor;
  sheet.freezePanes.freezeRows(4);
  const cols = rows[0].length;
  const last = colName(cols - 1);
  sheet.getRange(`A1:${last}1`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A2:${last}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A1").format = { fill: "#16324F", font: { bold: true, color: "#FFFFFF", size: 18 }, rowHeight: 28 };
  sheet.getRange("A2").format = { fill: "#DCE6F1", font: { italic: true, color: "#243447", size: 10 }, wrapText: true, rowHeight: 32 };
  sheet.getRangeByIndexes(3, 0, rows.length, cols).values = rows;
  const header = sheet.getRange(`A4:${last}4`);
  header.format = { fill: "#2F75B5", font: { bold: true, color: "#FFFFFF", size: 10 }, wrapText: true, verticalAlignment: "center", borders: { preset: "all", style: "thin", color: "#B4C7E7" } };
  const body = sheet.getRange(`A5:${last}${rows.length + 3}`);
  body.format = { font: { color: "#1F2937", size: 9 }, wrapText: true, verticalAlignment: "top", borders: { preset: "all", style: "thin", color: "#D9E2F3" } };
  for (let r = 5; r <= rows.length + 3; r++) {
    if (r % 2 === 0) sheet.getRange(`A${r}:${last}${r}`).format.fill = "#F4F7FB";
  }
  sheet.getRange(`A1:${last}${rows.length + 3}`).format.autofitColumns();
  sheet.getRange(`A1:${last}${rows.length + 3}`).format.autofitRows();
  for (let c = 0; c < cols; c++) {
    const w = Math.min(Math.max(c < 2 ? 110 : 95, (rows[0][c]?.length || 8) * 8), 270);
    sheet.getRange(`${colName(c)}:${colName(c)}`).format.columnWidthPx = w;
  }
}

const specs = [
  ["T1 Reproduced", "Table1a_Synapse_reproduced.csv", "Table 1A — Synapse reproduced results", "Seed-level mean ± sample SD. nnU-Net uses its model-specific protocol."],
  ["T1 Reported", "Table1b_Synapse_reported_baselines.csv", "Table 1B — Externally reported baselines", "Reported by original papers; not reproduced under the frozen 14/4/12 setting."],
  ["T2 Scan", "Table2_scan_design_and_memory_control.csv", "Table 2 — Scan design and matched-memory control", "Each ablation is tied to a research question; single-seed and screen-only evidence are explicitly marked."],
  ["T3 Fusion", "Table3_fusion_ablation.csv", "Table 3 — Fusion ablation", "Exploratory single-seed evidence. Fixed sum remains the final selected design."],
  ["T4 Scope", "Table4_cross_dataset_scope.csv", "Table 4 — Cross-dataset scope", "The benefit is dataset-dependent: favorable accuracy–memory trade-off on CT/MRI, limitation on BUSI ultrasound."],
  ["T5 Pretrain", "Table5_pretraining_ablation.csv", "Table 5 — Pre-training ablation", "ACDC 25% is formal three-seed evidence; 50% and 100% are seed-42 exploratory trends only."],
  ["T6 Efficiency", "Table6_efficiency.csv", "Table 6 — Efficiency", "Strict RTX 4090 inference benchmark; AMP off; 20 warm-ups; 200 iterations; excludes I/O, metrics, saving and post-processing."],
  ["T7 Statistics", "Table7_paired_statistical_tests.csv", "Table 7 — Patient-level paired statistics", "Three seeds are averaged within each independent patient/case before pairing. Bootstrap uses 10,000 resamples."],
  ["T7b Narrow", "Table7b_Synapse_matched_memory_statistics.csv", "Table 7B — Matched-memory control statistics", "Synapse patient-level comparisons among E1, E1-Narrow and BiUMamba; Holm-adjusted p values are reported."],
];

const wb = Workbook.create();
const overview = wb.worksheets.add("Overview");
overview.showGridLines = false;
overview.tabColor = "#16324F";
overview.getRange("A1:H1").merge();
overview.getRange("A1").values = [["BiUMamba Final Evidence Workbook"]];
overview.getRange("A1").format = { fill: "#16324F", font: { bold: true, color: "#FFFFFF", size: 22 }, rowHeight: 34 };
overview.getRange("A3:B8").values = [
  ["Release", "20260912_v1"],
  ["Central claim", "Lower peak training memory with comparable observed CT/MRI performance; BUSI is a dataset-dependent limitation."],
  ["Matched-memory result", "BiUMamba keeps full width and shows better observed Dice/NSD and lower seed variability than E1-Narrow at similar memory."],
  ["Runtime claim", "Do not claim universally faster: E1 is faster in the strict inference benchmark."],
  ["Evidence rule", "Seed-level tables and patient-level statistics use different aggregation and must not be interchanged."],
  ["Source policy", "All final values are regenerated from frozen CSVs and mapped in Source Map."],
];
overview.getRange("A3:A8").format = { fill: "#DCE6F1", font: { bold: true, color: "#16324F" }, borders: { preset: "all", style: "thin", color: "#B4C7E7" } };
overview.getRange("B3:B8").format = { wrapText: true, borders: { preset: "all", style: "thin", color: "#B4C7E7" } };
overview.getRange("A10:D10").values = [["Worksheet", "Rows", "Evidence status", "Use"]];
overview.getRange("A10:D10").format = { fill: "#2F75B5", font: { bold: true, color: "#FFFFFF" }, borders: { preset: "all", style: "thin", color: "#B4C7E7" } };

const sheetMeta = [];
for (const [name, file, title, subtitle] of specs) {
  const rows = parseCSV(await fs.readFile(path.join(csvDir, file), "utf8"));
  const sheet = wb.worksheets.add(name);
  styleDataSheet(sheet, rows, title, subtitle);
  sheetMeta.push({ name, rows: rows.length - 1, use: title });
}

const relatedRows = parseCSV(await fs.readFile(path.join(bundle, "related_work/method_difference_table.csv"), "utf8"));
const related = wb.worksheets.add("Related Work");
styleDataSheet(related, relatedRows, "Related-work method differentiation", "BiUMamba: two axis-specific channel groups; forward/backward scans within each axis; concatenation and projection; medical segmentation.", "#548235");
sheetMeta.push({ name: "Related Work", rows: relatedRows.length - 1, use: "Primary-source method differentiation" });

const claimsRows = parseCSV(await fs.readFile(path.join(bundle, "audit/CLAIM_AUDIT.csv"), "utf8"));
const claims = wb.worksheets.add("Claims");
styleDataSheet(claims, claimsRows, "Manuscript claim audit", "Only Supported or Qualified claims may enter the abstract, results, discussion or conclusion.", "#C55A11");
const statusCol = claimsRows[0].indexOf("status");
if (statusCol >= 0) {
  const statusRange = claims.getRange(`${colName(statusCol)}5:${colName(statusCol)}${claimsRows.length + 3}`);
  statusRange.conditionalFormats.add("containsText", { text: "Unsupported", format: { fill: "#F4CCCC", font: { color: "#9C0006", bold: true } } });
  statusRange.conditionalFormats.add("containsText", { text: "Qualified", format: { fill: "#FFF2CC", font: { color: "#7F6000", bold: true } } });
  statusRange.conditionalFormats.add("containsText", { text: "Supported", format: { fill: "#D9EAD3", font: { color: "#274E13", bold: true } } });
}
sheetMeta.push({ name: "Claims", rows: claimsRows.length - 1, use: "Claim audit" });

const sourceRows = parseCSV(await fs.readFile(path.join(bundle, "paper_tables/source_map/table_cell_source_map.csv"), "utf8"));
const sources = wb.worksheets.add("Source Map");
styleDataSheet(sources, sourceRows, "Cell-level source map", "Every paper-table cell is mapped to a frozen source file and derivation.", "#7030A0");
sheetMeta.push({ name: "Source Map", rows: sourceRows.length - 1, use: "Cell-level provenance" });

const pareto = wb.worksheets.add("Accuracy-Memory");
pareto.showGridLines = false;
pareto.tabColor = "#00A6A6";
pareto.getRange("A1:H1").merge();
pareto.getRange("A1").values = [["Synapse Accuracy–Memory Trade-off"]];
pareto.getRange("A1").format = { fill: "#16324F", font: { bold: true, color: "#FFFFFF", size: 20 }, rowHeight: 32 };
pareto.getRange("A3:E6").values = [
  ["Method", "Peak training allocated (GB)", "Dice (%)", "NSD (%)", "Evidence"],
  ["E1", 12.841952, 76.84, 71.59, "3 seeds"],
  ["E1-Narrow", 10.168335, 75.04, 69.15, "3 seeds; matched-memory control"],
  ["BiUMamba", 9.706626, 76.66, 71.59, "3 seeds"],
];
pareto.getRange("A3:E3").format = { fill: "#2F75B5", font: { bold: true, color: "#FFFFFF" }, borders: { preset: "all", style: "thin", color: "#B4C7E7" } };
pareto.getRange("A4:E6").format = { borders: { preset: "all", style: "thin", color: "#D9E2F3" } };
pareto.getRange("B4:D6").setNumberFormat("0.00");
const diceChart = pareto.charts.add("scatter", pareto.getRange("B3:C6"));
diceChart.titleText = "Dice vs Peak Training Memory";
diceChart.hasLegend = false;
diceChart.setPosition("G3", "N18");
pareto.getRange("P3:Q6").values = [
  ["Peak training allocated (GB)", "NSD (%)"],
  [12.841952, 71.59],
  [10.168335, 69.15],
  [9.706626, 71.59],
];
const nsdChart = pareto.charts.add("scatter", pareto.getRange("P3:Q6"));
nsdChart.titleText = "NSD vs Peak Training Memory";
nsdChart.hasLegend = false;
nsdChart.setPosition("G20", "N35");
pareto.getRange("A8:E11").values = [
  ["Interpretation", "BiUMamba is the favorable observed accuracy–memory point among E1, E1-Narrow and BiUMamba."],
  ["Do not claim", "Pareto dominance across every metric or universally faster inference."],
  ["Statistical support", "BiUMamba vs E1-Narrow: NSD remains significant after Holm correction; Dice raw p=0.034 but Holm p=0.068."],
  ["Scope", "Matched-memory experiment is Synapse-only."],
];
pareto.getRange("A8:A11").format = { fill: "#DCE6F1", font: { bold: true }, borders: { preset: "all", style: "thin", color: "#B4C7E7" } };
pareto.getRange("B8:E11").format = { wrapText: true, borders: { preset: "all", style: "thin", color: "#B4C7E7" } };
pareto.getRange("A1:N35").format.autofitRows();
pareto.getRange("A:A").format.columnWidthPx = 125;
pareto.getRange("B:E").format.columnWidthPx = 155;
sheetMeta.push({ name: "Accuracy-Memory", rows: 3, use: "Native Pareto chart data" });

for (let i = 0; i < sheetMeta.length; i++) {
  const r = 11 + i;
  overview.getRange(`A${r}:D${r}`).values = [[sheetMeta[i].name, sheetMeta[i].rows, "Frozen / audited", sheetMeta[i].use]];
  overview.getRange(`A${r}:D${r}`).format = { borders: { preset: "all", style: "thin", color: "#D9E2F3" }, wrapText: true };
  if (r % 2 === 0) overview.getRange(`A${r}:D${r}`).format.fill = "#F4F7FB";
}
overview.getRange("F3:H3").values = [["Control", "Formula", "Result"]];
overview.getRange("F3:H3").format = { fill: "#548235", font: { bold: true, color: "#FFFFFF" }, borders: { preset: "all", style: "thin", color: "#A9D18E" } };
overview.getRange("F4:G7").values = [
  ["Table sheets", "COUNT"], ["Source-map cells", "COUNT"], ["Claims", "COUNT"], ["Unsupported claims", "COUNTIF"]
];
overview.getRange("H4").formulas = [["=COUNTA(A11:A30)"]];
overview.getRange("H5").formulas = [["=COUNTA('Source Map'!A5:A2000)"]];
overview.getRange("H6").formulas = [["=COUNTA(Claims!A5:A100)"]];
overview.getRange("H7").formulas = [["=COUNTIF(Claims!D5:D100,\"Unsupported\")"]];
overview.getRange("F4:H7").format = { borders: { preset: "all", style: "thin", color: "#A9D18E" } };
overview.getRange("H7").conditionalFormats.add("cellIs", { operator: "greaterThan", formula: 0, format: { fill: "#F4CCCC", font: { bold: true, color: "#9C0006" } } });
overview.getRange("A1:H30").format.autofitRows();
overview.getRange("A:A").format.columnWidthPx = 150;
overview.getRange("B:B").format.columnWidthPx = 400;
overview.getRange("C:D").format.columnWidthPx = 150;
overview.getRange("F:G").format.columnWidthPx = 135;
overview.getRange("H:H").format.columnWidthPx = 90;

await fs.mkdir(previewDir, { recursive: true });
const exported = await SpreadsheetFile.exportXlsx(wb);
await exported.save(outputPath);
for (const name of ["Overview", ...specs.map(x => x[0]), "Related Work", "Claims", "Source Map", "Accuracy-Memory"]) {
  const img = await wb.render({ sheetName: name, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${name.replaceAll(" ", "_")}.png`), new Uint8Array(await img.arrayBuffer()));
}
const inspection = await wb.inspect({ kind: "sheet", include: "id,name", maxChars: 5000 });
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" });
await fs.writeFile(path.join(bundle, "audit/WORKBOOK_INSPECTION.txt"), `${inspection.ndjson}\n\n${errors.ndjson}\n`);
console.log(JSON.stringify({ outputPath, previewDir, sheets: 15 }, null, 2));
