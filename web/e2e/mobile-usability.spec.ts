import { expect, test, type Page } from "@playwright/test";

const devices = [
  { name: "phone portrait", width: 390, height: 844 },
  { name: "phone landscape", width: 844, height: 390 },
  { name: "iPad portrait", width: 820, height: 1180 },
  { name: "iPad landscape", width: 1180, height: 820 },
] as const;

async function openSelection(page:Page,mode:"one"|"two"="one"){
  await page.goto("/");
  if(mode==="two")await page.getByRole("button",{name:/Two players/}).click();
  await page.getByRole("button",{name:"Enter the culture →"}).click();
  const tutorial=page.getByRole("region",{name:"Interactive tutorial"});
  if(await tutorial.isVisible())await tutorial.getByRole("button",{name:"Skip"}).click();
  await expect(page.getByTestId("screen-fighter")).toBeVisible();
}

async function touchSwipe(page:Page,start:{x:number;y:number},end:{x:number;y:number}){
  const session=await page.context().newCDPSession(page);
  await session.send("Input.synthesizeScrollGesture",{x:start.x,y:start.y,xDistance:end.x-start.x,yDistance:end.y-start.y,speed:800,gestureSourceType:"touch"});
  await session.detach();
  await page.waitForTimeout(150);
}

async function expectFixedViewport(page:Page){
  const metrics=await page.evaluate(()=>({
    scrollX:window.scrollX,scrollY:window.scrollY,
    rootWidth:document.documentElement.scrollWidth,rootHeight:document.documentElement.scrollHeight,
    bodyWidth:document.body.scrollWidth,bodyHeight:document.body.scrollHeight,
    width:innerWidth,height:innerHeight,
  }));
  expect(metrics.scrollX).toBe(0);
  expect(metrics.scrollY).toBe(0);
  expect(metrics.rootWidth).toBeLessThanOrEqual(metrics.width+1);
  expect(metrics.rootHeight).toBeLessThanOrEqual(metrics.height+1);
  expect(metrics.bodyWidth).toBeLessThanOrEqual(metrics.width+1);
  expect(metrics.bodyHeight).toBeLessThanOrEqual(metrics.height+1);
  const controls=page.locator(".screen-frame .primary-action:visible:not([disabled]), .screen-frame .result-actions button:visible:not([disabled]), .screen-frame .pause-button:visible:not([disabled])");
  for(let index=0;index<await controls.count();index+=1){
    const box=await controls.nth(index).boundingBox();
    if(!box)continue;
    expect(box.x+box.width).toBeLessThanOrEqual(metrics.width+1);
    expect(box.y+box.height).toBeLessThanOrEqual(metrics.height+1);
    expect(box.x).toBeGreaterThanOrEqual(-1);
    expect(box.y).toBeGreaterThanOrEqual(-1);
  }
}

async function previewAndConfirm(page:Page,player:1|2,index=0){
  const allChoices=page.locator(".roster-list button"),choices=page.locator(".roster-list button:not([disabled])");
  await expect(allChoices).toHaveCount(10);
  const choice=choices.nth(index);
  await choice.click();
  await expect(page.getByTestId("screen-fighter")).toBeVisible();
  await expectFixedViewport(page);
  await page.getByRole("button",{name:`Select Player ${player} fighter →`}).first().click();
  await expectFixedViewport(page);
}

async function preparePlayer(page:Page,player:1|2){
  await page.getByRole("button",{name:`Lock Player ${player} colony →`}).click();
  await expectFixedViewport(page);
  await page.getByRole("button",{name:`Confirm Player ${player} preparation →`}).click();
  await expectFixedViewport(page);
}

async function finishMatch(page:Page,mode:"one"|"two"){
  await previewAndConfirm(page,1,0);
  if(mode==="two")await previewAndConfirm(page,2,0);
  await preparePlayer(page,1);
  if(mode==="two")await preparePlayer(page,2);
  await page.getByRole("button",{name:"Enter this habitat →"}).click();
  await expectFixedViewport(page);
  await page.getByRole("button",{name:"Enter the microscopic arena →"}).click();
  await expectFixedViewport(page);
  const skip=page.getByRole("button",{name:"Skip battle →"});
  const results=page.getByTestId("screen-results");
  await Promise.race([skip.waitFor({state:"visible",timeout:15_000}),results.waitFor({state:"visible",timeout:15_000})]);
  if(await skip.isVisible())await skip.click();
  await expect(results).toBeVisible({timeout:15_000});
  await expectFixedViewport(page);
}

test("selection shows ten vertically scrollable choices and requires explicit confirmation",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await openSelection(page);
  const list=page.getByTestId("fighter-choice-list"),choices=list.locator("button");
  await expect(choices).toHaveCount(10);
  const metrics=await list.evaluate(element=>{const style=getComputedStyle(element);return{clientHeight:element.clientHeight,scrollHeight:element.scrollHeight,overflowY:style.overflowY,touchAction:style.touchAction}});
  expect(metrics.scrollHeight).toBeGreaterThan(metrics.clientHeight);
  expect(metrics.overflowY).toBe("auto");
  expect(metrics.touchAction).toBe("pan-y");
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
  const beforeSelection=await choices.evaluateAll(items=>items.filter(item=>item.getAttribute("aria-pressed")==="true").length);
  await list.scrollIntoViewIfNeeded();
  const box=await list.boundingBox();
  expect(box).not.toBeNull();
  await touchSwipe(page,{x:(box?.x||0)+(box?.width||0)/2,y:(box?.y||0)+(box?.height||0)-24},{x:(box?.x||0)+(box?.width||0)/2,y:(box?.y||0)+30});
  expect(await list.evaluate(element=>element.scrollTop)).toBeGreaterThan(0);
  expect(await choices.evaluateAll(items=>items.filter(item=>item.getAttribute("aria-pressed")==="true").length)).toBe(beforeSelection);
  await choices.last().scrollIntoViewIfNeeded();
  await expect(choices.last()).toBeInViewport();
  const last=choices.last();
  await last.click();
  await expect(last).toHaveAttribute("aria-pressed","true");
  await last.click();
  await expect(page.getByTestId("screen-fighter")).toBeVisible();
  await page.getByRole("button",{name:"Select Player 1 fighter →"}).click();
  await expect(page.getByTestId("screen-colony")).toBeVisible();
});

test("comparison keeps preview and comparison fighters separate until explicit selection",async({page})=>{
  await page.setViewportSize({width:390,height:640});
  await openSelection(page);
  const list=page.getByTestId("fighter-choice-list"),choices=list.locator("button");
  await expect(choices).toHaveCount(10);
  await choices.first().click();
  const previewName=await choices.first().getAttribute("data-fighter-name");
  await list.evaluate(element=>{element.scrollTop=180});
  const savedScroll=await list.evaluate(element=>element.scrollTop);
  await page.getByRole("button",{name:"Compare fighter"}).click();
  await expect(page.getByTestId("fighter-comparison")).toHaveCount(0);
  await choices.nth(2).click();
  const panel=page.getByTestId("fighter-comparison");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText("Morphology");
  await expect(panel).toContainText("Habitat");
  await expect(panel).toContainText("Known BGCs");
  await expect(panel).toContainText("Recorded adaptations");
  await expect(panel).toContainText("Evidence availability");
  await expect(panel).toContainText("Colony traits");
  const names=await panel.locator(".comparison-fighters article").evaluateAll(items=>items.map(item=>item.getAttribute("data-fighter-name")));
  expect(names).toHaveLength(2);
  expect(names[0]).toBe(previewName);
  expect(names[1]).not.toBe(previewName);
  const comparisonScroll=panel.getByTestId("comparison-scroll-region"),comparisonBox=await comparisonScroll.boundingBox();
  expect(comparisonBox).not.toBeNull();
  const comparisonMetrics=await comparisonScroll.evaluate(element=>({clientHeight:element.clientHeight,scrollHeight:element.scrollHeight,touchAction:getComputedStyle(element).touchAction}));
  expect(comparisonMetrics.scrollHeight).toBeGreaterThan(comparisonMetrics.clientHeight);
  expect(comparisonMetrics.touchAction).toBe("pan-y");
  await touchSwipe(page,{x:(comparisonBox?.x||0)+(comparisonBox?.width||0)/2,y:(comparisonBox?.y||0)+(comparisonBox?.height||0)-25},{x:(comparisonBox?.x||0)+(comparisonBox?.width||0)/2,y:(comparisonBox?.y||0)+25});
  expect(await comparisonScroll.evaluate(element=>element.scrollTop)).toBeGreaterThan(0);
  await expect(choices.first()).toHaveAttribute("aria-pressed","true");
  await expect(page.getByTestId("screen-fighter")).toBeVisible();
  await panel.getByRole("button",{name:"Cancel comparison"}).click();
  await expect(panel).toHaveCount(0);
  expect(Math.abs((await list.evaluate(element=>element.scrollTop))-savedScroll)).toBeLessThanOrEqual(12);
  await page.getByRole("button",{name:"Compare fighter"}).click();
  await choices.nth(2).click();
  await page.getByTestId("fighter-comparison").getByRole("button",{name:"Select Player 1 fighter →"}).click();
  await expect(page.getByTestId("screen-colony")).toBeVisible();
});

test("orientation changes retain the preview, roster position, and open comparison",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await openSelection(page);
  const list=page.getByTestId("fighter-choice-list"),choices=list.locator("button");
  await choices.first().click();
  await list.evaluate(element=>{element.scrollTop=160});
  await page.getByRole("button",{name:"Compare fighter"}).click();
  await choices.nth(2).click();
  await expect(page.getByTestId("fighter-comparison")).toBeVisible();
  await page.setViewportSize({width:844,height:390});
  await expect(page.locator("main.game-shell")).toHaveAttribute("data-viewport","phone-landscape");
  await expect(page.getByTestId("fighter-comparison")).toBeVisible();
  await expect(choices.first()).toHaveAttribute("aria-pressed","true");
  expect(await list.evaluate(element=>element.scrollTop)).toBeGreaterThan(0);
  await page.getByRole("button",{name:"Close fighter comparison"}).click();
  await expect(page.getByTestId("fighter-comparison")).toHaveCount(0);
});

test("every result factor card expands on touch and exposes scientific detail",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await openSelection(page);
  await finishMatch(page,"one");
  await page.getByRole("button",{name:/View Science Breakdown/}).click();
  const modal=page.getByRole("dialog",{name:/Why this organism won/});
  await expect(modal).toBeVisible();
  const factors=modal.locator(".factor-list button");
  const count=await factors.count();
  expect(count).toBeGreaterThan(0);
  for(let index=0;index<count;index+=1){
    const factor=factors.nth(index);
    await factor.click();
    await expect(factor).toHaveAttribute("aria-expanded","true");
    await expect(factor.getByTestId("factor-details")).toContainText("Evidence and uncertainty");
  }
  await expectFixedViewport(page);
  const results=modal.locator(".science-results-scroll");
  const resultMetrics=await results.evaluate(element=>({clientHeight:element.clientHeight,scrollHeight:element.scrollHeight,touchAction:getComputedStyle(element).touchAction}));
  expect(resultMetrics.scrollHeight).toBeGreaterThan(resultMetrics.clientHeight);
  expect(resultMetrics.touchAction).toBe("pan-y");
  const resultsBox=await results.boundingBox();
  expect(resultsBox).not.toBeNull();
  await touchSwipe(page,{x:(resultsBox?.x||0)+(resultsBox?.width||0)/2,y:(resultsBox?.y||0)+(resultsBox?.height||0)-80},{x:(resultsBox?.x||0)+(resultsBox?.width||0)/2,y:(resultsBox?.y||0)+80});
  expect(await results.evaluate(element=>element.scrollTop)).toBeGreaterThan(0);
  expect(await page.evaluate(()=>window.scrollY)).toBe(0);
  await modal.getByRole("button",{name:/Close science breakdown/}).click();
  await expect(modal).toHaveCount(0);
  await expect(page.getByRole("button",{name:/Main menu/})).toBeInViewport();
});

test("corrected APK screens keep required controls and animated records visible",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.goto("/");
  for(const label of ["One player","Two players","Enter the culture","Random Match","Daily Challenge","How to Play","Microbe Lab","Settings"]){
    await expect(page.getByRole("button",{name:new RegExp(label,"i")}).first()).toBeInViewport();
  }
  await openSelection(page);
  await page.locator(".roster-list button:not([disabled])").filter({hasText:/[1-9]\d* BGCs/}).first().click();
  const confirm=page.getByRole("button",{name:"Select Player 1 fighter →"});
  await expect(confirm).toBeInViewport();
  const confirmBox=await confirm.boundingBox();
  expect((confirmBox?.y||0)+(confirmBox?.height||0)).toBeLessThanOrEqual(844);
  await confirm.click();
  await page.getByRole("button",{name:"Lock Player 1 colony →"}).click();
  const records=page.locator(".gene-chain i");
  expect(await records.count()).toBeGreaterThan(0);
  await expect(records.first()).toBeVisible();
  await expect(records.first()).not.toHaveText("");
  await page.getByRole("button",{name:"Confirm Player 1 preparation →"}).click();
  const environment=page.getByTestId("screen-environment");
  await expect(environment.getByRole("button",{name:/Enter this habitat/})).toBeInViewport();
  const overlapping=await environment.locator(".environment-grid button").evaluateAll(cards=>cards.some(card=>{const pieces=Array.from(card.querySelectorAll(":scope > b,:scope > em,:scope > small"));return pieces.some((piece,index)=>pieces.slice(index+1).some(other=>{const a=piece.getBoundingClientRect(),b=other.getBoundingClientRect();return a.bottom>b.top+1&&b.bottom>a.top+1}))}));
  expect(overlapping).toBe(false);
});

for(const device of devices){
  for(const mode of ["one","two"] as const){
    test(`${mode}-player complete flow works on ${device.name}`,async({page})=>{
      await page.setViewportSize({width:device.width,height:device.height});
      await openSelection(page,mode);
      expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(device.width+1);
      await finishMatch(page,mode);
      expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(device.width+1);
    });
  }
}
