import type { APIRoute } from "astro";
import { searchDocuments } from "../lib/catalog";

export const GET: APIRoute = () =>
  new Response(JSON.stringify(searchDocuments()), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
    },
  });
