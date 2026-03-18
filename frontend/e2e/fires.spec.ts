import { expect, test } from "@playwright/test";

test.describe("AI Wildfire Tracker E2E", () => {
  test("loads with seeded California results and no API error", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await expect(page.getByTestId("events-count")).toHaveText("3 events");
    await expect(page.locator(".error-banner")).toHaveCount(0);
  });

  test("starts with California-only filter enabled", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await expect(page.getByTestId("ca-toggle")).toBeChecked();
    await expect(page.getByTestId("events-count")).toHaveText("3 events");
    await expect(page.getByText("Lat/Lon: 31.00, -100.00")).toHaveCount(0);
  });

  test("expands result set when California-only is turned off", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await expect(page.getByTestId("events-count")).toHaveText("3 events");
    await page.getByTestId("ca-toggle").uncheck();
    await expect(page.getByTestId("ca-toggle")).not.toBeChecked();
    await expect(page.getByTestId("events-count")).toHaveText("5 events");
    await expect(page.getByText("Lat/Lon: 31.00, -100.00")).toBeVisible();
  });

  test("applies confidence filter and FRP ascending sort", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await page.getByTestId("ca-toggle").uncheck();
    await expect(page.getByTestId("ca-toggle")).not.toBeChecked();
    await expect(page.getByTestId("events-count")).toHaveText("5 events");

    await page.getByTestId("confidence-filter").selectOption("high");
    await expect(page.getByTestId("events-count")).toHaveText("2 events");

    await page.getByTestId("sort-key").selectOption("frp");
    await page.getByTestId("sort-dir").click();

    const firstRow = page.getByTestId("event-row").first();
    await expect(firstRow).toContainText("FRP: 35");
  });

  test("shows empty-state message when brightness excludes all events", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await page.getByTestId("brightness-filter").fill("999");

    await expect(page.getByText("No events match filters.")).toBeVisible();
    await expect(page.getByTestId("events-count")).toHaveText("0 events");
  });
});
