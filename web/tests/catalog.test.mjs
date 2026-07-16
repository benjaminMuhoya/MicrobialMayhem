import assert from "node:assert/strict";
import test from "node:test";
import { generateOpponentCfu, sampleFighters, searchFighters } from "../app/game/catalog.ts";

const fighters = Array.from({ length: 12 }, (_, index) => ({
  catalogId: `bacdive:${index}`, fullName: index === 3 ? "Bacillus subtilis 168" : `Microbium example${index}`,
  displayName: index === 4 ? "Friendly culture" : "", strain: index === 5 ? "ATCC 9005" : "",
  accessions: index === 6 ? ["BGC000006"] : [], products: [], activities: [], traits: [],
}));

test("reshuffling changes the displayed roster and preserves a locked fighter", () => {
  const first = sampleFighters(fighters, 6, 10);
  const second = sampleFighters(fighters, 6, 11, first, fighters[0]);
  assert.notDeepEqual(second.map((item) => item.catalogId), first.map((item) => item.catalogId));
  assert.equal(second[0].catalogId, fighters[0].catalogId);
});

test("seeded opponent colony matches Python randint", () => {
  assert.equal(generateOpponentCfu(12), 485);
});

test("catalog search covers scientific, display, genus, strain, and identifiers", () => {
  assert.equal(searchFighters(fighters, "Bacillus")[0].catalogId, "bacdive:3");
  assert.equal(searchFighters(fighters, "Friendly")[0].catalogId, "bacdive:4");
  assert.equal(searchFighters(fighters, "ATCC 9005")[0].catalogId, "bacdive:5");
  assert.equal(searchFighters(fighters, "BGC000006")[0].catalogId, "bacdive:6");
  assert.equal(searchFighters(fighters, "bacdive:3")[0].catalogId, "bacdive:3");
  assert.deepEqual(searchFighters(fighters, "no-such-organism"), []);
});
