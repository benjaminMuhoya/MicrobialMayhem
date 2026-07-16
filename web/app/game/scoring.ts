import { PythonRandom } from "./python-random.ts";
import type { BattleResult, BattleSetup, Environment, Fighter, ScoreBreakdown, ScoreComponent } from "./types.ts";

export const BASE_SCORE = 25;
export const ENV_MATCH_BONUS = 12;
export const NO_EVIDENCE_PENALTY = -3;
export const RANDOM_VARIATION_RANGE = 2;
const ADAPTATION: Partial<Record<Environment,string>> = { Cold:"Cryophile", Hot:"Thermophile", Salty:"Halophile", Alkaline:"Alkaliphile", Acidic:"Acidophile", "In the presence of antibiotics":"Drug resistant" };
const ADAPTATION_TRAITS = new Set(Object.values(ADAPTATION));
const round2 = (value:number) => Math.round((value + Number.EPSILON) * 100) / 100;

export function colonyScoreFromCfu(cfu: number) { const safe = Math.max(0, Number(cfu)); return Math.round((Math.log10(safe + 1) / Math.log10(1001) * 10) * 10) / 10; }
export function environmentStatus(entry: Fighter, environment: Environment): "MATCHED"|"MISMATCHED"|"UNKNOWN" {
  const target = ADAPTATION[environment]; if (!target) return "UNKNOWN";
  if (entry.traits.some((e) => e.trait === target)) return "MATCHED";
  return entry.traits.some((e) => ADAPTATION_TRAITS.has(e.trait)) ? "MISMATCHED" : "UNKNOWN";
}
function activityScore(entry:Fighter) { const text=entry.activities.join(" ").toLowerCase(); let score=0, matched=false; if(text.includes("antibacterial")||text.includes("antimicrobial")){score+=3;matched=true} if(text.includes("antifungal")){score+=2;matched=true} if(text.includes("cytotoxic")||text.includes("toxic")||text.includes("toxin")){score+=2;matched=true} if(text.includes("siderophore")||text.includes("iron")){score+=2;matched=true} if(entry.activities.length&&!matched)score+=1; return Math.min(5,score) }
function defenseScore(entry:Fighter) { let best=0; for(const evidence of entry.traits){if(evidence.trait!=="Drug resistant")continue; const text=`${evidence.field} ${evidence.explanation}`.toLowerCase(); if(evidence.evidenceLevel.startsWith("Direct")&&(text.includes("immunity")||text.includes("efflux")||text.includes("resistan")))best=Math.max(best,5);else if(text.includes("self-resistance"))best=Math.max(best,4);else best=Math.max(best,2)} return best }
function component(name:string,value:number,explanation:string,includedInTotal=true):ScoreComponent{return{name,value,explanation,includedInTotal}}

function scoreFighter(entry:Fighter, environment:Environment, cfu:number, arsenal:boolean, neitherMatches:boolean, rng:PythonRandom):ScoreBreakdown {
  const status=environmentStatus(entry,environment); const target=ADAPTATION[environment]??"environmental adaptation";
  const components=[component("Base",BASE_SCORE,"Every fighter starts from the same neutral base score."),component("Colony",colonyScoreFromCfu(cfu),`${cfu} CFU contributed points using the shared dynamic colony formula.`)];
  if(environment==="Neutral")components.push(component("Environment",0,"The neutral environment does not change either fighter's score."));
  else if(status==="MATCHED")components.push(component("Environment",ENV_MATCH_BONUS,`Supported ${target.toLowerCase()} evidence matches the ${environment} environment.`));
  else if(neitherMatches)components.push(component("Environment",NO_EVIDENCE_PENALTY,`No supported ${target.toLowerCase()} match was found; uncertainty applies a modest shared penalty.`));
  else if(status==="MISMATCHED")components.push(component("Environment",0,`Traits are documented, but none match the ${environment} environment; no bonus was awarded.`));
  else components.push(component("Environment",0,`No supported ${target.toLowerCase()} evidence was available; unknown is not treated as a confirmed mismatch.`));
  const defense=defenseScore(entry), arsenalScore=arsenal?Math.min(entry.accessions.length,5):0, activeCount=arsenal?entry.accessions.length:0, knownActivity=activityScore(entry);
  components.push(component("Resistance defense",defense,"Resistance, immunity, or efflux evidence contributes defense; antimicrobial production alone does not."));
  components.push(component("BGC arsenal",arsenalScore,`${activeCount} known MIBiG BGC(s) brought into battle; score is capped at 5.`,false));
  components.push(component("Known activity",knownActivity,"Capped score from documented biological activity.",false));
  components.push(component("Offense total",arsenalScore+knownActivity,`Offense subtotal = BGC arsenal ${arsenalScore>=0?"+":""}${arsenalScore.toFixed(1)} + known activity +${knownActivity.toFixed(1)}.`));
  components.push(component("Battle variation",round2(rng.uniform(-RANDOM_VARIATION_RANGE,RANDOM_VARIATION_RANGE)),"Small controlled random variation for close battles."));
  return {fighterName:entry.fullName,environmentStatus:status,colonyCfu:Math.trunc(cfu),total:round2(components.filter(c=>c.includedInTotal).reduce((sum,c)=>sum+c.value,0)),components};
}

export function scoreBattle(setup:BattleSetup):BattleResult {
  const rng=new PythonRandom(setup.seed); const neither=environmentStatus(setup.player,setup.environment)!=="MATCHED"&&environmentStatus(setup.opponent,setup.environment)!=="MATCHED";
  const player=scoreFighter(setup.player,setup.environment,setup.playerColonyCfu,setup.playerArsenal,neither,rng); const opponent=scoreFighter(setup.opponent,setup.environment,setup.opponentColonyCfu,setup.opponentArsenal,neither,rng);
  return {player,opponent,winner:player.total>opponent.total?"A":opponent.total>player.total?"B":"tie"};
}

