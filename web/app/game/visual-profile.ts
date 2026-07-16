import type { Fighter } from "./types";

export type VisualShape="coccus"|"rod"|"curved"|"vibrio"|"spiral"|"filament"|"chain"|"cluster"|"spore"|"capsule"|"irregular";
export type VisualAppendage="none"|"polar"|"tuft"|"peritrichous"|"pili";
export type VisualExpression="bold"|"cheery"|"focused"|"grumpy"|"curious";

const fallbackShapes:VisualShape[]=["coccus","rod","curved","vibrio","spiral","filament","chain","cluster","spore","capsule","irregular"];
const palettes=[
  ["#ff755f","#ffc15f"],["#7bf2bc","#52b7ff"],["#ad8bff","#ff82bd"],["#d7f171","#75e6a4"],
  ["#ff9f68","#ffe66d"],["#68d8ff","#c9f4ff"],["#f080c0","#ad8bff"],["#9be564","#4dd6a4"],
  ["#ff6f91","#ffb86c"],["#7fd1b9","#d7f171"],["#b8a1ff","#78c6ff"],["#f2c14e","#f78154"],
] as const;
const appendages:VisualAppendage[]=["none","polar","tuft","peritrichous","pili"];
const expressions:VisualExpression[]=["bold","cheery","focused","grumpy","curious"];

export function visualHash(value:string){let hash=2166136261;for(let i=0;i<value.length;i++){hash^=value.charCodeAt(i);hash=Math.imul(hash,16777619)}return hash>>>0}

function recordedShape(value?:string):VisualShape|undefined{const shape=(value||"").toLowerCase();if(!shape)return undefined;if(shape.includes("chain")||shape.includes("strepto"))return "chain";if(shape.includes("cluster")||shape.includes("staph"))return "cluster";if(shape.includes("spore"))return "spore";if(shape.includes("capsul"))return "capsule";if(shape.includes("filament")||shape.includes("hyph")||shape.includes("branch"))return "filament";if(shape.includes("spir")||shape.includes("spiro")||shape.includes("helix"))return "spiral";if(shape.includes("vibr")||shape.includes("comma"))return "vibrio";if(shape.includes("curv"))return "curved";if(shape.includes("cocc")||shape.includes("spher"))return "coccus";if(shape.includes("rod")||shape.includes("bacill"))return "rod";return undefined}

export function fighterVisualProfile(fighter:Fighter){
  const hash=visualHash(`${fighter.catalogId}|${fighter.fullName}`);
  const motility=(fighter.motility||"").toLowerCase();
  const shape=recordedShape(fighter.cellShape)??fallbackShapes[hash%fallbackShapes.length];
  const appendage:VisualAppendage=motility.includes("non-motile")||motility.includes("nonmotile")?"pili":motility.includes("motile")?appendages[1+(hash%3)]:appendages[(hash>>>5)%appendages.length];
  const palette=palettes[(hash>>>9)%palettes.length];
  return {shape,appendage,expression:expressions[(hash>>>14)%expressions.length],primary:palette[0],secondary:palette[1],motion:(hash>>>18)%3,tilt:(hash%17)-8};
}

export const duelShapeOrder:VisualShape[]=["rod","coccus","vibrio","spiral","filament","cluster","chain","spore","capsule","curved","irregular"];
