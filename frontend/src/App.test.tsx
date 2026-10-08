import { render, screen } from "@testing-library/react";

import App from "./App";

describe("App", () => {
  it("renders the product identity", () => {
    render(<App />);

    expect(screen.getByText("AI PANEL STUDIO")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /让观点/ })).toBeInTheDocument();
  });
});
