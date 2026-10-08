import { expect, test } from "@playwright/test";

test("completes and restores a full AI panel session", async ({ page }) => {
  const title = `E2E 圆桌：AI 决策边界 ${Date.now()}`;
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /别只要答案/ })).toBeVisible();

  await page.getByRole("button", { name: /发起新讨论/ }).click();
  await page.getByLabel("讨论主题").fill(title);
  await page.getByLabel("专家人数").selectOption("3");
  await page.getByLabel("讨论目标").fill("形成可审计、可执行的人机决策边界");
  await page.getByLabel("背景说明（可选）").fill("公司正在评估 AI 是否可以参与高风险终审。");
  await page.getByRole("button", { name: /生成专家阵容/ }).click();

  await expect(page.getByRole("heading", { name: /嘉宾已经就位/ })).toBeVisible();
  await expect(page.locator(".cast-card")).toHaveCount(4);
  await page.getByRole("button", { name: /确认入场并创建演播厅/ }).click();

  await expect(page.getByRole("heading", { name: "观点现场" })).toBeVisible();
  await page.getByRole("button", { name: "启动讨论" }).click();
  await expect(page.getByText("讨论已结束")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "本场讨论总结" })).toBeVisible();
  await expect(page.getByText("如何验证关键假设")).toBeVisible();
  expect(await page.locator(".message").count()).toBeGreaterThan(4);
  await expect(page.locator(".summary-panel p")).not.toContainText("{");

  const transcriptBox = await page.locator(".transcript-panel").boundingBox();
  const summaryBox = await page.locator(".summary-panel").boundingBox();
  const gridBox = await page.locator(".studio-grid").boundingBox();
  expect(transcriptBox?.height ?? 0).toBeGreaterThan(250);
  expect((summaryBox?.y ?? 0) + (summaryBox?.height ?? 9999)).toBeLessThanOrEqual(
    (gridBox?.y ?? 0) + (gridBox?.height ?? 0) + 1,
  );
  const summaryOverflow = await page.locator(".summary-panel__scroll").evaluate((element) => {
    const paragraph = element.querySelector("p");
    if (paragraph) paragraph.textContent = `${paragraph.textContent}\n\n`.repeat(30);
    return { clientHeight: element.clientHeight, scrollHeight: element.scrollHeight };
  });
  expect(summaryOverflow.scrollHeight).toBeGreaterThan(summaryOverflow.clientHeight);

  await page.locator(".brand-button").click();
  const topicCard = page.locator(".topic-card").filter({ hasText: title });
  await expect(topicCard).toBeVisible();
  await topicCard.getByRole("button", { name: "查看复盘" }).click();

  await expect(page.getByRole("heading", { name: "本场讨论总结" })).toBeVisible();
  await expect(page.getByText("如何验证关键假设")).toBeVisible();
});

test("shows a safe retryable message when panel generation fails", async ({ page }) => {
  await page.route("**/api/v1/topics/*/panel:generate", async (route) => {
    await route.fulfill({
      status: 504,
      contentType: "application/json",
      body: JSON.stringify({ error: { code: "LLM_TIMEOUT", message: "生成专家阵容超时，请重试。", requestId: "e2e", retryable: true, details: {} } }),
    });
  });
  await page.goto("/");
  await page.getByRole("button", { name: /发起新讨论/ }).click();
  await page.getByLabel("讨论主题").fill(`异常恢复测试 ${Date.now()}`);
  await page.getByRole("button", { name: /生成专家阵容/ }).click();

  const alert = page.getByRole("alert");
  await expect(alert).toContainText("生成专家阵容超时，请重试");
  await expect(alert).not.toContainText("Traceback");
  await expect(alert).not.toContainText("LLM_API_KEY");
});

test("keeps the mobile home and dialog within the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /别只要答案/ })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);

  await page.getByRole("button", { name: /发起新讨论/ }).click();
  await expect(page.getByRole("dialog", { name: /把一个难题带上圆桌/ })).toBeVisible();
  const dialogBox = await page.getByRole("dialog").boundingBox();
  expect(dialogBox?.x ?? -1).toBeGreaterThanOrEqual(0);
  expect((dialogBox?.x ?? 0) + (dialogBox?.width ?? 999)).toBeLessThanOrEqual(390);
});

test("edits and deletes an unstarted discussion from management", async ({ page }) => {
  const title = `E2E 管理讨论 ${Date.now()}`;
  await page.goto("/");
  await page.getByRole("button", { name: /发起新讨论/ }).click();
  await page.getByLabel("讨论主题").fill(title);
  await page.getByLabel("专家人数").selectOption("2");
  await page.getByRole("button", { name: /生成专家阵容/ }).click();
  await expect(page.getByRole("heading", { name: /嘉宾已经就位/ })).toBeVisible();
  await page.locator(".brand-button").click();

  const card = page.locator(".topic-card").filter({ hasText: title });
  await card.getByRole("button", { name: `管理讨论：${title}` }).click();
  const dialog = page.getByRole("dialog", { name: "管理讨论" });
  const hostCard = dialog.locator(".manager-member").first();
  await hostCard.getByLabel("姓名").fill("编辑后的主持人");
  await dialog.getByRole("button", { name: "保存阵容修改" }).click();
  await expect(dialog.getByText("版本 #2")).toBeVisible();

  await dialog.getByRole("button", { name: "删除这场讨论" }).click();
  await expect(dialog.getByText("请再次确认")).toBeVisible();
  await dialog.getByRole("button", { name: "确认永久删除" }).click();
  await expect(page.locator(".topic-card").filter({ hasText: title })).toHaveCount(0);
});
