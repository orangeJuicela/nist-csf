# NIST CSF 2.0 guide

Traditional Chinese (Taiwan) map of the [NIST Cybersecurity Framework 2.0](https://www.nist.gov/cyberframework) Core, NIST CSWP 29, published 2024-02-26.

Live site: https://orangejuicela.github.io/nist-csf/

The site is a navigable guide, not a translation. English outcome statements are reproduced from Appendix A of NIST CSWP 29. Traditional Chinese explanations are unofficial. Counts: 6 Functions, 22 Categories, 106 Subcategories. Identifier gaps such as `ID.AM-06` are intentional and are kept as absences. The PDF line-break in `RC.RP-06` is stored as `incident-related`.

## Data

`data/nist-cswp-29.json` is the catalog. Each NIST publication is a document; elements form a tree through `parentId`. CSF 2.0 uses `function`, `category`, and `subcategory`. Further publications (SP 800-53, SP 800-61, SP 800-63, SP 800-207, and others) can be added as more documents, or as separate relationship files keyed by element id. Informative references are not embedded.

`scripts/build_catalog.py` regenerates the English fields from a local `pdftotext` extract of Appendix A. It is not part of the site build. `navLabelZhTW` and `explanationZhTW` are unofficial.

Source checked: 2026-11-13.

NIST publications created by NIST employees are United States government works. They are not subject to copyright in the United States and are in the public domain there. NIST notes that its publications may be protected outside the United States.

Reprinted courtesy of the National Institute of Standards and Technology, U.S. Department of Commerce.

## Develop

```bash
npm install
npm run build
npm run preview
```

GitHub Pages is published by `.github/workflows/pages.yml` from the `main` branch, with base path `/nist-csf/`. Pages source must be **GitHub Actions**.
