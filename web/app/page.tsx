"use client";

import { useMemo, useState } from "react";

type Screen = "home" | "fighter" | "colony" | "preview" | "arena" | "results";

const screens: { id: Screen; label: string }[] = [
  { id: "home", label: "Home" },
  { id: "fighter", label: "Fighter" },
  { id: "colony", label: "Colony" },
  { id: "preview", label: "Preview" },
  { id: "arena", label: "Arena" },
  { id: "results", label: "Results" },
];

const roster = [
  { name: "Bacillus cereus", strain: "ATCC 14579", form: "Rod · spore-forming", habitat: "Soil & food", bgcs: 5, tone: "coral" },
  { name: "Pseudomonas fluorescens", strain: "A506", form: "Motile rod", habitat: "Plant surfaces", bgcs: 4, tone: "mint" },
  { name: "Streptomyces coelicolor", strain: "A3(2)", form: "Filamentous", habitat: "Temperate soil", bgcs: 22, tone: "violet" },
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

function Home({ go }: { go: (screen: Screen) => void }) {
  return (
    <section className="scene home-scene" data-testid="screen-home">
      <div className="home-copy">
        <p className="eyebrow">A microscopic battle of adaptation</p>
        <h1>Small cells.<br/><span>Big chemistry.</span></h1>
        <p className="lede">Build a living colony, choose an extreme habitat, and discover which bacterium is biologically prepared to thrive.</p>
        <div className="mode-picker" aria-label="Choose game mode">
          <button className="mode-card is-selected"><span>01</span><b>One player</b><small>Face a database rival</small></button>
          <button className="mode-card"><span>02</span><b>Two players</b><small>Pass-and-play locally</small></button>
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

function Colony({ go }: { go: (screen: Screen) => void }) {
  const [cfu, setCfu] = useState(500);
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
        <button className="primary-action" onClick={() => go("preview")}>Lock colony <span>→</span></button>
      </div>
    </div>
  </section>;
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
    <div className="battlefield"><div className="battle-fighter battle-fighter--left"><Microbe tone="coral"/><span>Thermocin surge</span></div><div className="impact-bloom"><i/><i/><i/></div><div className="battle-fighter battle-fighter--right"><Microbe tone="mint"/><span>Membrane guard</span></div></div>
    <div className="battle-caption"><span>05.8s</span><p><b>Environment pressure</b> · Heat adaptation is shifting the momentum.</p><button onClick={() => go("results")}>Skip →</button></div>
  </section>;
}

function Results({ go }: { go: (screen: Screen) => void }) {
  const [expanded, setExpanded] = useState(false);
  return <section className="scene results-scene" data-testid="screen-results"><div className="result-orbit"><Microbe tone="coral"/></div><p className="eyebrow">Culture resolved</p><h2>Victory blooms.</h2><h3><i>Bacillus cereus</i> wins</h3><p className="result-lede">Heat adaptation and an active biosynthetic arsenal created the decisive edge.</p>
    <div className="score-pair"><div><small>Your score</small><b>52.8</b></div><span>+13.4</span><div><small>Rival score</small><b>39.4</b></div></div>
    <button className="science-toggle" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>Scientific breakdown <span>{expanded ? "−" : "+"}</span></button>
    {expanded && <div className="breakdown"><span><b>+12</b> Heat match</span><span><b>+8.2</b> Colony</span><span><b>+5</b> BGC arsenal</span><span><b>+5</b> Known activity</span></div>}
    <div className="result-actions"><button className="primary-action">Rematch <span>↻</span></button><button onClick={() => go("fighter")}>Change fighters</button><button onClick={() => go("home")}>Main menu</button></div>
  </section>;
}

export default function HomePage() {
  const [screen, setScreen] = useState<Screen>("home");
  const content = useMemo(() => ({ home: <Home go={setScreen}/>, fighter: <Fighter go={setScreen}/>, colony: <Colony go={setScreen}/>, preview: <Preview go={setScreen}/>, arena: <Arena go={setScreen}/>, results: <Results go={setScreen}/> })[screen], [screen]);
  return <main className={`game-shell theme-${screen}`}><div className="liquid-bg"><i/><i/><i/></div><AppHeader screen={screen} setScreen={setScreen}/><div className="screen-frame" key={screen}>{content}</div><footer><span>Design prototype · Phase 2</span><span>Biology first · outcome precomputed</span></footer></main>;
}
