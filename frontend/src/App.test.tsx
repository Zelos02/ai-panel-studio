import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const topic = {
  id: "topic-1",
  title: "AI 是否应该参与招聘终审？",
  background: "效率与公平的取舍",
  goal: "明确责任边界",
  requestedExpertCount: 2,
  panelGeneration: 1,
  status: "draft",
  createdAt: "2026-10-08T04:00:00Z",
  updatedAt: "2026-10-08T04:00:00Z",
};

const host = { id: "host-1", topicId: "topic-1", kind: "host", name: "周岚", title: "科技记者", stance: "保持中立", publicProfile: "检验论据", color: "#69E4CE", displayOrder: 0, admitted: false };
const experts = [
  { id: "expert-1", topicId: "topic-1", kind: "expert", name: "林澈", title: "研究员", stance: "关注公平", publicProfile: "偏差审计", color: "#B49CFF", displayOrder: 1, admitted: false },
  { id: "expert-2", topicId: "topic-1", kind: "expert", name: "许珂", title: "产品负责人", stance: "关注效率", publicProfile: "流程一致性", color: "#F6C177", displayOrder: 2, admitted: false },
];
const panel = { topicId: "topic-1", generation: 1, host, experts };

function jsonResponse(data: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } }));
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn((input: string | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/topics") && !init?.method) return jsonResponse({ items: [topic], nextCursor: null });
    if (url.endsWith("/experts")) return jsonResponse(panel);
    if (url.endsWith("/panel") && init?.method === "PUT") {
      const body = JSON.parse(String(init.body));
      return jsonResponse({ ...panel, generation: 2, host: { ...host, ...body.host } });
    }
    if (url.endsWith("/topics/topic-1") && init?.method === "DELETE") return Promise.resolve(new Response(null, { status: 204 }));
    if (url.endsWith("/panel:admit")) return jsonResponse({ ...panel, host: { ...host, admitted: true }, experts: experts.map((item) => ({ ...item, admitted: true })) });
    if (url.endsWith("/sessions") && !init?.method) return jsonResponse({ items: [] });
    if (url.endsWith("/sessions") && init?.method === "POST") return jsonResponse({ id: "session-1", topicId: "topic-1", status: "admitted", turnCount: 0, maxTurns: 18, lastEventSequence: 0, createdAt: "2026-10-08T04:10:00Z", startedAt: null, endedAt: null }, 201);
    return jsonResponse({ error: { code: "NOT_FOUND", message: "not found" } }, 404);
  }));
});

afterEach(() => vi.unstubAllGlobals());

describe("App", () => {
  it("loads topics and opens the create dialog", async () => {
    render(<App />);
    expect(await screen.findByText(topic.title)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /发起新讨论/ }));
    expect(screen.getByRole("dialog", { name: /把一个难题带上圆桌/ })).toBeInTheDocument();
  });

  it("confirms the latest panel and creates a ready studio", async () => {
    render(<App />);
    await screen.findByText(topic.title);
    fireEvent.click(screen.getByRole("button", { name: "进入演播厅" }));

    expect(await screen.findByRole("heading", { name: /嘉宾已经就位/ })).toBeInTheDocument();
    expect(screen.getByText("林澈")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /确认入场并创建演播厅/ }));

    expect(await screen.findByRole("heading", { name: "观点现场" })).toBeInTheDocument();
    expect(screen.getByText("阵容已经就位")).toBeInTheDocument();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/panel:admit"), expect.objectContaining({ method: "PUT" })));
    expect(screen.queryByText("raise_hand")).not.toBeInTheDocument();
  });

  it("edits an unstarted panel and requires two steps to delete a discussion", async () => {
    render(<App />);
    await screen.findByText(topic.title);
    fireEvent.click(screen.getByRole("button", { name: `管理讨论：${topic.title}` }));

    const dialog = await screen.findByRole("dialog", { name: "管理讨论" });
    const nameInputs = await within(dialog).findAllByLabelText("姓名");
    fireEvent.change(nameInputs[0], { target: { value: "新主持人" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "保存阵容修改" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/panel"),
      expect.objectContaining({ method: "PUT" }),
    ));

    fireEvent.click(within(dialog).getByRole("button", { name: "删除这场讨论" }));
    expect(within(dialog).getByText("请再次确认")).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole("button", { name: "确认永久删除" }));
    await waitFor(() => expect(screen.queryByText(topic.title)).not.toBeInTheDocument());
  });
});
