export type QualityTier="low"|"medium"|"high";
export interface DeviceSignals{memory?:number;cores?:number;width:number;reducedMotion:boolean}
export function chooseQualityTier({memory,cores,width,reducedMotion}:DeviceSignals):QualityTier{if(reducedMotion||memory!==undefined&&memory<=2||cores!==undefined&&cores<=2)return"low";if(memory!==undefined&&memory<=4||cores!==undefined&&cores<=4||width<700)return"medium";return"high"}
export const QUALITY_LIMITS={low:{particles:8,colony:7,antialias:false},medium:{particles:16,colony:10,antialias:true},high:{particles:24,colony:14,antialias:true}} as const;
