import { execFile } from "node:child_process";
import { promisify } from "node:util";

const run = promisify(execFile);
const sdk = process.env.ANDROID_HOME;
if (!sdk) throw new Error("ANDROID_HOME is required.");
const adb = `${sdk}/platform-tools/adb`;
const endpoint = process.env.WEBVIEW_CDP || "http://127.0.0.1:9222";
const targets = await fetch(`${endpoint}/json`).then(response => response.json());
const target = targets.find(item => item.type === "page" && item.url === "https://localhost/");
if (!target) throw new Error("The Microbial Mayhem WebView is not available.");
const description = JSON.parse(target.description);

const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{socket.addEventListener("open",resolve,{once:true});socket.addEventListener("error",reject,{once:true})});
let commandId = 0;
const pending = new Map();
socket.addEventListener("message",event=>{const message=JSON.parse(event.data);if(!message.id)return;const handler=pending.get(message.id);if(!handler)return;pending.delete(message.id);if(message.error)handler.reject(new Error(message.error.message));else handler.resolve(message.result)});
const command=(method,params={})=>new Promise((resolve,reject)=>{const id=++commandId;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}))});
const evaluate=async expression=>{const result=await command("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw new Error(result.exceptionDetails.exception?.description||result.exceptionDetails.text);return result.result.value};
await command("Runtime.enable");

const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
const waitFor = async expression => {
  for(let attempt=0;attempt<40;attempt+=1){if(await evaluate(expression))return;await wait(250)}
  throw new Error(`Timed out waiting for ${expression}`);
};
const buttonExpression = label => `Array.from(document.querySelectorAll('button')).find(button=>(button.getAttribute('aria-label')||button.textContent).replace(/\\s+/g,' ').trim().includes(${JSON.stringify(label)}))`;
const selectorExpression = selector => `document.querySelector(${JSON.stringify(selector)})`;
const deviceRect = async elementExpression => {
  const metrics=await evaluate(`(()=>{const element=${elementExpression};if(!element)return null;element.scrollIntoView({block:'center',inline:'nearest'});const box=element.getBoundingClientRect();return{x:box.x,y:box.y,width:box.width,height:box.height,viewportWidth:innerWidth,viewportHeight:innerHeight}})()`);
  if(!metrics)throw new Error("Touch target is not visible.");
  const scaleX=description.width/metrics.viewportWidth,scaleY=description.height/metrics.viewportHeight;
  return{x:Math.round(description.screenX+(metrics.x+metrics.width/2)*scaleX),y:Math.round(description.screenY+(metrics.y+metrics.height/2)*scaleY),top:Math.round(description.screenY+metrics.y*scaleY),bottom:Math.round(description.screenY+(metrics.y+metrics.height)*scaleY)};
};
const tap = async elementExpression => {
  const point=await deviceRect(elementExpression);
  await run(adb,["shell","input","tap",String(point.x),String(point.y)]);
  await wait(400);
};
const swipeInside = async (elementExpression,direction="up") => {
  const point=await deviceRect(elementExpression);
  const start=direction==="up"?point.bottom-35:point.top+35,end=direction==="up"?point.top+35:point.bottom-35;
  await run(adb,["shell","input","swipe",String(point.x),String(start),String(point.x),String(end),"450"]);
  await wait(700);
};
const swipeViewport = async direction => {
  const x=Math.round(description.screenX+description.width*.88),top=description.screenY+180,bottom=description.screenY+description.height-180;
  const start=direction==="up"?bottom:top,end=direction==="up"?top:bottom;
  await run(adb,["shell","input","swipe",String(x),String(start),String(x),String(end),"500"]);
  await wait(700);
};

await waitFor("document.readyState==='complete'");
const viewportState=()=>evaluate(`(()=>{const root=document.documentElement,body=document.body;return{scrollX,scrollY,rootWidth:root.scrollWidth,rootHeight:root.scrollHeight,bodyWidth:body.scrollWidth,bodyHeight:body.scrollHeight,width:innerWidth,height:innerHeight,actions:Array.from(document.querySelectorAll('.screen-frame .primary-action,.screen-frame .pause-button')).filter(element=>element.offsetParent!==null).map(element=>{const box=element.getBoundingClientRect();return{label:element.textContent.trim(),left:box.left,top:box.top,right:box.right,bottom:box.bottom}})}})()`);
const assertFixedViewport=async label=>{const state=await viewportState();if(state.scrollX!==0||state.scrollY!==0||state.rootWidth>state.width+1||state.rootHeight>state.height+1||state.bodyWidth>state.width+1||state.bodyHeight>state.height+1)throw new Error(`${label} allowed root scrolling or overflow: ${JSON.stringify(state)}`);const outside=state.actions.find(action=>action.left< -1||action.top< -1||action.right>state.width+1||action.bottom>state.height+1);if(outside)throw new Error(`${label} placed an essential action outside the viewport: ${JSON.stringify(outside)}`);return state};
await swipeViewport("up");
const fixedRootAfterPhysicalSwipe=await assertFixedViewport("Home after physical swipe");
if(await evaluate(`Boolean(${buttonExpression("Discard")})`))await tap(buttonExpression("Discard"));
await tap(buttonExpression("One player"));
await tap(buttonExpression("Enter the culture"));
if(await evaluate(`Boolean(${buttonExpression("Skip")})`))await tap(buttonExpression("Skip"));
await waitFor("Boolean(document.querySelector('[data-testid=screen-fighter]'))");
await assertFixedViewport("Fighter selection");

const roster=selectorExpression("[data-testid=fighter-choice-list]");
const choices=`${roster}.querySelectorAll('button')`;
if(await evaluate(`${choices}.length`)!==10)throw new Error("The packaged roster does not contain ten fighters.");
const before=await evaluate(`(()=>{const element=${roster};return{scrollTop:element.scrollTop,selected:element.querySelectorAll('[aria-pressed=true]').length,touchAction:getComputedStyle(element).touchAction}})()`);
await swipeInside(roster,"up");
const after=await evaluate(`(()=>{const element=${roster};return{scrollTop:element.scrollTop,selected:element.querySelectorAll('[aria-pressed=true]').length}})()`);
if(after.scrollTop<=before.scrollTop)throw new Error("A physical upward swipe did not move the packaged roster.");
if(after.selected!==before.selected)throw new Error("Roster scrolling accidentally selected a fighter.");

for(let index=0;index<4;index+=1)await swipeInside(roster,"up");
const last=`${choices}[${await evaluate(`${choices}.length`)}-1]`;
await tap(last);
if(await evaluate(`${last}.getAttribute('aria-pressed')`)!=="true")throw new Error("The last fighter could not be selected after scrolling.");

const retainedPosition=await evaluate(`${roster}.scrollTop`);
await tap(buttonExpression("Compare fighter"));
await evaluate(`${choices}[0].click()`);
await waitFor("Boolean(document.querySelector('[data-testid=fighter-comparison]'))");
const comparisonScroll=selectorExpression("[data-testid=comparison-scroll-region]");
const comparisonBefore=await evaluate(`${comparisonScroll}.scrollTop`);
await swipeInside(comparisonScroll,"up");
const comparisonAfter=await evaluate(`${comparisonScroll}.scrollTop`);
if(comparisonAfter<=comparisonBefore)throw new Error("A physical swipe did not scroll the comparison modal.");
await evaluate(`${buttonExpression("Close fighter comparison")}.click()`);
await waitFor("!document.querySelector('[data-testid=fighter-comparison]')");
const restoredPosition=await evaluate(`${roster}.scrollTop`);
if(Math.abs(restoredPosition-retainedPosition)>12)throw new Error("Closing comparison changed the roster position.");

await tap(buttonExpression("Compare fighter"));
await evaluate(`${choices}[0].click()`);
await waitFor("Boolean(document.querySelector('[data-testid=fighter-comparison]'))");
await run(adb,["shell","settings","put","system","accelerometer_rotation","0"]);
await run(adb,["shell","settings","put","system","user_rotation","1"]);
await waitFor("document.querySelector('main.game-shell')?.dataset.viewport==='phone-landscape'");
const landscape=await evaluate(`(()=>{const modal=document.querySelector('[data-testid=fighter-comparison]'),panel=modal?.querySelector('.comparison-panel'),box=panel?.getBoundingClientRect(),roster=${roster};return{modal:Boolean(modal),selected:roster.querySelectorAll('[aria-pressed=true]').length,scrollTop:roster.scrollTop,noHorizontalOverflow:document.documentElement.scrollWidth<=innerWidth+1,modalFits:Boolean(box)&&box.left>=-1&&box.top>=-1&&box.right<=innerWidth+1&&box.bottom<=innerHeight+1,modalAboveHeader:Number(getComputedStyle(modal).zIndex)>Number(getComputedStyle(document.querySelector('.game-hud')).zIndex||0)}})()`);
if(!landscape.modal||landscape.selected!==1||!landscape.noHorizontalOverflow||!landscape.modalFits||!landscape.modalAboveHeader)throw new Error(`Landscape rotation did not preserve a usable comparison state: ${JSON.stringify(landscape)}`);
await run(adb,["shell","settings","put","system","user_rotation","0"]);
await waitFor("document.querySelector('main.game-shell')?.dataset.viewport==='phone-portrait'");
await evaluate(`${buttonExpression("Close fighter comparison")}.click()`);

const completeMatch=async (label,physical=true)=>{
  const activate=async text=>physical?tap(buttonExpression(text)):evaluate(`${buttonExpression(text)}.click()`);
  await activate("Select Player 1 fighter");
  await waitFor("Boolean(document.querySelector('[data-testid=screen-colony]'))");
  await assertFixedViewport(`${label} colony`);
  await activate("Lock Player 1 colony");
  await waitFor("Boolean(document.querySelector('[data-testid=screen-arsenal]'))");
  await assertFixedViewport(`${label} arsenal`);
  await activate("Confirm Player 1 preparation");
  await waitFor("Boolean(document.querySelector('[data-testid=screen-environment]'))");
  await assertFixedViewport(`${label} environment`);
  await activate("Enter this habitat");
  await waitFor("Boolean(document.querySelector('[data-testid=screen-preview]'))");
  await assertFixedViewport(`${label} preview`);
  await activate("Enter the microscopic arena");
  await waitFor("Boolean(document.querySelector('[data-testid=screen-arena]'))");
  await assertFixedViewport(`${label} battle`);
  await evaluate(`${buttonExpression("Skip battle")}.click()`);
  await waitFor("Boolean(document.querySelector('[data-testid=screen-results]'))");
  await assertFixedViewport(`${label} results`);
};

await completeMatch("Portrait");
const resultsPanel=selectorExpression("[data-testid=screen-results]");
const resultsBefore=await evaluate(`${resultsPanel}.scrollTop`);
await swipeInside(resultsPanel,"up");
const resultsAfter=await evaluate(`${resultsPanel}.scrollTop`);
if(resultsAfter<=resultsBefore)throw new Error("Physical results swipe did not move the internal results panel.");
await assertFixedViewport("Portrait results after internal swipe");
await tap(buttonExpression("Main menu"));
await waitFor("Boolean(document.querySelector('[data-testid=screen-home]'))");
await run(adb,["shell","settings","put","system","user_rotation","1"]);
await waitFor("document.querySelector('main.game-shell')?.dataset.viewport==='phone-landscape'");
await evaluate(`${buttonExpression("One player")}.click()`);
await evaluate(`${buttonExpression("Enter the culture")}.click()`);
if(await evaluate(`Boolean(${buttonExpression("Skip")})`))await evaluate(`${buttonExpression("Skip")}.click()`);
await waitFor("Boolean(document.querySelector('[data-testid=screen-fighter]'))");
await evaluate(`${selectorExpression("[data-testid=fighter-choice-list]")}.querySelector('button:not([disabled])').click()`);
await completeMatch("Landscape",false);
await run(adb,["shell","settings","put","system","user_rotation","0"]);

console.log(JSON.stringify({runtime:"Capacitor Android WebView",rootFixedAfterPhysicalSwipe:fixedRootAfterPhysicalSwipe,rosterTouchAction:before.touchAction,rosterScroll:[before.scrollTop,after.scrollTop],comparisonScroll:[comparisonBefore,comparisonAfter],resultsScroll:[resultsBefore,resultsAfter],lastFighterSelected:true,accidentalSelection:false,rosterPositionRestored:true,orientationStatePreserved:true,portraitCompleteFlow:true,landscapeCompleteFlow:true,landscapeComparison:landscape},null,2));
socket.close();
