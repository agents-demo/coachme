import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("real backend review, label, rate and adjudicate", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Benchmark runs" })).toBeVisible();
  await page.getByRole("link", { name: "Open" }).click();
  await expect(page.getByText("Release status")).toBeVisible();

  await page.getByRole("link", { name: "Review" }).click();
  await expect(page.getByText("Late footwork at contact.")).toBeVisible();
  await expect(page.getByText("ev_1")).toBeVisible();

  await page.goto("/runs/run-1/labels/clip-1");
  await page.locator("#text-0").fill("Updated late footwork at contact");
  await page.getByRole("button", { name: "Save label" }).click();
  await expect(page.getByText("Label saved.")).toBeVisible();

  await page.goto("/runs/run-1/rate");
  await page.getByRole("link", { name: "Rate" }).click();
  await page.locator("#preferred").selectOption("A");
  await page.locator("#rationale").fill("A is more specific.");
  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page.getByText("Draft saved.")).toBeVisible();
  await page.getByRole("button", { name: "Save and submit all" }).click();
  await expect(page.getByText(/Submitted 1 rating/)).toBeVisible();

  await page.goto("/runs/run-1/adjudicate");
  await page.getByRole("link", { name: "Adjudicate" }).click();
  await page.locator("#preferred").selectOption("B");
  await page.locator("#rationale").fill("B is better");
  await page.getByRole("button", { name: "Save decision" }).click();
  await expect(page.getByText("Decision saved.")).toBeVisible();

  await page.goto("/runs/run-1");
  await expect(page.getByRole("link", { name: "score.json" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Download rater packets" })).toBeVisible();
});


test("review screens have no serious accessibility violations", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("coachme.benchmark.labeler", "coach-c"));
  const routes = [
    "/",
    "/runs/run-1",
    "/runs/run-1/clips/clip-1",
    "/runs/run-1/labels/clip-1",
    "/runs/run-1/rate",
    "/runs/run-1/rate/clip-1",
    "/runs/run-1/adjudicate",
    "/runs/run-1/adjudicate/clip-1",
    "/runs/run-1/reviews",
    "/settings",
    "/help",
  ];
  for (const route of routes) {
    await page.goto(route);
    await page.waitForTimeout(400);
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    const serious = results.violations.filter((item) => ["serious", "critical"].includes(item.impact));
    expect(serious, route).toEqual([]);
  }
});


test("theme switch persists and applies light mode", async ({ page }) => {
  await page.goto("/settings");
  await page.locator(".theme-options").getByRole("button", { name: "Light" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.locator(".theme-options").getByRole("button", { name: "Dark" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});
