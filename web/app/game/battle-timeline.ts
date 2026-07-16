import type { Winner } from "./types.ts";

export const BATTLE_DURATION_MS = 8000;
export const BATTLE_CUES = [
  [350,"entrance"],[1050,"anticipate"],[1550,"attack"],[2250,"defend"],[2900,"counter"],[3650,"dodge"],
  [4250,"playerAbility"],[5050,"environment"],[5650,"opponentAbility"],[6350,"pause"],[6850,"finish"],[7550,"resolution"],
] as const;

export function battleHealth(progress:number,winner:Winner):[number,number]{
  const p=Math.max(0,Math.min(1,progress)); if(p<.82)return [Math.round(Math.max(42,100-55*p+6*Math.max(0,p-.48))),Math.round(Math.max(42,100-52*p-5*Math.max(0,p-.35)))];
  const t=(p-.82)/.18; const eased=t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
  if(winner==="A")return[Math.round(50-15*eased),Math.round(45*(1-eased))]; if(winner==="B")return[Math.round(45*(1-eased)),Math.round(50-15*eased)]; return[Math.round(45-37*eased),Math.round(45-37*eased)];
}

export class CompletionGate { private fired=false; finish(callback:()=>void){if(this.fired)return false;this.fired=true;callback();return true} get complete(){return this.fired} }
