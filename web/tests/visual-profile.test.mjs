import assert from "node:assert/strict";
import test from "node:test";
import { FIGHTER_ANIMATIONS, colonyVisualCount, differentiatedDuelProfiles, fighterVisualProfile, livingColonyCount } from "../app/game/visual-profile.ts";
import { clearSpriteSheetCache, loadSpriteManifest } from "../app/game/sprite-sheets.ts";
import fs from "node:fs";

const fighter=(id,cellShape,motility)=>({catalogId:id,fullName:`Microbe ${id}`,cellShape,motility,accessions:[],products:[],activities:[],traits:[]});

test("fighter appearance is stable and respects recorded morphology",()=>{
  const bacillus=fighter("bacillus","rod");
  assert.deepEqual(fighterVisualProfile(bacillus),fighterVisualProfile(bacillus));
  assert.equal(fighterVisualProfile(bacillus).shape,"rod");
  assert.equal(fighterVisualProfile(fighter("vibrio","curved rod")).shape,"curved");
  assert.equal(fighterVisualProfile(fighter("staph","coccus in clusters")).shape,"cluster");
});

test("fighters without morphology still receive diverse stable identities",()=>{
  const profiles=Array.from({length:24},(_,index)=>fighterVisualProfile(fighter(`catalog:${index}`,undefined)));
  assert.ok(new Set(profiles.map(profile=>profile.shape)).size>=7);
  assert.ok(new Set(profiles.map(profile=>`${profile.primary}-${profile.secondary}`)).size>=8);
  assert.ok(new Set(profiles.map(profile=>profile.expression)).size>=4);
  assert.ok(new Set(profiles.map(profile=>profile.appendage)).size>=4);
  assert.ok(new Set(profiles.map(profile=>profile.texture)).size>=4);
  assert.ok(new Set(profiles.map(profile=>profile.archetype)).size>=4);
});

test("similar opponents receive distinct presentation without changing fighter data",()=>{
  const left=fighter("same-a","rod","motile"),right=fighter("same-b","rod","motile");
  const [leftProfile,rightProfile]=differentiatedDuelProfiles(left,right);
  assert.notEqual(`${leftProfile.shape}-${leftProfile.primary}-${leftProfile.appendage}`,`${rightProfile.shape}-${rightProfile.primary}-${rightProfile.appendage}`);
  assert.equal(left.cellShape,"rod");
  assert.equal(right.cellShape,"rod");
});

test("colony population visibly follows selected CFU and presentation health",()=>{
  assert.ok(colonyVisualCount(1000,44)>colonyVisualCount(50,44));
  assert.equal(colonyVisualCount(500,44),colonyVisualCount(500,44));
  assert.ok(livingColonyCount(1000,20,44)<livingColonyCount(1000,100,44));
  assert.equal(livingColonyCount(500,72,44),livingColonyCount(500,72,44));
});

test("the shared visual contract covers every requested battle pose",()=>{
  assert.deepEqual(Object.keys(FIGHTER_ANIMATIONS),["entrance","idle","ready","move","anticipate","attack","defend","impact","arsenal","stress","decline","recover","victory","defeat"]);
});

test("sprite sheet manifest has an APK-safe procedural fallback",async()=>{
  clearSpriteSheetCache();
  assert.deepEqual(await loadSpriteManifest(),{});
  const manifest=JSON.parse(fs.readFileSync(new URL("../public/fighters/manifest.json",import.meta.url),"utf8"));
  assert.equal(manifest["shape:coccus"].idle.frames,6);
  assert.ok(fs.existsSync(new URL("../public/fighters/coccus-idle.svg",import.meta.url)));
  const arena=fs.readFileSync(new URL("../app/components/PhaserArena.tsx",import.meta.url),"utf8");
  const page=fs.readFileSync(new URL("../app/page.tsx",import.meta.url),"utf8");
  assert.match(arena,/fighterSpriteSheet/);
  assert.match(page,/sheet-microbe/);
});
