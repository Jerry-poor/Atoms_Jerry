import { expect, test } from "@playwright/test";

test("Google OAuth (TEST_MODE) -> create run -> view events/artifacts", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByRole("link", { name: "Log in with Google" }).click();

  await page.waitForURL(/\/app(\/.*)?$/);
  await page.goto("/app/runs");
  await expect(page.getByRole("heading", { name: "Runs" })).toBeVisible();

  // Keep e2e fast/deterministic: use the single engineer mode.
  await page.getByRole("button", { name: "Engineer" }).click();

  await page
    .getByPlaceholder("Describe the task to run...")
    .fill("hello world");
  await page.getByRole("button", { name: "Run" }).click();

  await page.waitForURL(/\/app\/runs\/[^/]+$/);
  await expect(page.getByText("Status:")).toBeVisible();
  await expect(page.getByText("Status: succeeded")).toBeVisible({
    timeout: 90_000,
  });

  await expect(page.getByText("跟随智能体的屏幕")).toBeVisible();
  await expect(page.getByText("代码工作区")).toBeVisible();
});

test("Logout blocks protected routes, GitHub OAuth (TEST_MODE) works", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByRole("link", { name: "Log in with GitHub" }).click();

  await page.waitForURL(/\/app(\/.*)?$/);
  await page.goto("/app/runs");
  await expect(page.getByRole("heading", { name: "Runs" })).toBeVisible();
  await page.getByRole("button", { name: "Logout" }).click();
  // After session is cleared, protected routes will redirect to login.
  await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();

  await page.goto("/app/runs");
  await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
});
