import { expect, test } from "@playwright/test";

function makeFireEvents(count: number) {
  return Array.from({ length: count }, (_, index) => ({
    lat: 32.6 + (index % 80) * 0.05,
    lon: -124.0 + (index % 80) * 0.05,
    brightness: 300 + (index % 100),
    frp: 5 + (index % 75),
    confidence: index % 2 === 0 ? "high" : "nominal",
    acq_date: "2026-04-14",
    acq_time: String(800 + (index % 900)).padStart(4, "0"),
    risk: 150 + (index % 120),
  }));
}

test.describe("Frontend performance", () => {
  test("loads and filters a larger wildfire dataset within acceptable time", async ({ page }) => {
    const largeDataset = makeFireEvents(1000);

    await page.route("**/fires*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(largeDataset),
      });
    });

    const startLoad = Date.now();
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.getByTestId("events-count")).toBeVisible();
    const loadMs = Date.now() - startLoad;

    expect(loadMs).toBeLessThan(2500);

    const startFilter = Date.now();
    await page.getByTestId("confidence-filter").selectOption("high");
    await expect(page.getByTestId("events-count")).toContainText("events");
    const filterMs = Date.now() - startFilter;

    expect(filterMs).toBeLessThan(2500);
  });
});