import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, ListTree } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Collapsible, CollapsibleContent } from "@/shared/ui/collapsible";
import type { MarkdownHeading } from "@/core/editor/headings";

interface TableOfContentsProps {
  headings: MarkdownHeading[];
  onNavigate: (heading: MarkdownHeading) => void;
}

const HeadingBranch = ({
  heading,
  onNavigate,
}: {
  heading: MarkdownHeading;
  onNavigate: (heading: MarkdownHeading) => void;
}) => {
  const [open, setOpen] = useState(true);
  const hasChildren = heading.children.length > 0;

  return (
    <li>
      <div className="flex min-h-7 items-center gap-0.5">
        {hasChildren ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-6 w-6 shrink-0 text-muted-foreground"
            aria-label={`${open ? "Collapse" : "Expand"} ${heading.text}`}
            aria-expanded={open}
            onClick={() => setOpen((current) => !current)}
          >
            {open ? <ChevronDown /> : <ChevronRight />}
          </Button>
        ) : (
          <span className="w-6 shrink-0" aria-hidden="true" />
        )}
        <Button
          type="button"
          variant="ghost"
          className="h-7 min-w-0 flex-1 justify-start truncate px-1.5 text-left text-xs font-normal"
          onClick={() => onNavigate(heading)}
          title={heading.text}
        >
          <span className="shrink-0 text-[10px] text-muted-foreground">H{heading.level}</span>
          <span className="truncate">{heading.text}</span>
        </Button>
      </div>
      {hasChildren && open && (
        <ul className="ml-3 border-l border-border/50 pl-2">
          {heading.children.map((child) => (
            <HeadingBranch key={child.id} heading={child} onNavigate={onNavigate} />
          ))}
        </ul>
      )}
    </li>
  );
};

export const TableOfContents = ({ headings, onNavigate }: TableOfContentsProps) => {
  const [open, setOpen] = useState(true);

  useEffect(() => {
    if (headings.length === 0) setOpen(false);
  }, [headings.length]);

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="border-b border-border/40 pb-2">
      <Button
        type="button"
        variant="ghost"
        className="h-9 w-full justify-between px-2 text-sm"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        aria-controls="markdown-table-of-contents"
      >
        <span className="flex items-center gap-2">
          <ListTree className="text-muted-foreground" />
          Table of contents
          <span className="text-xs font-normal text-muted-foreground">{headings.length ? "" : "Empty"}</span>
        </span>
        {open ? <ChevronDown /> : <ChevronRight />}
      </Button>
      <CollapsibleContent id="markdown-table-of-contents">
        {headings.length ? (
          <nav aria-label="Table of contents" className="max-h-64 overflow-y-auto py-1 pr-1">
            <ul>
              {headings.map((heading) => (
                <HeadingBranch key={heading.id} heading={heading} onNavigate={onNavigate} />
              ))}
            </ul>
          </nav>
        ) : (
          <p className="px-8 py-2 text-xs text-muted-foreground">Add a heading to create an outline.</p>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
};