import type { Fighter } from "./types";

export type VisualShape="coccus"|"rod"|"curved"|"vibrio"|"spiral"|"filament"|"chain"|"cluster"|"spore"|"capsule"|"irregular";
export type VisualAppendage="none"|"polar"|"tuft"|"peritrichous"|"pili";
export type VisualExpression="bold"|"cheery"|"focused"|"grumpy"|"curious";
export type VisualTexture="granular"|"smooth"|"banded"|"speckled"|"translucent";
export type VisualPersonality="sprinter"|"guardian"|"coordinator"|"trickster"|"sentinel"|"explorer";
export type LocomotionStyle="roll"|"tumble"|"glide"|"dart"|"undulate"|"corkscrew"|"stretch"|"pulse";
export type BattlePose="entrance"|"idle"|"ready"|"move"|"anticipate"|"attack"|"defend"|"impact"|"arsenal"|"stress"|"decline"|"recover"|"victory"|"defeat";

const fallbackShapes:VisualShape[]=["coccus","rod","curved","vibrio","spiral","filament","chain","cluster","spore","capsule","irregular"];
const palettes=[
  ["#ff755f","#ffc15f"],["#7bf2bc","#52b7ff"],["#ad8bff","#ff82bd"],["#d7f171","#75e6a4"],
  ["#ff9f68","#ffe66d"],["#68d8ff","#c9f4ff"],["#f080c0","#ad8bff"],["#9be564","#4dd6a4"],
  ["#ff6f91","#ffb86c"],["#7fd1b9","#d7f171"],["#b8a1ff","#78c6ff"],["#f2c14e","#f78154"],
] as const;
const appendages:VisualAppendage[]=["none","polar","tuft","peritrichous","pili"];
const expressions:VisualExpression[]=["bold","cheery","focused","grumpy","curious"];
const textures:VisualTexture[]=["granular","smooth","banded","speckled","translucent"];
const personalities:VisualPersonality[]=["sprinter","guardian","coordinator","trickster","sentinel","explorer"];
const shapeNames:Record<VisualShape,string>={coccus:"Coccus",rod:"Bacillus",curved:"Curved rod",vibrio:"Vibrio",spiral:"Spiral",filament:"Filamentous",chain:"Cell chain",cluster:"Cell cluster",spore:"Spore former",capsule:"Encapsulated",irregular:"Pleomorphic"};
const personalityNames:Record<VisualPersonality,string>={sprinter:"The Sprinter",guardian:"The Guardian",coordinator:"The Collective",trickster:"The Trickster",sentinel:"The Sentinel",explorer:"The Explorer"};
const locomotionByShape:Record<VisualShape,LocomotionStyle>={
  coccus:"roll",cluster:"tumble",chain:"undulate",rod:"glide",curved:"undulate",
  vibrio:"dart",spiral:"corkscrew",filament:"stretch",spore:"tumble",
  capsule:"glide",irregular:"pulse",
};

export const FIGHTER_ANIMATIONS:Record<BattlePose,{frames:number;frameMs:number;loop:boolean}>={
  entrance:{frames:8,frameMs:70,loop:false},idle:{frames:6,frameMs:150,loop:true},
  ready:{frames:4,frameMs:120,loop:true},move:{frames:8,frameMs:75,loop:true},
  anticipate:{frames:4,frameMs:70,loop:false},attack:{frames:6,frameMs:55,loop:false},
  defend:{frames:4,frameMs:90,loop:false},impact:{frames:4,frameMs:50,loop:false},
  arsenal:{frames:8,frameMs:60,loop:false},stress:{frames:6,frameMs:95,loop:true},
  decline:{frames:4,frameMs:130,loop:false},recover:{frames:5,frameMs:85,loop:false},
  victory:{frames:8,frameMs:90,loop:false},defeat:{frames:6,frameMs:110,loop:false},
};

export function visualHash(value:string){let hash=2166136261;for(let i=0;i<value.length;i++){hash^=value.charCodeAt(i);hash=Math.imul(hash,16777619)}return hash>>>0}

function recordedShape(value?:string):VisualShape|undefined{const shape=(value||"").toLowerCase();if(!shape)return undefined;if(shape.includes("chain")||shape.includes("strepto"))return "chain";if(shape.includes("cluster")||shape.includes("staph"))return "cluster";if(shape.includes("spore"))return "spore";if(shape.includes("capsul"))return "capsule";if(shape.includes("filament")||shape.includes("hyph")||shape.includes("branch"))return "filament";if(shape.includes("spir")||shape.includes("spiro")||shape.includes("helix"))return "spiral";if(shape.includes("vibr")||shape.includes("comma"))return "vibrio";if(shape.includes("curv"))return "curved";if(shape.includes("cocc")||shape.includes("spher"))return "coccus";if(shape.includes("rod")||shape.includes("bacill"))return "rod";return undefined}

export function fighterVisualProfile(fighter:Fighter){
  const hash=visualHash(`${fighter.catalogId}|${fighter.fullName}`);
  const motility=(fighter.motility||"").toLowerCase();
  const shape=recordedShape(fighter.cellShape)??fallbackShapes[hash%fallbackShapes.length];
  const appendage:VisualAppendage=motility.includes("non-motile")||motility.includes("nonmotile")?"pili":motility.includes("motile")?appendages[1+(hash%3)]:appendages[(hash>>>5)%appendages.length];
  const palette=palettes[(hash>>>9)%palettes.length];
  const personality=personalities[(hash>>>21)%personalities.length];
  return {shape,shapeName:shapeNames[shape],appendage,expression:expressions[(hash>>>14)%expressions.length],texture:textures[(hash>>>17)%textures.length],personality,archetype:personalityNames[personality],locomotion:locomotionByShape[shape],primary:palette[0],secondary:palette[1],motion:(hash>>>18)%3,tilt:(hash%17)-8,scaleX:.9+((hash>>>23)%5)*.06,scaleY:.88+((hash>>>26)%5)*.055};
}

export function colonyVisualCount(cfu:number,maxCells:number){
  const normalized=Math.max(0,Math.min(1000,cfu))/1000;
  return Math.max(cfu>0?3:1,Math.round(3+Math.pow(normalized,.72)*(maxCells-3)));
}

export function livingColonyCount(cfu:number,health:number,maxCells:number){
  const full=colonyVisualCount(cfu,maxCells);
  return Math.max(health>0?2:1,Math.round(full*(.18+.82*Math.max(0,Math.min(100,health))/100)));
}

export const duelShapeOrder:VisualShape[]=["rod","coccus","vibrio","spiral","filament","cluster","chain","spore","capsule","curved","irregular"];

export function differentiatedDuelProfiles(player:Fighter,opponent:Fighter){
  const left=fighterVisualProfile(player),base=fighterVisualProfile(opponent);
  if(left.shape!==base.shape&&left.primary!==base.primary)return [left,base] as const;
  const shape=left.shape===base.shape?duelShapeOrder[(duelShapeOrder.indexOf(base.shape)+3)%duelShapeOrder.length]:base.shape;
  const appendage=left.appendage===base.appendage?appendages[(appendages.indexOf(base.appendage)+2)%appendages.length]:base.appendage;
  const expression=left.expression===base.expression?expressions[(expressions.indexOf(base.expression)+2)%expressions.length]:base.expression;
  const palette=palettes[(palettes.findIndex(value=>value[0]===base.primary)+5)%palettes.length];
  return [left,{...base,shape,shapeName:shapeNames[shape],appendage,expression,primary:palette[0],secondary:palette[1],tilt:-base.tilt,scaleX:Math.max(.82,1.9-base.scaleX),scaleY:Math.max(.82,1.86-base.scaleY)}] as const;
}
