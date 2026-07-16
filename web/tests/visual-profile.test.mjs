import assert from "node:assert/strict";
import test from "node:test";
import { fighterVisualProfile } from "../app/game/visual-profile.ts";

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
});
