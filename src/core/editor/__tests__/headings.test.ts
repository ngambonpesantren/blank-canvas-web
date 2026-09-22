import { describe, expect, it } from "vitest";
import { flattenHeadings, parseMarkdownHeadings } from "@/core/editor/headings";

describe("parseMarkdownHeadings", () => {
  it("builds a nested H1-H6 outline and section boundaries", () => {
    const source = [
      "# Root",
      "intro",
      "## Child",
      "child body",
      "#### Deep",
      "deep body",
      "# Next",
      "end",
    ].join("\n");
    const roots = parseMarkdownHeadings(source);
    const flat = flattenHeadings(roots);

    expect(roots.map((heading) => heading.text)).toEqual(["Root", "Next"]);
    expect(roots[0].children[0].text).toBe("Child");
    expect(roots[0].children[0].children[0].level).toBe(4);
    expect(source.slice(flat[0].contentFrom, flat[0].sectionTo)).toContain("deep body");
    expect(source.slice(flat[1].contentFrom, flat[1].sectionTo)).not.toContain("# Next");
  });

  it("creates unique stable anchors for repeated heading labels", () => {
    const flat = flattenHeadings(parseMarkdownHeadings("# Same\n## Same\n# Same"));
    expect(flat.map((heading) => heading.id)).toEqual(["same", "same-2", "same-3"]);
  });

  it("recognizes all six heading levels", () => {
    const source = Array.from({ length: 6 }, (_, index) => `${"#".repeat(index + 1)} H${index + 1}`).join("\n");
    expect(flattenHeadings(parseMarkdownHeadings(source)).map((heading) => heading.level)).toEqual([1, 2, 3, 4, 5, 6]);
  });
});