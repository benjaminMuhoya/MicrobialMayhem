import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { scoreBattle } from "../app/game/scoring.ts";

const data=JSON.parse(await readFile(new URL("../../tests/fixtures/battle_parity.json",import.meta.url),"utf8"));
for(const fixture of data.fixtures)test(`Python scoring parity: ${fixture.name}`,()=>{
  const result=scoreBattle({mode:fixture.mode,seed:fixture.seed,environment:fixture.environment,player:fixture.player,opponent:fixture.opponent,playerColonyCfu:fixture.playerColonyCfu,opponentColonyCfu:fixture.opponentColonyCfu,playerArsenal:fixture.playerArsenal,opponentArsenal:fixture.opponentArsenal});
  assert.equal(result.winner,fixture.expected.winner); assert.equal(result.player.total,fixture.expected.player.total); assert.equal(result.opponent.total,fixture.expected.opponent.total);
  assert.deepEqual(result.player.components.map(c=>[c.name,c.value,c.includedInTotal]),fixture.expected.player.components.map(c=>[c.name,c.value,c.includedInTotal]));
  assert.deepEqual(result.opponent.components.map(c=>[c.name,c.value,c.includedInTotal]),fixture.expected.opponent.components.map(c=>[c.name,c.value,c.includedInTotal]));
});
