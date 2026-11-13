import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://orangejuicela.github.io",
  base: "/nist-csf",
  trailingSlash: "always",
  compressHTML: true,
});
