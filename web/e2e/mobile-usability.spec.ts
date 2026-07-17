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

async function previewAndConfirm(page:Page,player:1|2,index=0){
  const allChoices=page.locator(".roster-list button"),choices=page.locator(".roster-list button:not([disabled])");
  await expect(allChoices).toHaveCount(10);
  const choice=choices.nth(index);
  await choice.click();
  await expect(page.getByTestId("screen-fighter")).toBeVisible();
  await page.getByRole("button",{name:`Select Player ${player} fighter →`}).first().click();
}

async function preparePlayer(page:Page,player:1|2){
  await page.getByRole("button",{name:`Lock Player ${player} colony →`}).click();
  await page.getByRole("button",{name:`Confirm Player ${player} preparation →`}).click();
}

async function finishMatch(page:Page,mode:"one"|"two"){
  await previewAndConfirm(page,1,0);
  if(mode==="two")await previewAndConfirm(page,2,0);
  await preparePlayer(page,1);
  if(mode==="two")await preparePlayer(page,2);
  await page.getByRole("button",{name:"Enter this habitat →"}).click();
  await page.getByRole("button",{name:"Enter the microscopic arena →"}).click();
  const skip=page.getByRole("button",{name:"Skip battle →"});
  if(await skip.isVisible())await skip.click();
  await expect(page.getByTestId("screen-results")).toBeVisible({timeout:15_000});
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
  const first=choices.first();
  await first.click();
  await expect(first).toHaveAttribute("aria-pressed","true");
  await first.click();
  await expect(page.getByTestId("screen-fighter")).toBeVisible();
  await page.getByRole("button",{name:"Select Player 1 fighter →"}).click();
  await expect(page.getByTestId("screen-colony")).toBeVisible();
});

test("comparison keeps preview and comparison fighters separate until explicit selection",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await openSelection(page);
  const choices=page.locator(".roster-list button");
  await expect(choices).toHaveCount(10);
  await choices.first().click();
  const previewName=await choices.first().getAttribute("data-fighter-name");
  await page.getByRole("button",{name:"Compare fighter"}).click();
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
  await choices.nth(2).click();
  await expect(choices.first()).toHaveAttribute("aria-pressed","true");
  await expect(page.getByTestId("screen-fighter")).toBeVisible();
  await panel.getByRole("button",{name:"Cancel comparison"}).click();
  await expect(panel).toHaveCount(0);
  await page.getByRole("button",{name:"Compare fighter"}).click();
  await page.getByTestId("fighter-comparison").getByRole("button",{name:"Select Player 1 fighter →"}).click();
  await expect(page.getByTestId("screen-colony")).toBeVisible();
});

test("every result factor card expands on touch and exposes scientific detail",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await openSelection(page);
  await finishMatch(page,"one");
  const factors=page.locator(".factor-list button");
  const count=await factors.count();
  expect(count).toBeGreaterThan(0);
  for(let index=0;index<count;index+=1){
    const factor=factors.nth(index);
    await factor.click();
    await expect(factor).toHaveAttribute("aria-expanded","true");
    await expect(factor.getByTestId("factor-details")).toContainText("Evidence and uncertainty");
  }
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
