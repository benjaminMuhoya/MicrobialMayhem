import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const output = new URL("../dist/pages/", import.meta.url);
const client = new URL("../dist/client/", import.meta.url);
const workerUrl = new URL("../dist/server/index.js", import.meta.url);

await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await cp(client, output, { recursive: true });

const { default: worker } = await import(`${pathToFileURL(workerUrl.pathname).href}?pages=${Date.now()}`);
const response = await worker.fetch(
  new Request("https://microbial-mayhem.invalid/", { headers: { accept: "text/html" } }),
  { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
  { waitUntil() {}, passThroughOnException() {} },
);

if (!response.ok) throw new Error(`Unable to render the GitHub Pages shell (${response.status}).`);

const html = (await response.text())
  // Vinext embeds its hydration entry point and RSC asset references inside
  // inline scripts, so rewriting only HTML href/src attributes leaves a
  // visually complete but non-interactive page on a project Pages URL.
  .replaceAll("/assets/", "./assets/")
  .replaceAll('href="/', 'href="./')
  .replaceAll('src="/', 'src="./');

await writeFile(new URL("index.html", output), html);
await writeFile(new URL(".nojekyll", output), "");

const built = await readFile(new URL("index.html", output), "utf8");
if (
  !built.includes("Microbial Mayhem") ||
  !built.includes("./assets/") ||
  built.includes('import("/assets/') ||
  built.includes('href="/assets/')
) {
  throw new Error("GitHub Pages output did not contain the expected game shell and relative assets.");
}
