"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { PhaserArena } from "./components/PhaserArena";
import { scoreBattle } from "./game/scoring";
import type { BattleResult, Environment, Fighter, GameMode } from "./game/types";
import { chooseCatalogOpponent, generateOpponentCfu, sampleFighters, searchFighters, type RuntimeCatalog } from "./game/catalog";
import { PythonRandom } from "./game/python-random";
import { fighterVisualProfile } from "./game/visual-profile";
import { DEFAULT_PREFERENCES, normalizePreferences, type GamePreferences } from "./game/preferences";
import { classifyViewport, type ViewportClass } from "./game/viewport";
import { gameFeedback } from "./game/feedback";
import { loadPreference, savePreference } from "./components/PwaRuntime";

type Screen = "home" | "fighter" | "colony" | "arsenal" | "environment" | "preview" | "arena" | "results" | "settings" | "how" | "lab";

const battleFighters: Fighter[] = [
  {catalogId:"fixture:bacillus",fullName:"Bacillus cereus ATCC 14579",strain:"ATCC 14579",accessions:["BGC0000033","BGC0000034","BGC0000035","BGC0000036","BGC0000037"],products:["cereulide"],activities:["cytotoxic","antibacterial"],traits:[{trait:"Thermophile",evidenceLevel:"Direct evidence",field:"genes",explanation:"Resistance and heat-response evidence."}],description:"A documented Bacillus fighter.",cellShape:"rod",motility:"motile"},
  {catalogId:"fixture:psychrobacter",fullName:"Psychrobacter cryonix ICE-2",strain:"ICE-2",accessions:["BGC-COLD-1"],products:["cryoprotectin"],activities:["siderophore"],traits:[{trait:"Cryophile",evidenceLevel:"Direct evidence",field:"organism_name",explanation:"Cold-adaptation evidence."}],description:"A cold-adapted database rival.",cellShape:"coccus",motility:"non-motile"},
];

function Microbe({ tone = "mint", compact = false, fighter, shape }: { tone?: string; compact?: boolean; fighter?:Fighter; shape?:string }) {
  const profile=fighter?fighterVisualProfile(fighter):{shape:shape||"irregular",appendage:shape==="coccus"?"pili":"polar",expression:"cheery",primary:tone==="coral"?"#ff755f":tone==="violet"?"#ad8bff":"#7bf2bc",secondary:tone==="coral"?"#ffc15f":tone==="violet"?"#ff82bd":"#52b7ff",motion:0,tilt:-6};
  return (
    <div className={`microbe microbe--${profile.shape} appendage--${profile.appendage} expression--${profile.expression} texture--${"texture" in profile?profile.texture:"smooth"} personality--${"personality" in profile?profile.personality:"explorer"} motion--${profile.motion} ${compact ? "microbe--compact" : ""}`} style={{"--c":profile.primary,"--c2":profile.secondary,"--tilt":`${profile.tilt}deg`,"--sx":"scaleX" in profile?profile.scaleX:1,"--sy":"scaleY" in profile?profile.scaleY:1} as React.CSSProperties} aria-hidden="true">
      <span className="microbe__membrane" />
      <span className="microbe__core" />
      <span className="microbe__spark microbe__spark--one" />
      <span className="microbe__spark microbe__spark--two" />
      <span className="microbe__tail" />
      <span className="microbe__pili" />
      <span className="microbe__capsule" />
      <span className="microbe__face"><i/><i/><b/></span>
      <span className="microbe__satellites"><i/><i/><i/></span>
    </div>
  );
}

function AppHeader({ screen, goBack, setScreen }: { screen: Screen; goBack: () => void; setScreen: (screen: Screen) => void }) {
  return (
    <header className="app-header game-hud">
      {screen!=="home"?<button className="hud-back" onClick={goBack} aria-label="Go back"><span>←</span><b>Back</b></button>:<span className="hud-spacer"/>}
      <button className="brand" onClick={() => setScreen("home")} aria-label="Microbial Mayhem home">
        <span className="brand__mark"><span /></span>
        <span><b>Microbial</b><em>Mayhem</em></span>
      </button>
      <button className="icon-button" onClick={()=>setScreen("settings")} aria-label="Open settings"><span className="gear">✦</span></button>
    </header>
  );
}

function Home({ start, mode, setMode, open, introSeen, skipIntro, ready }: { start: () => void; mode: GameMode; setMode:(mode:GameMode)=>void;open:(screen:Screen)=>void;introSeen:boolean;skipIntro:()=>void;ready:boolean }) {
  return (
    <section className={`scene home-scene ${introSeen?"intro-complete":"intro-playing"}`} data-testid="screen-home">
      {!introSeen&&<button className="skip-intro" onClick={skipIntro}>Skip intro</button>}
      <div className="home-copy">
        <h1><small>A MICROSCOPIC BATTLE TO SURVIVE</small>Microscopic Gladiators<br/><span>Meet in the Petri Dish</span></h1>
        <p className="lede">Build a living colony, choose the arena, and discover which bacterium is biologically prepared to thrive.</p>
        <div className="mode-picker" aria-label="Choose game mode">
          <button className={`mode-card ${mode==="1_player"?"is-selected":""}`} onClick={()=>{gameFeedback.cue("select");setMode("1_player")}}><span>01</span><b>One player</b><small>Face a database rival</small></button>
          <button className={`mode-card ${mode==="2_players"?"is-selected":""}`} onClick={()=>{gameFeedback.cue("select");setMode("2_players")}}><span>02</span><b>Two players</b><small>Pass-and-play locally</small></button>
        </div>
        <button className="primary-action" disabled={!ready} aria-busy={!ready} onClick={start}>{ready?"Enter the culture":"Preparing cultures"} <span>{ready?"→":"…"}</span></button>
        <nav className="home-utilities" aria-label="Explore Microbial Mayhem"><button onClick={()=>open("lab")}><span>◉</span><b>Microbe Lab</b><small>Explore all 384 fighters</small></button><button onClick={()=>open("how")}><span>?</span><b>How to Play</b><small>Learn through one quick match</small></button><button onClick={()=>open("settings")}><span>✦</span><b>Settings</b><small>Sound, motion and comfort</small></button></nav>
      </div>
      <div className="hero-dish" aria-label="Animated microscopic bacterial colony">
        <div className="microscope-focus" /><div className="dish-orbit dish-orbit--one" /><div className="dish-orbit dish-orbit--two" />
        <div className="intro-colony intro-colony--left">{Array.from({length:12},(_,i)=><i key={i}/>)}</div><div className="intro-colony intro-colony--right">{Array.from({length:12},(_,i)=><i key={i}/>)}</div>
        <div className="intro-fighter intro-fighter--left"><Microbe tone="coral" shape="rod" /></div><div className="intro-fighter intro-fighter--right"><Microbe tone="mint" shape="coccus" compact /></div>
        <div className="specimen-tag"><span>LIVE SPECIMEN</span><b>Culture #MM-042</b></div>
      </div>
    </section>
  );
}

function SettingsScreen({ preferences, update, replayIntro }: {preferences:GamePreferences;update:(patch:Partial<GamePreferences>)=>void;replayIntro:()=>void}) {
  return <section className="scene native-panel-scene" data-testid="screen-settings"><div className="screen-heading"><div><p className="eyebrow">Culture controls</p><h2>Settings</h2></div><p>Shape the experience without changing the biology.</p></div><div className="settings-grid"><label><span><b>Music</b><small>Microscopic ambience and battle themes</small></span><input aria-label="Music volume" type="range" min="0" max="1" step="0.05" value={preferences.musicVolume} onChange={event=>update({musicVolume:Number(event.target.value)})}/></label><label><span><b>Sound effects</b><small>Interface, character and arena cues</small></span><input aria-label="Sound effects volume" type="range" min="0" max="1" step="0.05" value={preferences.effectsVolume} onChange={event=>update({effectsVolume:Number(event.target.value)})}/></label>{[["Captions","Show visual equivalents for important sounds","captions"],["Reduced motion","Calmer transitions and fewer particles","reducedMotion"],["Haptics","Light touch feedback on supported devices","haptics"]].map(([title,copy,key])=><button key={key} role="switch" aria-checked={preferences[key as keyof GamePreferences] as boolean} onClick={()=>update({[key]:!preferences[key as keyof GamePreferences]} as Partial<GamePreferences>)}><span><b>{title}</b><small>{copy}</small></span><i>{preferences[key as keyof GamePreferences]?"On":"Off"}</i></button>)}</div><button className="quiet-action replay-intro" onClick={replayIntro}>Replay opening sequence</button></section>
}

function HowToPlay() { return <section className="scene native-panel-scene" data-testid="screen-how"><div className="screen-heading"><div><p className="eyebrow">First culture</p><h2>How to Play</h2></div><p>Experiment first. The science reveals itself as you play.</p></div><div className="tutorial-path">{[["1","Choose a fighter","Tap a bacterium to preview its morphology and recorded strengths."],["2","Grow the colony","Choose how many colony-forming units enter the dish."],["3","Prepare and adapt","Decide whether to activate documented chemistry, then choose an environment."],["4","Watch the battle","The arena brings the biologically determined matchup to life."],["5","Discover why","Open the scientific breakdown to see the decisive evidence."]].map(([n,title,copy])=><article key={n}><span>{n}</span><div><h3>{title}</h3><p>{copy}</p></div></article>)}</div></section> }

function MicrobeLab({fighters,onChoose}:{fighters:Fighter[];onChoose:(fighter:Fighter)=>void}) { const genera=useMemo(()=>Array.from(new Set(fighters.map(f=>f.genus||f.fullName.split(" ")[0]))).sort(),[fighters]); const [genus,setGenus]=useState<string|null>(null); const shown=genus?fighters.filter(f=>(f.genus||f.fullName.split(" ")[0])===genus):fighters.slice(0,18); return <section className="scene native-panel-scene lab-scene" data-testid="screen-lab"><div className="screen-heading"><div><p className="eyebrow">Discovered cultures</p><h2>Microbe Lab</h2></div><p>Browse the roster by genus, then inspect a living specimen.</p></div><div className="lab-browser"><aside><button className={!genus?"is-selected":""} onClick={()=>setGenus(null)}>Highlights <small>{fighters.length} fighters</small></button>{genera.slice(0,40).map(item=><button key={item} className={genus===item?"is-selected":""} onClick={()=>setGenus(item)}><i>{item}</i><small>{fighters.filter(f=>(f.genus||f.fullName.split(" ")[0])===item).length} specimen(s)</small></button>)}</aside><div className="lab-roster">{shown.slice(0,24).map(fighter=><button key={fighter.catalogId} onClick={()=>onChoose(fighter)}><Microbe fighter={fighter}/><span><i>{fighter.fullName}</i><small>{fighter.cellShape} · {fighter.motility}</small></span></button>)}</div></div></section> }

function FighterScreen({ fighters, roster, selected, locked, activePlayer, loading, onSelect, onConfirm, onShuffle, onResetRoster }: { fighters:Fighter[]; roster:Fighter[]; selected:Fighter|null; locked:Fighter|null; activePlayer:1|2; loading:boolean; onSelect:(fighter:Fighter)=>void; onConfirm:()=>void; onShuffle:()=>void; onResetRoster:()=>void }) {
  const [query,setQuery]=useState(""); const [details,setDetails]=useState(false); const [genus,setGenus]=useState("All"); const [morphology,setMorphology]=useState("All"); const [compareMode,setCompareMode]=useState(false); const [comparison,setComparison]=useState<Fighter|null>(null); const [quickFact,setQuickFact]=useState<Fighter|null>(null); const holdTimer=useRef<ReturnType<typeof setTimeout>|null>(null); const suppressClick=useRef(false);
  const matches=useMemo(()=>searchFighters(fighters,query),[fighters,query]); const source=query.trim()?matches:roster; const genera=useMemo(()=>Array.from(new Set(roster.map(item=>item.genus||item.fullName.split(" ")[0]))).sort().slice(0,8),[roster]); const shown=source.filter(item=>(genus==="All"||(item.genus||item.fullName.split(" ")[0])===genus)&&(morphology==="All"||(item.cellShape||"").toLowerCase().includes(morphology.toLowerCase())));
  const fighter=selected;
  const choose=(item:Fighter)=>{if(suppressClick.current){suppressClick.current=false;return}if(compareMode&&fighter?.catalogId!==item.catalogId){setComparison(item);gameFeedback.cue("select");return}if(fighter?.catalogId===item.catalogId){gameFeedback.cue("select","medium");onConfirm();return}gameFeedback.cue("select");onSelect(item)};
  const beginFact=(item:Fighter)=>{suppressClick.current=false;if(holdTimer.current)clearTimeout(holdTimer.current);holdTimer.current=setTimeout(()=>{suppressClick.current=true;setQuickFact(item);gameFeedback.haptic("medium")},520)}; const endFact=()=>{if(holdTimer.current)clearTimeout(holdTimer.current);holdTimer.current=null};
  useEffect(()=>{if(!details)return;const close=(event:KeyboardEvent)=>{if(event.key==="Escape")setDetails(false)};window.addEventListener("keydown",close);return()=>window.removeEventListener("keydown",close)},[details]);
  return (
    <section className="scene explorer" data-testid="screen-fighter">
      <div className="screen-heading"><div><p className="eyebrow">Player {activePlayer} · specimen selection</p><h2>{activePlayer===2?"Choose a different rival":"Choose your organism"}</h2></div><p>Recorded biology drives the battle.<br/>Procedural styling gives it personality.</p></div>
      {activePlayer===2&&locked&&<aside className="locked-player" aria-label={`Player 1 selected ${locked.fullName}`}><span>Player 1 locked</span><Microbe fighter={locked} compact/><b><i>{locked.fullName}</i></b><small>{locked.cellShape} · {locked.motility}</small></aside>}
      <div className="explorer-grid">
        <aside className="roster-panel">
          <label className="search"><span>⌕</span><input aria-label="Search bacterial fighters" value={query} onChange={event=>setQuery(event.target.value)} placeholder="Search genus, species, strain, ID" /></label>
          <div className="taxonomy-filters" aria-label="Taxonomy filters"><button className={genus==="All"?"is-selected":""} onClick={()=>setGenus("All")}>All genera</button>{genera.map(item=><button key={item} className={genus===item?"is-selected":""} onClick={()=>setGenus(item)}><i>{item}</i></button>)}</div><div className="morphology-filters" aria-label="Morphology filters">{["All","coccus","rod","spiral","chain","cluster"].map(item=><button key={item} className={morphology===item?"is-selected":""} onClick={()=>setMorphology(item)}>{item==="All"?"All shapes":item}</button>)}</div>
          <p className="search-status" role="status">{loading?"Loading production catalog…":query.trim()?matches.length?`Found ${matches.length} match(es) for '${query}'.`:`The database went quiet on '${query}'. Try another genus, species, or strain.`:`Showing ${roster.length} random database-derived bacteria.`}</p>
          <div className="roster-list">
            {shown.slice(0,30).map((item) => {const unavailable=activePlayer===2&&locked?.catalogId===item.catalogId; return <button key={item.catalogId} disabled={unavailable} aria-disabled={unavailable} aria-pressed={selected?.catalogId===item.catalogId} onPointerDown={()=>beginFact(item)} onPointerUp={endFact} onPointerCancel={endFact} onContextMenu={event=>{event.preventDefault();setQuickFact(item)}} onClick={() => choose(item)} className={selected?.catalogId===item.catalogId?"is-selected":comparison?.catalogId===item.catalogId?"is-comparing":unavailable?"is-locked":""}>
              <Microbe fighter={item} compact /><span><i>{item.fullName}</i><small>{item.strain||"Strain not recorded"} · {item.accessions.length} BGCs{unavailable?" · Player 1 locked":""}</small></span><b>{unavailable?"Locked":selected?.catalogId===item.catalogId?"Tap again to select":compareMode?"Compare":"Preview"}</b>
            </button>})}
          </div>
          {query.trim()?<button className="quiet-action" onClick={()=>{setQuery("");onResetRoster()}}>Reset to random roster</button>:<button className="quiet-action" onClick={onShuffle}>Show different bacteria</button>}
        </aside>
        {fighter?<article className="fighter-focus is-previewed">{(()=>{const visual=fighterVisualProfile(fighter);return <>
          <div className="fighter-stage"><div className="focus-ring"/><Microbe fighter={fighter}/><span className={`recorded-pill ${fighter.traits.length||fighter.accessions.length?"has-evidence":"limited-evidence"}`}>{fighter.traits.length||fighter.accessions.length?"Detailed biological data":"Limited biological data"}</span></div>
          <div className="fighter-info"><p className="eyebrow">Fighter preview</p><h3><i>{fighter.fullName}</i></h3><p className="strain">strain {fighter.strain||"not recorded"}</p>
            <div className="fighter-identity"><span>{visual.archetype}</span><b>{visual.shapeName}</b><small>{visual.texture} surface · {visual.appendage} appendages</small></div>
            <div className="fact-row"><span><small>Morphology</small><b>{fighter.cellShape||"Not recorded"} · {fighter.motility||"motility not recorded"}</b></span><span><small>Habitat</small><b>{fighter.habitat||"Not recorded"}</b></span><span><small>Known BGCs</small><b>{fighter.accessions.length} documented</b></span></div>
            <div className="strength-chips" aria-label="Recorded strengths">{fighter.traits.slice(0,3).map(trait=><span key={trait.trait}>{trait.trait}</span>)}{!fighter.traits.length&&<span>Biology still being documented</span>}</div>
            <div className="ability"><span className="ability__icon">✦</span><span><small>Signature chemistry</small><b>Documented biosynthetic activity</b></span><button onClick={()=>setDetails(true)}>Biology details</button></div>
            <div className="fighter-actions"><button className="compare-action" aria-pressed={compareMode} onClick={()=>{setCompareMode(value=>!value);setComparison(null)}}>{compareMode?"Cancel comparison":"Compare fighter"}</button><button className="primary-action" onClick={()=>{gameFeedback.cue("select","strong");onConfirm()}}>Select Player {activePlayer} fighter <span>→</span></button></div>
          </div></>})()}
        </article>:<article className="fighter-focus empty-focus"><p>Select a bacterium to inspect its recorded biology.</p></article>}
      </div>
      {compareMode&&fighter&&<aside className="compare-tray" aria-live="polite"><article><Microbe fighter={fighter} compact/><span><small>Previewed fighter</small><b><i>{fighter.fullName}</i></b><em>{fighter.cellShape}</em></span></article><strong>VS</strong>{comparison?<article><Microbe fighter={comparison} compact/><span><small>Comparison fighter</small><b><i>{comparison.fullName}</i></b><em>{comparison.cellShape}</em></span></article>:<p>Tap another fighter card to compare without losing this preview.</p>}</aside>}
      {quickFact&&<div className="quick-fact" role="dialog" aria-modal="true" aria-label={`Quick fact about ${quickFact.fullName}`} onClick={()=>setQuickFact(null)}><div><Microbe fighter={quickFact} compact/><p className="eyebrow">Press-and-hold discovery</p><h3><i>{quickFact.fullName}</i></h3><p>{quickFact.curiousFact||quickFact.description||quickFact.traits[0]?.explanation||"The available biological evidence is limited—another reason microbial research matters."}</p><button autoFocus onClick={()=>setQuickFact(null)}>Return to fighters</button></div></div>}
      {details&&fighter&&<div className="modal-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)setDetails(false)}}><section className="biology-modal" role="dialog" aria-modal="true" aria-labelledby="biology-title"><button className="modal-close" autoFocus onClick={()=>setDetails(false)} aria-label="Close biology details">×</button><p className="eyebrow">Recorded biological evidence</p><h2 id="biology-title"><i>{fighter.fullName}</i></h2><p>Strain {fighter.strain||"not recorded"}</p><div className="biology-grid"><span><small>Morphology</small><b>{fighter.cellShape||"Not recorded"}; {fighter.motility||"motility not recorded"}</b></span><span><small>Habitat</small><b>{fighter.habitat||"Not recorded"}</b></span><span><small>Colony appearance</small><b>{fighter.colonyAppearance||"Not recorded"}</b></span><span><small>Provenance</small><b>{typeof fighter.provenance==="string"?fighter.provenance:String((fighter.provenance as Record<string,unknown>)?.source||"Production catalog")}</b></span></div><h3>Documented BGC accessions</h3><p>{fighter.accessions.length?fighter.accessions.join(", "):"No documented MIBiG BGC is available. The game will not imply an arsenal."}</p><h3>Products and activities</h3><p>{fighter.products.length?fighter.products.join(", "):"Products not recorded"} · {fighter.activities.length?fighter.activities.join(", "):"activities not recorded"}</p><h3>Trait evidence</h3>{fighter.traits.length?<ul>{fighter.traits.map((trait,index)=><li key={`${trait.trait}-${index}`}><b>{trait.trait}</b> — {trait.evidenceLevel}: {trait.explanation}</li>)}</ul>:<p>No compact trait evidence is available. That is why we need more research.</p>}<h3>Biological note</h3><p>{fighter.description||fighter.curiousFact||"The biological explanation is still hiding under the microscope. That is why we need more research."}</p><aside><b>Visual honesty</b><p>Morphology above is recorded when available. Color, glow, personality and combat motion are deterministic procedural styling—not claimed biological observations.</p></aside></section></div>}
    </section>
  );
}

function Colony({ onConfirm, cfu, setCfu, mode, setupPlayer, fighter }: { onConfirm: () => void; cfu:number; setCfu:(cfu:number)=>void; mode:GameMode; setupPlayer:1|2; fighter:Fighter }) {
  const [visualCfu,setVisualCfu]=useState(cfu); const visualRef=useRef(cfu); const profile=fighterVisualProfile(fighter);
  useEffect(()=>{let frame=0;const animate=()=>{const current=visualRef.current,next=current+(cfu-current)*.14;visualRef.current=Math.abs(next-cfu)<1?cfu:next;setVisualCfu(Math.round(visualRef.current));if(visualRef.current!==cfu)frame=requestAnimationFrame(animate)};frame=requestAnimationFrame(animate);return()=>cancelAnimationFrame(frame)},[cfu]);
  const cells = Math.max(7, Math.round(visualCfu / 35));
  const stage=cfu<250?"Small culture":cfu<700?"Established culture":"Dense culture";
  const consequence=cfu<250?"Quick to mobilize, with fewer cells contributing.":cfu<700?"A balanced population with a meaningful numbers advantage.":"A large population, though additional cells bring diminishing returns.";
  const chooseStage=(value:number)=>{gameFeedback.cue("select",value>=900?"strong":"medium");setCfu(value)};
  return <section className={`scene colony-scene colony-player-${setupPlayer}`} data-testid="screen-colony">
    <div className="screen-heading"><div><p className="eyebrow">{mode==="2_players"?`Player ${setupPlayer} · `:""}colony preparation</p><h2>Grow your numbers</h2></div><p>More cells add strength with diminishing returns.</p></div>
    <div className="colony-layout">
      <div className={`culture-dish culture-shape-${profile.shape}`} style={{"--energy": `${visualCfu / 1000}`,"--colony-primary":profile.primary,"--colony-secondary":profile.secondary} as React.CSSProperties}>
        <div className="culture-dish__well">
          <div className="agar-depth"/>{Array.from({ length: cells }).map((_, i) => <i key={i} style={{"--i": i, "--angle": `${(i * 137.5) % 360}deg`, "--radius": `${20 + (i * 17) % 38}%`,"--delay":`${-(i%9)*.19}s`} as React.CSSProperties}><span/></i>) }
        </div><span className="dish-label"><i>{fighter.fullName}</i> · live density preview</span>
      </div>
      <div className="colony-controls"><p className="eyebrow">Player {setupPlayer} culture · colony size</p><div className="cfu-readout"><b>{visualCfu.toLocaleString()}</b><span>CFU</span></div><p className="colony-name">{stage}</p>
        <div className="colony-stages" aria-label="Colony growth stages">{[["Small",150],["Medium",500],["Large",900]].map(([label,value])=><button key={label} className={cfu===value?"is-selected":""} aria-pressed={cfu===value} onClick={()=>chooseStage(Number(value))}><b>{label}</b><small>{value} CFU</small></button>)}</div>
        <input aria-label="Colony forming units" type="range" min="0" max="1000" step="10" value={cfu} onChange={(event) => setCfu(Number(event.target.value))}/>
        <div className="range-labels"><span>0</span><span>1,000</span></div>
        <div className="colony-consequence"><span aria-hidden="true">◌</span><p><b>{stage}</b><small>{consequence}</small></p></div>
        <button className="primary-action" onClick={onConfirm}>Lock Player {setupPlayer} colony <span>→</span></button>
      </div>
    </div>
  </section>;
}

function Arsenal({onConfirm,active,setActive,fighter,mode,setupPlayer}:{onConfirm:()=>void;active:boolean;setActive:(value:boolean)=>void;fighter:Fighter;mode:GameMode;setupPlayer:1|2}){
  const documented=fighter.accessions.length>0; return <section className="scene prep-scene" data-testid="screen-arsenal"><div className="screen-heading"><div><p className="eyebrow">{mode==="2_players"?`Player ${setupPlayer} · `:""}biosynthetic preparation</p><h2>{documented?"Activate documented chemistry?":"No documented arsenal available"}</h2></div><p>{fighter.accessions.length} MIBiG record(s) are available for this fighter.</p></div><div className="gene-stage"><Microbe fighter={fighter}/><div className={`gene-chain ${active&&documented?"is-active":""}`}>{fighter.accessions.slice(0,5).map((id,i)=><i key={id}>{id||`BGC ${i+1}`}</i>)}</div></div><div className="prep-controls"><p><b>{active&&documented?"Arsenal activated":"Arsenal dormant"}</b><span>{active&&documented?"Documented clusters contribute up to +5 offense points.":documented?"Known activity remains documented, but BGC accessions add no arsenal points.":"No documented BGC is available, so the game does not imply an arsenal."}</span></p><div className="binary-choice"><button disabled={!documented} className={active&&documented?"is-selected":""} onClick={()=>setActive(true)}>Activate</button><button className={!active||!documented?"is-selected":""} onClick={()=>setActive(false)}>Keep dormant</button></div><button className="primary-action" onClick={onConfirm}>Confirm Player {setupPlayer} preparation <span>→</span></button></div></section>
}

const environments:Environment[]=["Neutral","Salty","Alkaline","Hot","Cold","Acidic","In the presence of antibiotics"];
const environmentPresentation:Record<Environment,{title:string;icon:string;tagline:string}>={
  Neutral:{title:"Neutral",icon:"◌",tagline:"Balanced agar with no added environmental pressure"},Salty:{title:"Salty",icon:"◇",tagline:"Crystallizing minerals draw moisture from the culture"},Alkaline:{title:"Alkaline",icon:"⬡",tagline:"High-pH mineral patterns spread across the agar"},Hot:{title:"Heat",icon:"⌁",tagline:"Thermal shimmer and drying agar test heat tolerance"},Cold:{title:"Cold",icon:"❄",tagline:"Frost and ice crystals slow the living culture"},Acidic:{title:"Acid",icon:"◉",tagline:"Reactive droplets create strong acidic pressure"},"In the presence of antibiotics":{title:"Antibiotics",icon:"✚",tagline:"Chemical pulses challenge documented resistance"},
};
/* eslint-disable jsx-a11y/role-supports-aria-props -- native pressed state complements listbox selection for touch assistive technology */
function EnvironmentScreen({go,value,setValue,mode,previewFor}:{go:(screen:Screen)=>void;value:Environment;setValue:(value:Environment)=>void;mode:GameMode;previewFor:(environment:Environment)=>BattleResult}){
 const modifier=(env:Environment,side:"player"|"opponent")=>previewFor(env)[side].components.find(c=>c.name==="Environment")?.value||0; const selected=previewFor(value),presentation=environmentPresentation[value];
 const selectEnvironment=(env:Environment)=>{gameFeedback.cue(env==="In the presence of antibiotics"?"ability":"clash","medium");setValue(env)};
 return <section className={`scene environment-scene env-${value.replaceAll(" ","-").toLowerCase()}`} data-testid="screen-environment"><div className="environment-preview" aria-hidden="true"><div className="preview-dish"><span className="preview-icon">{presentation.icon}</span><i/><i/><i/><i/><i/></div><div className="preview-condition"><small>Live habitat preview</small><b>{presentation.title}</b><span>{presentation.tagline}</span></div></div><div className="screen-heading"><div><p className="eyebrow">Shared arena · habitat pressure</p><h2>Choose the living arena</h2></div><p>Tap the habitat itself to preview and select it.</p></div><div className="environment-grid" role="listbox" aria-label="Living arena environments">{environments.map(env=>{const p=modifier(env,"player"),o=modifier(env,"opponent"),meta=environmentPresentation[env];return <button key={env} role="option" aria-selected={value===env} aria-pressed={value===env} onClick={()=>selectEnvironment(env)} className={`${value===env?"is-selected":""} motif-${env.replaceAll(" ","-").toLowerCase()}`}><span className="environment-card-icon" aria-hidden="true">{meta.icon}</span><i/><b>{meta.title}</b><em>{meta.tagline}</em><small>Player 1 {p>=0?"+":""}{p} · {mode==="2_players"?"Player 2":"Rival"} {o>=0?"+":""}{o}</small><span className="selected-check">Selected</span></button>})}</div><div className="environment-confirm"><p><span>Selected habitat</span><b>{presentation.title}</b><small>{selected.player.components.find(c=>c.name==="Environment")?.explanation} {mode==="2_players"?"Player 2":"Automated Rival"}: {selected.opponent.components.find(c=>c.name==="Environment")?.explanation}</small></p><button className="primary-action" onClick={()=>go("preview")}>Enter this habitat <span>→</span></button></div></section>
}
/* eslint-enable jsx-a11y/role-supports-aria-props */

function Preview({ go, mode, player, opponent, playerCfu, opponentCfu, playerArsenal, opponentArsenal, environment, result }: { go:(screen:Screen)=>void; mode:GameMode; player:Fighter; opponent:Fighter; playerCfu:number; opponentCfu:number; playerArsenal:boolean; opponentArsenal:boolean; environment:Environment; result:BattleResult }) {
  const pEnv=result.player.components.find(c=>c.name==="Environment")?.value||0; const oEnv=result.opponent.components.find(c=>c.name==="Environment")?.value||0;
  return <section className="scene preview-scene" data-testid="screen-preview"><div className="arena-aura"/>
    <div className="screen-heading centered"><p className="eyebrow">{environment}</p><h2>Ready to culture chaos?</h2><p>Actual environment modifiers: Player 1 <b>{pEnv>=0?"+":""}{pEnv}</b> · {mode==="2_players"?"Player 2":"Automated Rival"} <b>{oEnv>=0?"+":""}{oEnv}</b>.</p></div>
    <div className="versus"><article><span className="player-label">{mode==="2_players"?"Player 1":"You"}</span><Microbe fighter={player}/><h3><i>{player.fullName}</i></h3><dl><div><dt>Colony</dt><dd>{playerCfu} CFU</dd></div><div><dt>Arsenal</dt><dd className={playerArsenal?"active":""}>{playerArsenal?"Activated":"Dormant"}</dd></div></dl></article><span className="versus-mark">VS</span><article><span className="player-label">{mode==="2_players"?"Player 2":"Automated Rival"}</span><Microbe fighter={opponent}/><h3><i>{opponent.fullName}</i></h3><dl><div><dt>Colony</dt><dd>{opponentCfu} CFU</dd></div><div><dt>Arsenal</dt><dd className={opponentArsenal?"active":""}>{opponentArsenal?"Activated":"Dormant"}</dd></div></dl></article></div>
    <button className="primary-action centered-action" onClick={() => go("arena")}>Enter the microscopic arena <span>→</span></button>
  </section>;
}

function Arena({ go, mode, player, opponent, environment, result, seed, reducedMotion }: { go:(screen:Screen)=>void;mode:GameMode;player:Fighter;opponent:Fighter;environment:Environment;result:BattleResult;seed:number;reducedMotion:boolean }) {
  const [paused,setPaused]=useState(false); return <section className="scene arena-scene" data-testid="screen-arena"><div className="heat-haze"/><div className="arena-top"><div><small>{mode==="2_players"?"Player 1":"You"} · <i>{player.fullName}</i></small><span><b style={{width:"64%"}}/></span></div><p>{environment.toUpperCase()}</p><div><small>{mode==="2_players"?"Player 2":"Automated Rival"} · <i>{opponent.fullName}</i></small><span><b style={{width:"64%"}}/></span></div></div>
    <button className="pause-button" onClick={()=>setPaused(true)} aria-label="Pause battle">Ⅱ</button><PhaserArena paused={paused} reducedMotion={reducedMotion} environment={environment} player={player} opponent={opponent} result={result} seed={seed} onComplete={()=>go("results")} onCue={kind=>{if(kind==="attack"||kind==="counter")gameFeedback.cue("attack");else if(kind==="playerAbility"||kind==="opponentAbility")gameFeedback.cue("ability","medium");else if(kind==="finish")gameFeedback.cue("final_hit","strong");else if(kind==="environment")gameFeedback.cue("clash")}}/>
    {paused&&<div className="pause-overlay" role="dialog" aria-modal="true" aria-label="Battle paused"><div><p className="eyebrow">Culture suspended</p><h2>Battle paused</h2><button className="primary-action" onClick={()=>setPaused(false)}>Resume culture <span>▶</span></button><button onClick={()=>go("home")}>Return to main menu</button></div></div>}
    <div className="battle-caption"><button onClick={() => go("results")}>Skip battle →</button></div>
  </section>;
}

function Results({ result, mode, player, opponent, environment, onRematch, onChangeFighters, onMainMenu }: { result:BattleResult;mode:GameMode;player:Fighter;opponent:Fighter;environment:Environment;onRematch:()=>void;onChangeFighters:()=>void;onMainMenu:()=>void }) {
  const [expanded, setExpanded] = useState(false);
  const playerWon=result.winner==="A", tie=result.winner==="tie"; const winner=playerWon?player:opponent; const missing=!winner.products.length||!winner.activities.length||!winner.curiousFact; const headline=mode==="2_players"?(tie?"TIE!":playerWon?"PLAYER 1 WINS!":"PLAYER 2 WINS!"):(tie?"TIE!":playerWon?"VICTORY!":"DEFEAT!"); return <section className="scene results-scene" data-testid="screen-results"><div className="result-orbit"><Microbe fighter={winner}/></div><p className="eyebrow">Culture resolved</p><h2>{headline}</h2><h3>{tie?"Evenly matched!":<><i>{winner.fullName}</i> wins</>}</h3><p className="result-lede">{tie?"That was a good fight! The microbes were tied.":Math.abs(result.player.total-result.opponent.total)>=10?"A commanding culture! The winner adapted, grew and brought the stronger biological toolkit.":"A close culture clash—small biological advantages decided the arena."}</p>
    <div className="score-pair"><div><small>{mode==="2_players"?"Player 1":"You"}</small><b>{result.player.total.toFixed(1)}</b></div><span>{(result.player.total-result.opponent.total)>=0?"+":""}{(result.player.total-result.opponent.total).toFixed(1)}</span><div><small>{mode==="2_players"?"Player 2":"Automated Rival"}</small><b>{result.opponent.total.toFixed(1)}</b></div></div>
    <button className="science-toggle" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>Scientific breakdown <span>{expanded ? "−" : "+"}</span></button>
    {expanded && <div className="full-breakdown"><div className="score-columns">{[[mode==="2_players"?"Player 1":"You",result.player],[mode==="2_players"?"Player 2":"Automated Rival",result.opponent]].map(([label,data])=><article key={String(label)}><h4>{String(label)} · {(data as typeof result.player).fighterName}</h4>{(data as typeof result.player).components.filter(c=>c.name!=="Base").map(c=><span key={c.name}><b>{c.value>=0?"+":""}{c.value.toFixed(1)}</b><em>{c.name}</em><small>{c.explanation}</small></span>)}</article>)}</div><aside><b>Biological interpretation</b><p>{tie?"Neither culture established a scoring advantage under the documented evidence and shared arena rules.":`${winner.fullName} brought ${winner.accessions.length} known BGC(s). ${environment} pressure, colony size and documented activity produced the decisive component difference.`} {missing?"Some biological details remain unresolved. That is why we need more research.":winner.curiousFact}</p></aside></div>}
    <div className="result-actions"><button className="primary-action" onClick={onRematch}>Rematch <span>↻</span></button><button onClick={onChangeFighters}>Change fighters</button><button onClick={onMainMenu}>Main menu</button></div>
  </section>;
}

export default function HomePage() {
  const [screen, setScreen] = useState<Screen>("home");
  const [,setHistory]=useState<Screen[]>([]); const [preferences,setPreferences]=useState<GamePreferences>(DEFAULT_PREFERENCES); const [viewport,setViewport]=useState<ViewportClass>("desktop");
  const [mode,setMode]=useState<GameMode>("1_player"); const [environment,setEnvironment]=useState<Environment>("Neutral");
  const [catalog,setCatalog]=useState<Fighter[]>([]); const [roster,setRoster]=useState<Fighter[]>([]); const [selected,setSelected]=useState<Fighter|null>(null); const [player1,setPlayer1]=useState<Fighter|null>(null); const [player2,setPlayer2]=useState<Fighter|null>(null); const [activePlayer,setActivePlayer]=useState<1|2>(1); const [setupPlayer,setSetupPlayer]=useState<1|2>(1); const [rosterSeed,setRosterSeed]=useState(41); const [catalogLoading,setCatalogLoading]=useState(true); const [battleSeed,setBattleSeed]=useState(17);
  const [player1Cfu,setPlayer1Cfu]=useState(100); const [player2Cfu,setPlayer2Cfu]=useState(100); const [player1Arsenal,setPlayer1Arsenal]=useState(false); const [player2Arsenal,setPlayer2Arsenal]=useState(false);
  useEffect(()=>{loadPreference<Partial<GamePreferences>>("game-preferences").then(value=>setPreferences(normalizePreferences(value))).catch(()=>undefined)},[]);
  useEffect(()=>{gameFeedback.configure(preferences)},[preferences]);
  useEffect(()=>{void gameFeedback.startPhase(screen==="arena"?"battle":screen==="results"?"results":"setup")},[screen]);
  useEffect(()=>{const visibility=()=>document.hidden?gameFeedback.suspend():gameFeedback.resume();document.addEventListener("visibilitychange",visibility);return()=>document.removeEventListener("visibilitychange",visibility)},[]);
  useEffect(()=>{const update=()=>setViewport(classifyViewport(window.innerWidth,window.innerHeight));update();window.addEventListener("resize",update);return()=>window.removeEventListener("resize",update)},[]);
  const updatePreferences=(patch:Partial<GamePreferences>)=>setPreferences(current=>{const next=normalizePreferences({...current,...patch});void savePreference("game-preferences",next);return next});
  const navigate=(next:Screen)=>{setHistory(items=>[...items,screen]);setScreen(next)}; const goBack=()=>setHistory(items=>{const copy=items.slice();setScreen(copy.pop()||"home");return copy});
  useEffect(()=>{let live=true; fetch("./data/fighters-core.v2.json").then(response=>response.json()).then((data:RuntimeCatalog)=>{if(!live)return;setCatalog(data.fighters);setRoster(sampleFighters(data.fighters,10,41));}).finally(()=>live&&setCatalogLoading(false));return()=>{live=false}},[]);
  const startGame=()=>{
    setScreen("fighter");
    setHistory(["home"]);
    setActivePlayer(1); setSetupPlayer(1); setPlayer1(null); setPlayer2(null); setSelected(null);
    setPlayer1Cfu(100); setPlayer2Cfu(100); setPlayer1Arsenal(false); setPlayer2Arsenal(false);
    setEnvironment("Neutral"); setBattleSeed(17);
    setRoster(previous=>sampleFighters(catalog,10,rosterSeed+1,previous)); setRosterSeed(value=>value+1);
    gameFeedback.cue("select","medium");
  };
  const shuffleRoster=()=>{const next=rosterSeed+1;setRoster(previous=>sampleFighters(catalog,10,next,previous,activePlayer===2?player1||undefined:undefined));setRosterSeed(next);setSelected(null)};
  const confirmFighter=()=>{if(!selected)return;if(activePlayer===1){setPlayer1(selected);if(mode==="2_players"){setSelected(null);setActivePlayer(2);const next=rosterSeed+1;setRoster(previous=>sampleFighters(catalog,10,next,previous,selected));setRosterSeed(next);return}const rival=chooseCatalogOpponent(catalog,selected.catalogId,battleSeed);setPlayer2(rival);setPlayer2Cfu(generateOpponentCfu(battleSeed));setPlayer2Arsenal(new PythonRandom(battleSeed+1).random()>=.5);setSetupPlayer(1);setScreen("colony");return}setPlayer2(selected);setSetupPlayer(1);setScreen("colony")};
  const currentCfu=setupPlayer===1?player1Cfu:player2Cfu; const setCurrentCfu=setupPlayer===1?setPlayer1Cfu:setPlayer2Cfu; const currentArsenal=setupPlayer===1?player1Arsenal:player2Arsenal; const setCurrentArsenal=setupPlayer===1?setPlayer1Arsenal:setPlayer2Arsenal;
  const confirmArsenal=()=>{if(mode==="2_players"&&setupPlayer===1){setSetupPlayer(2);setScreen("colony")}else setScreen("environment")};
  const p1=player1||battleFighters[0],p2=player2||battleFighters[1];
  const result=useMemo(()=>scoreBattle({mode,seed:battleSeed,environment,player:p1,opponent:p2,playerColonyCfu:player1Cfu,opponentColonyCfu:player2Cfu,playerArsenal:player1Arsenal,opponentArsenal:player2Arsenal}),[mode,battleSeed,environment,p1,p2,player1Cfu,player2Cfu,player1Arsenal,player2Arsenal]);
  const content = screen === "home" ? <Home start={startGame} mode={mode} setMode={setMode} open={navigate} introSeen={preferences.introSeen||preferences.reducedMotion} skipIntro={()=>updatePreferences({introSeen:true})} ready={!catalogLoading&&catalog.length>0}/> :
    screen === "settings" ? <SettingsScreen preferences={preferences} update={updatePreferences} replayIntro={()=>{updatePreferences({introSeen:false});setHistory([]);setScreen("home")}}/> :
    screen === "how" ? <HowToPlay/> :
    screen === "lab" ? <MicrobeLab fighters={catalog} onChoose={fighter=>{setSelected(fighter);setActivePlayer(1);setHistory(["home","lab"]);setScreen("fighter")}}/> :
    screen === "fighter" ? <FighterScreen fighters={catalog} roster={roster} selected={selected} locked={player1} activePlayer={activePlayer} loading={catalogLoading} onSelect={setSelected} onConfirm={confirmFighter} onShuffle={shuffleRoster} onResetRoster={shuffleRoster}/> :
    screen === "colony" ? <Colony onConfirm={()=>setScreen("arsenal")} cfu={currentCfu} setCfu={setCurrentCfu} mode={mode} setupPlayer={setupPlayer} fighter={setupPlayer===1?p1:p2}/> :
    screen === "arsenal" ? <Arsenal onConfirm={confirmArsenal} active={currentArsenal} setActive={setCurrentArsenal} fighter={setupPlayer===1?p1:p2} mode={mode} setupPlayer={setupPlayer}/> :
    screen === "environment" ? <EnvironmentScreen go={setScreen} value={environment} setValue={setEnvironment} mode={mode} previewFor={env=>scoreBattle({mode,seed:battleSeed,environment:env,player:p1,opponent:p2,playerColonyCfu:player1Cfu,opponentColonyCfu:player2Cfu,playerArsenal:player1Arsenal,opponentArsenal:player2Arsenal})}/> :
    screen === "preview" ? <Preview go={setScreen} mode={mode} player={p1} opponent={p2} playerCfu={player1Cfu} opponentCfu={player2Cfu} playerArsenal={player1Arsenal} opponentArsenal={player2Arsenal} environment={environment} result={result}/> :
    screen === "arena" ? <Arena go={setScreen} mode={mode} player={p1} opponent={p2} environment={environment} result={result} seed={battleSeed} reducedMotion={preferences.reducedMotion}/> : <Results result={result} mode={mode} player={p1} opponent={p2} environment={environment} onRematch={()=>{setBattleSeed(seed=>seed+1);if(mode==="1_player")setPlayer2Cfu(generateOpponentCfu(battleSeed+1));setScreen("arena")}} onChangeFighters={startGame} onMainMenu={()=>{setPlayer1(null);setPlayer2(null);setSelected(null);setMode("1_player");setHistory([]);setScreen("home")}}/>;
  return <main className={`game-shell theme-${screen} viewport-${viewport} ${preferences.reducedMotion?"reduce-motion":""}`} data-viewport={viewport}><div className="liquid-bg"><i/><i/><i/></div><AppHeader screen={screen} goBack={goBack} setScreen={next=>next==="home"?(setHistory([]),setScreen("home")):navigate(next)}/><div className="screen-frame" key={screen}>{content}</div></main>;
}
