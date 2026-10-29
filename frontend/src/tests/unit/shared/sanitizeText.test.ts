import { describe, it, expect } from "vitest";
import { sanitizeText } from "@/shared/lib/sanitizeText";

describe("sanitizeText", () => {
  it("strips HTML tags from text", () => {
    expect(sanitizeText("<b>bold</b>")).toBe("bold");
  });

  it("strips script tags", () => {
    expect(sanitizeText('<script>alert("xss")</script>')).toBe(
      'alert("xss")',
    );
  });

  it("strips nested tags", () => {
    expect(sanitizeText("<div><p>hello</p></div>")).toBe("hello");
  });

  it("returns plain text unchanged", () => {
    expect(sanitizeText("Hello, world!")).toBe("Hello, world!");
  });

  it("preserves text between tags", () => {
    expect(sanitizeText("Hello <b>world</b> today")).toBe(
      "Hello world today",
    );
  });

  it("handles empty string", () => {
    expect(sanitizeText("")).toBe("");
  });

  it("handles self-closing tags", () => {
    expect(sanitizeText("Hello<br/>World")).toBe("HelloWorld");
  });
});
