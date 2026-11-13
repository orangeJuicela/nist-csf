import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const data = JSON.parse(readFileSync(new URL("../data/nist-cswp-29.json", import.meta.url), "utf8"));
const elements = data.documents[0].elements;

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) walk(path, acc);
    else acc.push(path);
  }
  return acc;
}

const files = walk("dist");
const html = files.filter((path) => path.endsWith(".html")).map((path) => readFileSync(path, "utf8")).join("\n");
let failed = false;
function fail(message) {
  failed = true;
  console.error(message);
}

for (const el of elements) {
  if (!html.includes(el.id)) fail(`built HTML is missing ${el.id}`);
  if (!html.includes(el.explanationZhTW.slice(0, 12))) fail(`built HTML is missing explanation for ${el.id}`);
}
if (!html.includes("incident-related documentation is completed")) fail("RC.RP-06 text missing from build");
if (html.includes("incident- related") || html.includes("incidentrelated")) fail("hyphenation artifact in build");
if (!html.includes("非官方說明")) fail("unofficial label missing");
if (!html.includes("2026-11-13")) fail("source checked date missing");
if (!html.includes("/nist-csf/function/gv/")) fail("base path missing from function links");
if (html.includes('href="/function/')) fail("root-absolute function link without base path");

const required = [
  "dist/index.html",
  "dist/about/index.html",
  "dist/search/index.html",
  "dist/search-index.json",
  "dist/function/gv/index.html",
  "dist/function/rc/index.html",
  "dist/category/gv-oc/index.html",
  "dist/category/id-am/index.html",
  "dist/category/rc-rp/index.html",
  "dist/404.html",
];
for (const path of required) {
  if (!files.includes(path)) fail(`missing ${path}`);
}

const index = JSON.parse(readFileSync("dist/search-index.json", "utf8"));
if (index.length !== 134) fail(`search index length ${index.length}`);
const home = readFileSync("dist/index.html", "utf8");
for (const text of ["6", "22", "106"]) {
  if (!home.includes(text)) fail(`home missing count ${text}`);
}

if (failed) process.exit(1);
console.log("dist ok", files.length, "files");
