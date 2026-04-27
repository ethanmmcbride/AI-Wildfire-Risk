import { expect, test } from "@playwright/test";

test.describe("AI Wildfire Tracker E2E", () => {
  test("loads with seeded California results and no API error", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });

    await expect(page.getByText("Loading...")).toHaveCount(0);
    await expect(page.getByTestId("events-count")).toHaveText("3 events", {
      timeout: 10000,
    });
    await expect(page.locator(".error-banner")).toHaveCount(0);
  });

  test("starts with California region selected by default", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await expect(page.getByTestId("region-filter")).toHaveValue("ca");
    await expect(page.getByTestId("events-count")).toHaveText("3 events");
    await expect(page.getByText("Lat/Lon: 31.00, -100.00")).toHaveCount(0);
  });

  test("expands result set when region is changed to All US", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await expect(page.getByTestId("events-count")).toHaveText("3 events");
    await page.getByTestId("region-filter").selectOption("us");
    await expect(page.getByTestId("region-filter")).toHaveValue("us");
    await expect(page.getByTestId("events-count")).toHaveText("5 events");
    await expect(page.getByText("Lat/Lon: 31.00, -100.00")).toBeVisible();
  });

  test("applies confidence filter and FRP ascending sort", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await page.getByTestId("region-filter").selectOption("us");
    await expect(page.getByTestId("region-filter")).toHaveValue("us");
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

  test("keeps event count consistent with visible event rows after filters", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await page.getByTestId("region-filter").selectOption("us");
    await expect(page.getByTestId("events-count")).toHaveText("5 events");

    await expect(page.getByTestId("event-row")).toHaveCount(5);

    await page.getByTestId("confidence-filter").selectOption("high");
    await expect(page.getByTestId("events-count")).toHaveText("2 events");
    await expect(page.getByTestId("event-row")).toHaveCount(2);
  });

  test("heatmap toggle is visible and enabled by default", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.getByTestId("heatmap-toggle")).toBeVisible();
    await expect(page.getByTestId("heatmap-toggle")).toBeChecked();
  });

  test("shows stale-data banner when fire records are old", async ({ page }) => {
    await page.route("**/fires*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            lat: 34.05,
            lon: -118.25,
            brightness: 360,
            frp: 55,
            confidence: "high",
            acq_date: "2020-01-01",
            acq_time: "1210",
            risk: 238,
          },
        ]),
      });
    });

    await page.goto("/", { waitUntil: "domcontentloaded" });

    await expect(page.getByTestId("stale-data-banner")).toBeVisible();
    await expect(page.getByTestId("stale-data-banner")).toContainText(/stale/i);
  });
});
