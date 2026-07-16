import { PythonRandom } from "./python-random.ts";
import type { Fighter } from "./types.ts";

export interface RuntimeCatalog { contentVersion: string; schemaVersion: number; fighters: Fighter[] }

export function fighterGenus(fighter: Fighter) {
  return fighter.genus || fighter.fullName.trim().split(/\s+/)[0] || "";
}

export function searchFighters(catalog: Fighter[], query: string) {
  const needle = query.trim().toLocaleLowerCase();
  if (!needle) return [];
  return catalog.filter((fighter) => [
    fighter.fullName, fighter.displayName, fighterGenus(fighter), fighter.strain,
    fighter.catalogId, fighter.searchKey, ...fighter.accessions,
  ].filter(Boolean).join(" ").toLocaleLowerCase().includes(needle));
}

function sameSet(a: Fighter[], b: Fighter[]) {
  return a.length === b.length && new Set(a.map((item) => item.catalogId)).size === b.length && a.every((item) => b.some((other) => other.catalogId === item.catalogId));
}

export function sampleFighters(catalog: Fighter[], count: number, seed: number, previous: Fighter[] = [], locked?: Fighter) {
  const available = catalog.filter((fighter) => fighter.catalogId !== locked?.catalogId);
  if (available.length <= Math.max(0, count - (locked ? 1 : 0))) return locked ? [locked, ...available] : available.slice();
  for (let attempt = 0; attempt < 8; attempt++) {
    const rng = new PythonRandom(seed + attempt);
    const pool = available.slice();
    const chosen: Fighter[] = locked ? [locked] : [];
    while (chosen.length < count && pool.length) chosen.push(pool.splice(Math.floor(rng.random() * pool.length), 1)[0]);
    if (!sameSet(chosen, previous)) return chosen;
  }
  return (locked ? [locked, ...available] : available).slice(0, count);
}

export function chooseCatalogOpponent(catalog: Fighter[], playerId: string, seed: number) {
  const candidates = catalog.filter((fighter) => fighter.catalogId !== playerId);
  if (!candidates.length) throw new Error("No opponent candidates available");
  return candidates[Math.floor(new PythonRandom(seed).random() * candidates.length)];
}

export function generateOpponentCfu(seed: number) {
  return new PythonRandom(seed).randint(0, 1000);
}
