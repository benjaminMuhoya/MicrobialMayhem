"use client";

import { useMemo, useState } from "react";
import { PhaserArena } from "./components/PhaserArena";
import { scoreBattle } from "./game/scoring";
import type { BattleResult, Environment, Fighter, GameMode } from "./game/types";

type Screen = "home" | "fighter" | "colony" | "arsenal" | "environment" | "preview" | "arena" | "results";

const screens: { id: Screen; label: string }[] = [
  { id: "home", label: "Home" },
  { id: "fighter", label: "Fighter" },
  { id: "colony", label: "Colony" },
  { id: "arsenal", label: "Arsenal" },
  { id: "environment", label: "Habitat" },
  { id: "preview", label: "Preview" },
  { id: "arena", label: "Arena" },
  { id: "results", label: "Results" },
];

const roster = [
  { name: "Bacillus cereus", strain: "ATCC 14579", form: "Rod · spore-forming", habitat: "Soil & food", bgcs: 5, tone: "coral" },
  { name: "Pseudomonas fluorescens", strain: "A506", form: "Motile rod", habitat: "Plant surfaces", bgcs: 4, tone: "mint" },
  { name: "Streptomyces coelicolor", strain: "A3(2)", form: "Filamentous", habitat: "Temperate soil", bgcs: 22, tone: "violet" },
];
const battleFighters: Fighter[] = [
  {catalogId:"fixture:bacillus",fullName:"Bacillus cereus ATCC 14579",strain:"ATCC 14579",accessions:["BGC0000033","BGC0000034","BGC0000035","BGC0000036","BGC0000037"],products:["cereulide"],activities:["cytotoxic","antibacterial"],traits:[{trait:"Thermophile",evidenceLevel:"Direct evidence",field:"genes",explanation:"Resistance and heat-response evidence."}],description:"A documented Bacillus fighter.",cellShape:"rod",motility:"motile"},
  {catalogId:"fixture:psychrobacter",fullName:"Psychrobacter cryonix ICE-2",strain:"ICE-2",accessions:["BGC-COLD-1"],products:["cryoprotectin"],activities:["siderophore"],traits:[{trait:"Cryophile",evidenceLevel:"Direct evidence",field:"organism_name",explanation:"Cold-adaptation evidence."}],description:"A cold-adapted database rival.",cellShape:"coccus",motility:"non-motile"},
];

function Microbe({ tone = "mint", compact = false }: { tone?: string; compact?: boolean }) {
  return (
    <div className={`microbe microbe--${tone} ${compact ? "microbe--compact" : ""}`} aria-hidden="true">
      <span className="microbe__membrane" />
      <span className="microbe__core" />
      <span className="microbe__spark microbe__spark--one" />
      <span className="microbe__spark microbe__spark--two" />
      <span className="microbe__tail" />
    </div>
  );
}

function AppHeader({ screen, setScreen }: { screen: Screen; setScreen: (screen: Screen) => void }) {
  return (
    <header className="app-header">
      <button className="brand" onClick={() => setScreen("home")} aria-label="Microbial Mayhem home">
        <span className="brand__mark"><span /></span>
        <span><b>Microbial</b><em>Mayhem</em></span>
      </button>
      <nav className="prototype-nav" aria-label="Design prototype screens">
        {screens.map((item) => (
          <button key={item.id} className={screen === item.id ? "is-active" : ""} onClick={() => setScreen(item.id)}>
            {item.label}
          </button>
        ))}
      </nav>
      <button className="icon-button" aria-label="Open settings"><span className="gear">✦</span></button>
    </header>
  );
}

function Home({ go, mode, setMode }: { go: (screen: Screen) => void; mode: GameMode; setMode:(mode:GameMode)=>void }) {
  return (
    <section className="scene home-scene" data-testid="screen-home">
      <div className="home-copy">
        <p className="eyebrow">A microscopic battle of adaptation</p>
        <h1>Small cells.<br/><span>Big chemistry.</span></h1>
        <p className="lede">Build a living colony, choose an extreme habitat, and discover which bacterium is biologically prepared to thrive.</p>
        <div className="mode-picker" aria-label="Choose game mode">
          <button className={`mode-card ${mode==="1_player"?"is-selected":""}`} onClick={()=>setMode("1_player")}><span>01</span><b>One player</b><small>Face a database rival</small></button>
          <button className={`mode-card ${mode==="2_players"?"is-selected":""}`} onClick={()=>setMode("2_players")}><span>02</span><b>Two players</b><small>Pass-and-play locally</small></button>
        </div>
        <button className="primary-action" onClick={() => go("fighter")}>Enter the culture <span>→</span></button>
      </div>
      <div className="hero-dish" aria-label="Animated microscopic bacterial colony">
        <div className="dish-orbit dish-orbit--one" /><div className="dish-orbit dish-orbit--two" />
        <Microbe tone="coral" /><Microbe tone="mint" compact />
        <div className="specimen-tag"><span>LIVE SPECIMEN</span><b>Culture #MM-042</b></div>
      </div>
    </section>
  );
}

function Fighter({ go }: { go: (screen: Screen) => void }) {
  const [selected, setSelected] = useState(1);
  const fighter = roster[selected];
  return (
    <section className="scene explorer" data-testid="screen-fighter">
      <div className="screen-heading"><div><p className="eyebrow">Player 1 · specimen selection</p><h2>Choose your organism</h2></div><p>Recorded biology drives the battle.<br/>Procedural styling gives it personality.</p></div>
      <div className="explorer-grid">
        <aside className="roster-panel">
          <label className="search"><span>⌕</span><input aria-label="Search bacterial fighters" placeholder="Search genus, species, or strain" /></label>
          <div className="roster-list">
            {roster.map((item, index) => <button key={item.name} onClick={() => setSelected(index)} className={selected === index ? "is-selected" : ""}>
              <Microbe tone={item.tone} compact /><span><i>{item.name}</i><small>{item.strain} · {item.bgcs} BGCs</small></span><b>→</b>
            </button>)}
          </div>
          <button className="quiet-action">Shuffle the culture shelf</button>
        </aside>
        <article className="fighter-focus">
          <div className="fighter-stage"><div className="focus-ring"/><Microbe tone={fighter.tone}/><span className="recorded-pill">Recorded morphology</span></div>
          <div className="fighter-info"><p className="eyebrow">Selected fighter</p><h3><i>{fighter.name}</i></h3><p className="strain">strain {fighter.strain}</p>
            <div className="fact-row"><span><small>Morphology</small><b>{fighter.form}</b></span><span><small>Habitat</small><b>{fighter.habitat}</b></span><span><small>Known BGCs</small><b>{fighter.bgcs} documented</b></span></div>
            <div className="ability"><span className="ability__icon">✦</span><span><small>Signature chemistry</small><b>Documented biosynthetic activity</b></span><button>Biology details</button></div>
            <button className="primary-action" onClick={() => go("colony")}>Culture this fighter <span>→</span></button>
          </div>
        </article>
      </div>
    </section>
  );
}

function Colony({ go, cfu, setCfu }: { go: (screen: Screen) => void; cfu:number; setCfu:(cfu:number)=>void }) {
  const cells = Math.max(7, Math.round(cfu / 35));
  const score = Math.log10(cfu + 1) / Math.log10(1001) * 10;
  return <section className="scene colony-scene" data-testid="screen-colony">
    <div className="screen-heading"><div><p className="eyebrow">Step 2 · colony preparation</p><h2>Grow your numbers</h2></div><p>More cells add strength with diminishing returns.</p></div>
    <div className="colony-layout">
      <div className="culture-dish" style={{"--energy": `${cfu / 1000}`} as React.CSSProperties}>
        <div className="culture-dish__well">
          {Array.from({ length: cells }).map((_, i) => <i key={i} style={{"--i": i, "--angle": `${(i * 137.5) % 360}deg`, "--radius": `${20 + (i * 17) % 38}%`} as React.CSSProperties}/>) }
        </div><span className="dish-label">Live colony · density preview</span>
      </div>
      <div className="colony-controls"><p className="eyebrow">Colony size</p><div className="cfu-readout"><b>{cfu.toLocaleString()}</b><span>CFU</span></div><p className="colony-name">{cfu < 200 ? "A nimble micro-colony" : cfu < 650 ? "A lively, balanced culture" : "A densely packed population"}</p>
        <input aria-label="Colony forming units" type="range" min="0" max="1000" step="10" value={cfu} onChange={(event) => setCfu(Number(event.target.value))}/>
        <div className="range-labels"><span>0</span><span>1,000</span></div>
        <div className="score-contribution"><span>Battle contribution</span><b>+{score.toFixed(1)}</b><small>of 10 points</small></div>
        <button className="primary-action" onClick={() => go("arsenal")}>Lock colony <span>→</span></button>
      </div>
    </div>
  </section>;
}

function Arsenal({go,active,setActive}:{go:(screen:Screen)=>void;active:boolean;setActive:(value:boolean)=>void}){
  return <section className="scene prep-scene" data-testid="screen-arsenal"><div className="screen-heading"><div><p className="eyebrow">Step 3 · biosynthetic preparation</p><h2>Activate documented chemistry?</h2></div><p>Five MIBiG records are available for this fighter.</p></div><div className="gene-stage"><Microbe tone="violet"/><div className={`gene-chain ${active?"is-active":""}`}>{[1,2,3,4,5].map(i=><i key={i}>BGC {i}</i>)}</div></div><div className="prep-controls"><p><b>{active?"Arsenal activated":"Arsenal dormant"}</b><span>{active?"Documented clusters contribute up to +5 offense points.":"Known activity remains documented, but BGC accessions add no arsenal points."}</span></p><div className="binary-choice"><button className={active?"is-selected":""} onClick={()=>setActive(true)}>Activate</button><button className={!active?"is-selected":""} onClick={()=>setActive(false)}>Keep dormant</button></div><button className="primary-action" onClick={()=>go("environment")}>Confirm preparation <span>→</span></button></div></section>
}

const environments:Environment[]=["Neutral","Salty","Alkaline","Hot","Cold","Acidic","In the presence of antibiotics"];
function EnvironmentScreen({go,value,setValue}:{go:(screen:Screen)=>void;value:Environment;setValue:(value:Environment)=>void}){
 return <section className={`scene environment-scene env-${value.replaceAll(" ","-").toLowerCase()}`} data-testid="screen-environment"><div className="screen-heading"><div><p className="eyebrow">Step 4 · habitat pressure</p><h2>Choose the living arena</h2></div><p>Actual modifiers are shown before confirmation.</p></div><div className="environment-grid">{environments.map(env=><button key={env} onClick={()=>setValue(env)} className={value===env?"is-selected":""}><i/><b>{env==="In the presence of antibiotics"?"Antibiotics":env}</b><small>{env==="Hot"?"Player +12 · Rival +0":env==="Cold"?"Player +0 · Rival +12":env==="Neutral"?"Both +0":"No supported match · both −3"}</small></button>)}</div><div className="environment-confirm"><p><span>Selected habitat</span><b>{value}</b><small>{value==="Hot"?"Supported thermophile evidence gives your fighter +12.":value==="Cold"?"Supported cryophile evidence gives the rival +12.":value==="Neutral"?"Neutral medium changes neither score.":"Current evidence preview applies the shared uncertainty rule."}</small></p><button className="primary-action" onClick={()=>go("preview")}>Enter this habitat <span>→</span></button></div></section>
}

function Preview({ go }: { go: (screen: Screen) => void }) {
  return <section className="scene preview-scene" data-testid="screen-preview"><div className="arena-aura"/>
    <div className="screen-heading centered"><p className="eyebrow">Hot spring · 78°C</p><h2>Ready to culture chaos?</h2><p>Thermophile evidence grants the left fighter a <b>+12 environment advantage</b>.</p></div>
    <div className="versus"><article><span className="player-label">Your fighter</span><Microbe tone="coral"/><h3><i>Bacillus cereus</i></h3><dl><div><dt>Colony</dt><dd>500 CFU</dd></div><div><dt>Arsenal</dt><dd className="active">Activated</dd></div></dl></article><span className="versus-mark">VS</span><article><span className="player-label">Database rival</span><Microbe tone="mint"/><h3><i>Psychrobacter cryonix</i></h3><dl><div><dt>Colony</dt><dd>250 CFU</dd></div><div><dt>Arsenal</dt><dd>Dormant</dd></div></dl></article></div>
    <button className="primary-action centered-action" onClick={() => go("arena")}>Enter the microscopic arena <span>→</span></button>
  </section>;
}

function Arena({ go }: { go: (screen: Screen) => void }) {
  return <section className="scene arena-scene" data-testid="screen-arena"><div className="heat-haze"/><div className="arena-top"><div><small>You · <i>B. cereus</i></small><span><b style={{width:"64%"}}/></span></div><p>HOT SPRING <small>78°C</small></p><div><small>Rival · <i>P. cryonix</i></small><span><b style={{width:"38%"}}/></span></div></div>
    <PhaserArena />
    <div className="battle-caption"><span>05.8s</span><p><b>Environment pressure</b> · Heat adaptation is shifting the momentum.</p><button onClick={() => go("results")}>Skip →</button></div>
  </section>;
}

function Results({ go, result }: { go: (screen: Screen) => void; result:BattleResult }) {
  const [expanded, setExpanded] = useState(false);
  const playerWon=result.winner==="A"; return <section className="scene results-scene" data-testid="screen-results"><div className="result-orbit"><Microbe tone={playerWon?"coral":"mint"}/></div><p className="eyebrow">Culture resolved</p><h2>{result.winner==="tie"?"Perfect equilibrium.":playerWon?"Victory blooms.":"The rival thrives."}</h2><h3><i>{playerWon?result.player.fighterName:result.opponent.fighterName}</i> {result.winner==="tie"?"draws":"wins"}</h3><p className="result-lede">Environment, colony growth and documented chemistry resolved this precomputed outcome.</p>
    <div className="score-pair"><div><small>Your score</small><b>{result.player.total.toFixed(1)}</b></div><span>{(result.player.total-result.opponent.total)>=0?"+":""}{(result.player.total-result.opponent.total).toFixed(1)}</span><div><small>Rival score</small><b>{result.opponent.total.toFixed(1)}</b></div></div>
    <button className="science-toggle" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>Scientific breakdown <span>{expanded ? "−" : "+"}</span></button>
    {expanded && <div className="breakdown">{result.player.components.filter(c=>c.name!=="Base"&&c.includedInTotal).map(c=><span key={c.name}><b>{c.value>=0?"+":""}{c.value.toFixed(1)}</b>{c.name}</span>)}</div>}
    <div className="result-actions"><button className="primary-action">Rematch <span>↻</span></button><button onClick={() => go("fighter")}>Change fighters</button><button onClick={() => go("home")}>Main menu</button></div>
  </section>;
}

export default function HomePage() {
  const [screen, setScreen] = useState<Screen>("home");
  const [mode,setMode]=useState<GameMode>("1_player"); const [cfu,setCfu]=useState(500); const [arsenal,setArsenal]=useState(true); const [environment,setEnvironment]=useState<Environment>("Hot");
  const result=useMemo(()=>scoreBattle({mode,seed:17,environment,player:battleFighters[0],opponent:battleFighters[1],playerColonyCfu:cfu,opponentColonyCfu:250,playerArsenal:arsenal,opponentArsenal:false}),[mode,cfu,arsenal,environment]);
  const content = screen === "home" ? <Home go={setScreen} mode={mode} setMode={setMode}/> :
    screen === "fighter" ? <Fighter go={setScreen}/> :
    screen === "colony" ? <Colony go={setScreen} cfu={cfu} setCfu={setCfu}/> :
    screen === "arsenal" ? <Arsenal go={setScreen} active={arsenal} setActive={setArsenal}/> :
    screen === "environment" ? <EnvironmentScreen go={setScreen} value={environment} setValue={setEnvironment}/> :
    screen === "preview" ? <Preview go={setScreen}/> :
    screen === "arena" ? <Arena go={setScreen}/> : <Results go={setScreen} result={result}/>;
  return <main className={`game-shell theme-${screen}`}><div className="liquid-bg"><i/><i/><i/></div><AppHeader screen={screen} setScreen={setScreen}/><div className="screen-frame" key={screen}>{content}</div><footer><span>Design prototype · Phase 2</span><span>Biology first · outcome precomputed</span></footer></main>;
}
