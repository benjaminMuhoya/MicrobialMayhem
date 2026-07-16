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
  assert.match(html, /Microscopic Gladiators/);
  assert.match(html, /One player/);
  assert.match(html, /data-testid="screen-home"/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton|Your site is taking shape/);
});

test("prototype includes six screens and responsive accessibility rules", async () => {
  const [page, css] = await Promise.all([readFile(new URL("app/page.tsx", root), "utf8"), readFile(new URL("app/globals.css", root), "utf8")]);
  for (const screen of ["home", "fighter", "colony", "arsenal", "environment", "preview", "arena", "results"]) assert.match(page, new RegExp(`screen-${screen}`));
  for (const screen of ["settings", "how", "lab"]) assert.match(page, new RegExp(`screen-${screen}`));
  assert.match(page, /Microbe Lab/);
  assert.match(page, /How to Play/);
  assert.match(page, /Music volume/);
  assert.match(page, /aria-label="Search bacterial fighters"/);
  assert.match(page, /aria-expanded/);
  assert.match(page, /Show different bacteria/);
  assert.match(page, /That is why we need more research/);
  assert.match(page, /Biological interpretation/);
  assert.doesNotMatch(page, /Biology first|Outcome precomputed|8\.0s|animation dramatizes/i);
  for (const shape of ["coccus", "rod", "vibrio", "spiral", "filament", "irregular"]) assert.match(page + css, new RegExp(`microbe--${shape}`));
  for (const detail of ["microbe__face", "microbe__pili", "microbe__capsule", "microbe__satellites"]) assert.match(page + css, new RegExp(detail));
  for (const motif of ["motif-cold", "motif-hot", "motif-salty", "motif-alkaline", "motif-acidic", "motif-in-the-presence-of-antibiotics", "motif-neutral"]) assert.match(page + css, new RegExp(motif));
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

test("packages original modular audio for offline mobile play", async () => {
  const feedback = await readFile(new URL("app/game/feedback.ts", root), "utf8");
  for (const file of ["setup_theme.wav", "battle_theme.wav", "results_theme.wav", "select.wav", "impact.wav", "victory.wav"]) {
    await readFile(new URL(`../public/audio/${file.includes("theme") ? "music" : "sfx"}/${file}`, import.meta.url));
  }
  assert.match(feedback, /visibilitychange|suspend|resume/);
  assert.match(feedback, /lastCue/);
});
