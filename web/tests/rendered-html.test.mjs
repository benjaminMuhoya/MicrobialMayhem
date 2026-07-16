import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(new Request("http://localhost/", { headers: { accept: "text/html" } }), { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } }, { waitUntil() {}, passThroughOnException() {} });
}

test("server-renders the Microbial Mayhem design prototype", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /<title>Microbial Mayhem/);
  assert.match(html, /Small cells/);
  assert.match(html, /One player/);
  assert.match(html, /data-testid="screen-home"/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton|Your site is taking shape/);
});

test("prototype includes six screens and responsive accessibility rules", async () => {
  const [page, css] = await Promise.all([readFile(new URL("app/page.tsx", root), "utf8"), readFile(new URL("app/globals.css", root), "utf8")]);
  for (const screen of ["home", "fighter", "colony", "arsenal", "environment", "preview", "arena", "results"]) assert.match(page, new RegExp(`screen-${screen}`));
  assert.match(page, /aria-label="Search bacterial fighters"/);
  assert.match(page, /aria-expanded/);
  assert.match(css, /@media\(max-width:620px\)/);
  assert.match(css, /prefers-reduced-motion:reduce/);
  assert.match(css, /focus-visible/);
});

test("ships installable offline metadata and a versioned cache", async () => {
  const manifest = JSON.parse(await readFile(new URL("../public/manifest.webmanifest", import.meta.url), "utf8"));
  const worker = await readFile(new URL("../public/sw.js", import.meta.url), "utf8");
  assert.equal(manifest.display, "standalone");
  assert.match(worker, /microbial-mayhem-v0\.4\.0/);
  assert.match(worker, /fighters-core\.v2\.json/);
});
