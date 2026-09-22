export interface MarkdownHeading {
  id: string;
  text: string;
  level: number;
  from: number;
  headingEnd: number;
  contentFrom: number;
  sectionTo: number;
  children: MarkdownHeading[];
}

interface FlatHeading extends Omit<MarkdownHeading, "children"> {
  children: MarkdownHeading[];
}

const headingPattern = /^(#{1,6})[\t ]+(.+?)[\t ]*#*[\t ]*$/gm;

export const headingSlug = (text: string): string =>
  text
    .toLowerCase()
    .replace(/[`*_~[\]()<>{}]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "") || "section";

export function parseMarkdownHeadings(markdown: string): MarkdownHeading[] {
  const matches = Array.from(markdown.matchAll(headingPattern));
  const slugCounts = new Map<string, number>();
  const flat: FlatHeading[] = matches.map((match, index) => {
    const text = match[2]?.trim() || "Untitled section";
    const base = headingSlug(text);
    const count = slugCounts.get(base) ?? 0;
    slugCounts.set(base, count + 1);
    const from = match.index ?? 0;
    const headingEnd = from + match[0].length;
    const level = match[1]?.length ?? 1;
    let sectionTo = markdown.length;

    for (let next = index + 1; next < matches.length; next += 1) {
      const nextLevel = matches[next][1]?.length ?? 1;
      if (nextLevel <= level) {
        sectionTo = matches[next].index ?? markdown.length;
        break;
      }
    }

    return {
      id: count === 0 ? base : `${base}-${count + 1}`,
      text,
      level,
      from,
      headingEnd,
      contentFrom: markdown[headingEnd] === "\n" ? headingEnd + 1 : headingEnd,
      sectionTo,
      children: [],
    };
  });

  const roots: MarkdownHeading[] = [];
  const stack: MarkdownHeading[] = [];
  flat.forEach((heading) => {
    while (stack.length && (stack.at(-1)?.level ?? 0) >= heading.level) {
      stack.pop();
    }
    const parent = stack.at(-1);
    if (parent) parent.children.push(heading);
    else roots.push(heading);
    stack.push(heading);
  });
  return roots;
}

export function flattenHeadings(headings: MarkdownHeading[]): MarkdownHeading[] {
  return headings.flatMap((heading) => [heading, ...flattenHeadings(heading.children)]);
}