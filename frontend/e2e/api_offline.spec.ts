import { expect, test } from "@playwright/test";

test.describe("AI Wildfire Tracker API offline recovery", () => {
  test("falls back safely to 0 events when backend is unavailable", async ({ page }) => {
    await page.route("**/fires**", async (route) => {
      await route.abort("failed");
    });

    await page.goto("/", { waitUntil: "domcontentloaded" });

    await expect(page.getByTestId("events-count")).toHaveText("0 events");
    await expect(page.getByTestId("event-row")).toHaveCount(0);
    await expect(page.getByText(/AI Wildfire Tracker/i)).toBeVisible();
  });
});