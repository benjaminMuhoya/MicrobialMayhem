import assert from "node:assert/strict"; import test from "node:test";
import fs from "node:fs";
import { BATTLE_CUES,BATTLE_DURATION_MS,CompletionGate,battleHealth } from "../app/game/battle-timeline.ts";
test("battle cues remain an exact ten-second deterministic presentation",()=>{assert.equal(BATTLE_DURATION_MS,10000);assert.equal(BATTLE_CUES[0][0],0);assert.deepEqual(BATTLE_CUES.map(c=>c[1]),["entrance","anticipate","attack","defend","counter","dodge","playerAbility","environment","opponentAbility","recovery","finish","resolution"])});
test("normal completion and skip enter results exactly once",()=>{const gate=new CompletionGate();let shown=0;assert.equal(gate.finish(()=>shown++),true);assert.equal(gate.finish(()=>shown++),false);assert.equal(shown,1)});
test("health hides the outcome until the finale",()=>{for(const winner of ["A","B","tie"]){const [a,b]=battleHealth(.81,winner);assert.ok(a>=42&&b>=42)}assert.equal(battleHealth(1,"A")[1],0);assert.equal(battleHealth(1,"B")[0],0)});
test("Phaser results transition uses the same wall-clock ten-second duration",()=>{const arena=fs.readFileSync(new URL("../app/components/PhaserArena.tsx",import.meta.url),"utf8");assert.ok(arena.includes("window.setTimeout(()=>gate.finish(()=>callback.current()),BATTLE_DURATION_MS)") )});
