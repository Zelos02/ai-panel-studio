import { fireEvent, render, screen } from "@testing-library/react";

import App from "./App";

describe("App", () => {
  it("renders the home dashboard and opens the new topic dialog", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: /别只要答案/ })).toBeInTheDocument();
    expect(screen.getByText("AI 是否应该参与招聘终审？")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /发起新讨论/ }));
    expect(screen.getByRole("dialog", { name: /把一个难题带上圆桌/ })).toBeInTheDocument();
  });

  it("opens a studio view without rendering internal event labels", () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /查看演播厅示例/ }));

    expect(screen.getByRole("heading", { name: "观点现场" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "圆桌成员" })).toBeInTheDocument();
    expect(screen.getByText("一致性是否等于公平")).toBeInTheDocument();
    expect(screen.queryByText("raise_hand")).not.toBeInTheDocument();
    expect(screen.queryByText("transcript.append")).not.toBeInTheDocument();
  });
});
