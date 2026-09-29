import { expect, test } from "@playwright/test";

const shots = "/opt/cursor/artifacts/screenshots";

test("queues messages, then unfolds and expands the chain", async ({ page }) => {
  await page.goto("/?demo=1");
  await expect(page.getByRole("heading", { name: "What's the play?" })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "causal chain" })).toHaveCount(0);
  await page.screenshot({ path: `${shots}/01-chat-folded.png` });

  await page.getByLabel("Message").fill("The Strait of Hormuz is going to open next week.");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByText("Creating a case")).toBeVisible();
  await expect(page.getByText("Saving both ends")).toHaveCount(0);
  await page.screenshot({ path: `${shots}/02-message-queued.png` });

  const panel = page.getByRole("complementary", { name: "causal chain" });
  await expect(panel).toBeVisible();
  await expect(panel.getByText("naval interdiction")).toBeVisible();
  await page.screenshot({ path: `${shots}/03-panel-unfolded.png` });

  await panel.getByRole("button", { name: /Diplomatic talks/ }).click();
  const agreement = panel.locator("[data-situation-id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1']");
  await expect(agreement).toHaveAttribute("data-open", "true");
  await expect(agreement.locator(".node-detail")).toContainText("coast guards");
  await page.screenshot({ path: `${shots}/04-situation-card.png` });

  await panel.getByRole("button", { name: "Open link 0.4200" }).click();
  await expect(panel.getByText("talks_hold")).toBeVisible();
  await expect(panel.locator(".edge-card.is-open")).toBeVisible();
  await page.screenshot({ path: `${shots}/05-edge-card.png` });

  await page.getByRole("button", { name: "causal_chains://chain" }).click();
  const start = panel.locator("[data-situation-id='99b353e5-0f01-4fcc-b78e-89b1b4233f46']");
  await expect(start).toHaveAttribute("data-open", "true");
});
