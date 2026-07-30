import type { BattlePose, VisualShape } from "./visual-profile";

export interface SpriteSheetDefinition{
  src:string;frameWidth:number;frameHeight:number;frames:number;anchor:[number,number];
}
type Manifest=Record<string,Partial<Record<BattlePose,SpriteSheetDefinition>>>;

let manifestPromise:Promise<Manifest>|null=null;
const imageCache=new Map<string,Promise<HTMLImageElement|null>>();

export function loadSpriteManifest(){
  if(typeof window==="undefined")return Promise.resolve({} as Manifest);
  manifestPromise??=fetch("./fighters/manifest.json").then(response=>response.ok?response.json():{}).catch(()=>({})) as Promise<Manifest>;
  return manifestPromise;
}

export async function fighterSpriteSheet(catalogId:string,pose:BattlePose,shape?:VisualShape){
  const manifest=await loadSpriteManifest(),definition=manifest[catalogId]?.[pose]??(shape?manifest[`shape:${shape}`]?.[pose]:undefined);
  if(!definition)return null;
  if(!imageCache.has(definition.src))imageCache.set(definition.src,new Promise(resolve=>{const image=new Image();image.decoding="async";image.onload=()=>resolve(image);image.onerror=()=>resolve(null);image.src=definition.src}));
  return await imageCache.get(definition.src)?definition:null;
}

export function clearSpriteSheetCache(){imageCache.clear();manifestPromise=null}
