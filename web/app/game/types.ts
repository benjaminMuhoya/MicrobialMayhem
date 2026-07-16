export type Environment = "Neutral" | "Salty" | "Alkaline" | "Hot" | "Cold" | "Acidic" | "In the presence of antibiotics";
export type GameMode = "1_player" | "2_players";
export type Winner = "A" | "B" | "tie";

export interface TraitEvidence { trait: string; evidenceLevel: string; field: string; explanation: string }
export interface Fighter {
  catalogId: string; fullName: string; displayName?: string; strain?: string;
  accessions: string[]; products: string[]; activities: string[]; traits: TraitEvidence[];
  description?: string; curiousFact?: string; habitat?: string; colonyAppearance?: string;
  cellShape?: string; motility?: string; provenance?: string;
}
export interface ScoreComponent { name: string; value: number; explanation: string; includedInTotal: boolean }
export interface ScoreBreakdown { fighterName: string; environmentStatus: "MATCHED"|"MISMATCHED"|"UNKNOWN"; colonyCfu: number; total: number; components: ScoreComponent[] }
export interface BattleSetup { mode: GameMode; seed: number; environment: Environment; player: Fighter; opponent: Fighter; playerColonyCfu: number; opponentColonyCfu: number; playerArsenal: boolean; opponentArsenal: boolean }
export interface BattleResult { player: ScoreBreakdown; opponent: ScoreBreakdown; winner: Winner }

