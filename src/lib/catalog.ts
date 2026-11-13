import raw from "../../data/nist-cswp-29.json";

export type ElementType = "function" | "category" | "subcategory";

export interface CatalogElement {
  id: string;
  elementType: ElementType;
  parentId: string | null;
  name: string | null;
  outcome: string;
  sort: number;
  navLabelZhTW: string | null;
  explanationZhTW: string;
}

const TYPES = new Set<ElementType>(["function", "category", "subcategory"]);

function asElement(value: (typeof raw.documents)[0]["elements"][number]): CatalogElement {
  if (!TYPES.has(value.elementType as ElementType)) {
    throw new Error(`Unknown elementType on ${value.id}`);
  }
  return value as CatalogElement;
}

export const sourceChecked = raw.sourceChecked;
export const csf = raw.documents[0];
export const elements: CatalogElement[] = csf.elements.map(asElement);

const byId = new Map(elements.map((el) => [el.id, el]));

export const functions = elements.filter((el) => el.elementType === "function");
export const categories = elements.filter((el) => el.elementType === "category");
export const subcategories = elements.filter((el) => el.elementType === "subcategory");

export function getElement(id: string): CatalogElement {
  const el = byId.get(id);
  if (!el) throw new Error(`Unknown element ${id}`);
  return el;
}

export function childrenOf(id: string): CatalogElement[] {
  return elements.filter((el) => el.parentId === id);
}

export function subcategoryCount(id: string): number {
  const el = getElement(id);
  if (el.elementType === "category") return childrenOf(id).length;
  if (el.elementType === "function") {
    return childrenOf(id).reduce((sum, cat) => sum + childrenOf(cat.id).length, 0);
  }
  return 0;
}

export function owningFunction(el: CatalogElement): CatalogElement {
  let current: CatalogElement | undefined = el;
  while (current && current.elementType !== "function") {
    current = current.parentId ? byId.get(current.parentId) : undefined;
  }
  if (!current) throw new Error(`No function for ${el.id}`);
  return current;
}

export function slug(id: string): string {
  return id.toLowerCase().replace(/\./g, "-");
}

export function href(path = ""): string {
  const base = import.meta.env.BASE_URL;
  return base + path.replace(/^\//, "");
}

export function elementHref(el: CatalogElement): string {
  if (el.elementType === "function") return href(`function/${slug(el.id)}/`);
  if (el.elementType === "category") return href(`category/${slug(el.id)}/`);
  const parent = getElement(el.parentId ?? "");
  return `${href(`category/${slug(parent.id)}/`)}#${el.id}`;
}

export function pageLabel(el: CatalogElement): string {
  if (el.elementType === "function") return `${el.navLabelZhTW}（${el.id}）`;
  return `${el.id} ${el.navLabelZhTW ?? ""}`.trim();
}

export function readingOrder(): CatalogElement[] {
  const pages: CatalogElement[] = [];
  for (const fn of functions) {
    pages.push(fn);
    pages.push(...childrenOf(fn.id));
  }
  return pages;
}

export function neighbors(id: string): { prev: CatalogElement | null; next: CatalogElement | null } {
  const pages = readingOrder();
  const index = pages.findIndex((page) => page.id === id);
  return {
    prev: index > 0 ? pages[index - 1] : null,
    next: index >= 0 && index < pages.length - 1 ? pages[index + 1] : null,
  };
}

/** Absent numeric suffixes from 01 through the highest published suffix. */
export function missingSubcategoryIds(categoryId: string): string[] {
  const nums = childrenOf(categoryId).map((sub) => Number(sub.id.slice(sub.id.lastIndexOf("-") + 1)));
  const max = Math.max(...nums);
  const have = new Set(nums);
  const missing: string[] = [];
  for (let n = 1; n <= max; n += 1) {
    if (!have.has(n)) missing.push(`${categoryId}-${String(n).padStart(2, "0")}`);
  }
  return missing;
}

export function searchDocuments() {
  return elements.map((el) => ({
    id: el.id,
    elementType: el.elementType,
    name: el.name,
    navLabelZhTW: el.navLabelZhTW,
    outcome: el.outcome,
    explanationZhTW: el.explanationZhTW,
    href: elementHref(el),
    functionId: owningFunction(el).id,
  }));
}

export const counts = {
  functions: functions.length,
  categories: categories.length,
  subcategories: subcategories.length,
};
