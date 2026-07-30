import type { Winner } from "./types.ts";

export const BATTLE_DURATION_MS = 10000;
export const BATTLE_CUES = [
  [0,"entrance"],[1050,"anticipate"],[1750,"attack"],[2650,"defend"],[3450,"counter"],[4250,"dodge"],
  [5050,"playerAbility"],[6050,"environment"],[6850,"opponentAbility"],[7650,"recovery"],[8350,"finish"],[9300,"resolution"],
] as const;

export function battleHealth(progress:number,winner:Winner):[number,number]{
  const p=Math.max(0,Math.min(1,progress)); if(p<.82)return [Math.round(Math.max(42,100-55*p+6*Math.max(0,p-.48))),Math.round(Math.max(42,100-52*p-5*Math.max(0,p-.35)))];
  const t=(p-.82)/.18; const eased=t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
  if(winner==="A")return[Math.round(50-15*eased),Math.round(45*(1-eased))]; if(winner==="B")return[Math.round(45*(1-eased)),Math.round(50-15*eased)]; return[Math.round(45-37*eased),Math.round(45-37*eased)];
}

export class CompletionGate { private fired=false; finish(callback:()=>void){if(this.fired)return false;this.fired=true;callback();return true} get complete(){return this.fired} }
