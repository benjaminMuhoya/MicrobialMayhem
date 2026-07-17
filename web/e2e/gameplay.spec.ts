import { expect, test, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  page.on("pageerror", error => { throw error; });
  page.on("console", message => { if (message.type() === "error") throw new Error(message.text()); });
});

async function enterCulture(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Enter the culture →" }).click();
  await expect(page.getByTestId("screen-fighter")).toBeVisible();
}

async function chooseVisibleFighter(page: Page, player: 1 | 2) {
  const choices = page.locator(".roster-list button:not([disabled])");
  await expect(choices.first()).toBeVisible();
  await choices.first().click();
  await page.getByRole("button", { name: `Select Player ${player} fighter →` }).click();
}

async function setupPlayer(page: Page, player: 1 | 2) {
  await page.getByRole("button", { name: `Lock Player ${player} colony →` }).click();
  await page.getByRole("button", { name: `Confirm Player ${player} preparation →` }).click();
}

test("production roster reshuffles, searches, and opens Biology Details", async ({ page }) => {
  await enterCulture(page);
  const cards = page.locator(".roster-list button");
  await expect(cards.first()).toBeVisible();
  const before = await cards.allTextContents();
  await page.getByRole("button", { name: "Show different bacteria" }).click();
  await expect.poll(async () => await cards.allTextContents()).not.toEqual(before);
  const search = page.getByRole("textbox", { name: "Search bacterial fighters" });
  await search.fill("Bacillus");
  await expect(page.locator(".search-status")).toContainText("Found");
  await cards.first().click();
  await page.getByRole("button", { name: "Biology details" }).click();
  await expect(page.getByRole("dialog")).toContainText("Recorded biological evidence");
  await page.getByRole("button", { name: "Close biology details" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await search.fill("not-a-real-microbe");
  await expect(page.locator(".search-status")).toContainText("database went quiet");
});

test("one-player completes automatically and supports rematch and menu actions", async ({ page }) => {
  await enterCulture(page);
  await chooseVisibleFighter(page, 1);
  await setupPlayer(page, 1);
  const coldArena = page.getByRole("option", { name: /Cold/ });
  await coldArena.click();
  await expect(coldArena).toHaveAttribute("aria-selected", "true");
  await page.getByRole("button", { name: "Enter this habitat →" }).click();
  await expect(page.getByText("Automated Rival", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Enter the microscopic arena →" }).click();
  await expect(page.getByTestId("screen-results")).toBeVisible({ timeout: 22_000 });
  await expect(page.getByText("Automated Rival", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Scientific breakdown" }).click();
  await expect(page.getByText("Biological interpretation")).toBeVisible();
  await page.getByRole("button", { name: /Rematch/ }).click();
  await expect(page.getByTestId("screen-arena")).toBeVisible();
  await page.getByRole("button", { name: "Skip battle →" }).click();
  await expect(page.getByTestId("screen-results")).toBeVisible();
  await page.getByRole("button", { name: "Change fighters" }).click();
  await expect(page.getByText("Player 1 · specimen selection")).toBeVisible();
});

test("two-player locks distinct fighters and completes both independent setups", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Two players/ }).click();
  await page.getByRole("button", { name: "Enter the culture →" }).click();
  await expect(page.getByTestId("screen-fighter")).toBeVisible();
  await chooseVisibleFighter(page, 1);
  await expect(page.locator(".roster-list button[disabled]")).toHaveCount(1);
  await chooseVisibleFighter(page, 2);
  await setupPlayer(page, 1);
  await setupPlayer(page, 2);
  await expect(page.getByTestId("screen-environment")).toBeVisible();
  await page.getByRole("button", { name: "Enter this habitat →" }).click();
  await expect(page.getByText("Player 2", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Enter the microscopic arena →" }).click();
  await page.getByRole("button", { name: "Pause battle" }).click();
  await expect(page.getByRole("dialog", { name: "Battle paused" })).toBeVisible();
  await page.getByRole("switch", { name: /Sound effects/ }).click();
  await page.getByRole("button", { name: /Resume culture/ }).click();
  await page.getByRole("button", { name: "Skip battle →" }).click();
  await expect(page.getByTestId("screen-results")).toBeVisible();
  await expect(page.getByText("Player 2", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Main menu" }).click();
  await expect(page.getByTestId("screen-home")).toBeVisible();
});
