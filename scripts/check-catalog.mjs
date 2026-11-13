import { readFileSync } from "node:fs";

const data = JSON.parse(readFileSync(new URL("../data/nist-cswp-29.json", import.meta.url), "utf8"));
const doc = data.documents[0];
const elements = doc.elements;
const byId = new Map(elements.map((el) => [el.id, el]));
let failed = false;

function fail(message) {
  failed = true;
  console.error(message);
}

const counts = {
  function: elements.filter((el) => el.elementType === "function").length,
  category: elements.filter((el) => el.elementType === "category").length,
  subcategory: elements.filter((el) => el.elementType === "subcategory").length,
};

if (counts.function !== 6 || counts.category !== 22 || counts.subcategory !== 106) {
  fail(`expected 6/22/106, got ${counts.function}/${counts.category}/${counts.subcategory}`);
}
if (data.sourceChecked !== "2026-11-13") fail("sourceChecked drifted");
if (doc.published !== "2024-02-26" || doc.publicationId !== "NIST CSWP 29") fail("publication identity drifted");

const ids = new Set();
for (const el of elements) {
  if (ids.has(el.id)) fail(`duplicate id ${el.id}`);
  ids.add(el.id);
  if (!el.outcome || el.outcome.length < 12) fail(`short outcome ${el.id}`);
  if (!el.explanationZhTW || el.explanationZhTW.length < 8) fail(`missing explanation ${el.id}`);
  if (el.parentId && !byId.has(el.parentId)) fail(`bad parent ${el.id}`);
  if (el.elementType !== "subcategory" && !el.navLabelZhTW) fail(`missing nav label ${el.id}`);
  if (el.elementType === "subcategory" && el.navLabelZhTW) fail(`unexpected nav label ${el.id}`);
}

if (ids.has("ID.AM-06")) fail("ID.AM-06 must stay absent");
for (const id of ["PR.DS-03", "DE.CM-04", "DE.AE-01", "RS.AN-01", "RS.CO-01", "RC.CO-01"]) {
  if (ids.has(id)) fail(`${id} is a numbering gap and must stay absent`);
}

const rc = byId.get("RC.RP-06");
if (!rc || !rc.outcome.endsWith("incident-related documentation is completed")) {
  fail(`RC.RP-06 outcome is wrong: ${rc && rc.outcome}`);
}
if (rc.outcome.includes("incidentrelated") || rc.outcome.includes("incident- related")) {
  fail("RC.RP-06 still has the hyphenation artifact");
}

const org = byId.get("GV.OC");
if (!org.outcome.includes("—") || !org.outcome.includes("organization’s")) {
  fail("GV.OC did not keep Appendix A punctuation");
}
if (!byId.get("PR.AA").outcome.includes("hardware and managed commensurate")) {
  fail("PR.AA outcome drifted");
}
if (byId.get("ID.IM").outcome.includes("procedures, and")) fail("ID.IM picked up an Oxford comma");

const simplified = /[这为对从后发过还进现设认让该经组软网数识护复应与么们产线门问业国体机关报险络据并里后]/;
for (const el of elements) {
  const hit = `${el.explanationZhTW}${el.navLabelZhTW ?? ""}`.match(simplified);
  if (hit) fail(`simplified character ${hit[0]} in ${el.id}`);
}

const expectedOrder = ["GV", "ID", "PR", "DE", "RS", "RC"];
const actualOrder = elements.filter((el) => el.elementType === "function").map((el) => el.id);
if (actualOrder.join() !== expectedOrder.join()) fail(`function order ${actualOrder}`);

if (failed) process.exit(1);
console.log("catalog ok", `${counts.function}/${counts.category}/${counts.subcategory}`);
