import type { Environment, Fighter, GameMode } from "./types";
import type { MatchVariant } from "./progression";

export const APP_VERSION="0.5.0";
export type RecoverableScreen="fighter"|"colony"|"arsenal"|"environment"|"preview";
export interface SavedMatchSession{version:1;savedAt:string;screen:RecoverableScreen;mode:GameMode;variant:MatchVariant;player1Id:string|null;player2Id:string|null;activePlayer:1|2;setupPlayer:1|2;player1Cfu:number;player2Cfu:number;player1Arsenal:boolean;player2Arsenal:boolean;environment:Environment;battleSeed:number}
export interface CatalogEnvelope{schemaVersion:number;contentVersion?:string;fighters:Fighter[]}

export function validateCatalog(value:unknown):CatalogEnvelope{
  if(!value||typeof value!=="object")throw new Error("Catalog file is unavailable.");
  const candidate=value as Partial<CatalogEnvelope>;
  if(candidate.schemaVersion!==2||!Array.isArray(candidate.fighters)||candidate.fighters.length<2)throw new Error("Catalog format is not supported.");
  const ids=new Set<string>();
  for(const fighter of candidate.fighters){if(!fighter||typeof fighter.catalogId!=="string"||!fighter.catalogId||typeof fighter.fullName!=="string"||!fighter.fullName)throw new Error("Catalog contains an incomplete fighter.");if(ids.has(fighter.catalogId))throw new Error("Catalog contains duplicate fighters.");ids.add(fighter.catalogId)}
  return candidate as CatalogEnvelope;
}

export function validateSession(value:unknown,catalog:Fighter[]):SavedMatchSession|null{
  if(!value||typeof value!=="object")return null;const session=value as SavedMatchSession;if(session.version!==1||!["fighter","colony","arsenal","environment","preview"].includes(session.screen))return null;
  const ids=new Set(catalog.map(item=>item.catalogId));if(session.player1Id&&!ids.has(session.player1Id)||session.player2Id&&!ids.has(session.player2Id))return null;
  if(!Number.isFinite(session.player1Cfu)||!Number.isFinite(session.player2Cfu)||!Number.isFinite(session.battleSeed))return null;return session;
}
