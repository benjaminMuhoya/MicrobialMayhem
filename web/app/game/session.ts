import type { BattleResult, BattleSetup, Environment, Fighter, GameMode } from "./types";
import { scoreBattle } from "./scoring";

export type GameScreen = "home"|"fighter"|"colony"|"arsenal"|"environment"|"preview"|"arena"|"results"|"settings";
export interface PlayerSetup { fighter?: Fighter; colonyCfu: number; arsenal?: boolean }
export interface GameSession { mode?: GameMode; screen: GameScreen; activePlayer: 1|2; player1: PlayerSetup; player2: PlayerSetup; environment?: Environment; seed?: number; result?: BattleResult }
export const newSession=():GameSession=>({screen:"home",activePlayer:1,player1:{colonyCfu:100},player2:{colonyCfu:100}});
export function calculateSessionBattle(session:GameSession):GameSession {
  if(!session.mode||!session.player1.fighter||!session.player2.fighter||session.player1.arsenal===undefined||session.player2.arsenal===undefined||!session.environment||session.seed===undefined)throw new Error("Battle setup is incomplete");
  const setup:BattleSetup={mode:session.mode,seed:session.seed,environment:session.environment,player:session.player1.fighter,opponent:session.player2.fighter,playerColonyCfu:session.player1.colonyCfu,opponentColonyCfu:session.player2.colonyCfu,playerArsenal:session.player1.arsenal,opponentArsenal:session.player2.arsenal};
  return {...session,result:scoreBattle(setup),screen:"preview"};
}

