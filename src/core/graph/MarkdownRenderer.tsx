import { useMemo, useState } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import rehypeRaw from 'rehype-raw';
import { ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/shared/lib";
import { Button } from "@/shared/ui/button";
import {
  flattenHeadings,
  parseMarkdownHeadings,
  type MarkdownHeading,
} from "@/core/editor/headings";

interface MarkdownRendererProps {
  content: string;
  onWikilinkClick?: (target: string) => void;
  onTagClick?: (tag: string) => void;
  className?: string;
}

export const MarkdownRenderer = ({ 
  content, 
  onWikilinkClick,
  onTagClick,
  className 
}: MarkdownRendererProps) => {
  const headingTree = useMemo(() => parseMarkdownHeadings(content), [content]);
  const headings = useMemo(() => flattenHeadings(headingTree), [headingTree]);
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());

  const visibleContent = useMemo(() => {
    const ranges = headings
      .filter((heading) => collapsed.has(heading.id) && heading.sectionTo > heading.contentFrom)
      .map((heading) => ({ from: heading.contentFrom, to: heading.sectionTo }))
      .sort((a, b) => b.from - a.from);
    return ranges.reduce(
      (markdown, range) => `${markdown.slice(0, range.from)}${markdown.slice(range.to)}`,
      content,
    );
  }, [collapsed, content, headings]);
  
  // Process wikilinks
  const processedContent = visibleContent.replace(
    /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
    (match, target, alias) => {
      const displayText = alias || target;
      return `<span class="wikilink" data-target="${target.trim()}">${displayText}</span>`;
    }
  );

  // Process tags
  const processedWithTags = processedContent.replace(
    /#([\w-]+)/g,
    (match, tag) => {
      return `<span class="hashtag" data-tag="${tag}">${match}</span>`;
    }
  );

  const handleClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    
    // Handle wikilink clicks
    if (target.classList.contains('wikilink')) {
      e.preventDefault();
      const linkTarget = target.getAttribute('data-target');
      if (linkTarget && onWikilinkClick) {
        onWikilinkClick(linkTarget);
      }
    }
    
    // Handle tag clicks
    if (target.classList.contains('hashtag')) {
      e.preventDefault();
      const tag = target.getAttribute('data-tag');
      if (tag && onTagClick) {
        onTagClick(tag);
      }
    }
  };

  const visibleHeadings = useMemo(
    () => flattenHeadings(parseMarkdownHeadings(visibleContent)),
    [visibleContent],
  );
  let headingIndex = 0;
  const renderHeading = (level: number) => {
    const HeadingTag = `h${level}` as keyof JSX.IntrinsicElements;
    return ({ children }: { children?: React.ReactNode }) => {
      const visibleHeading = visibleHeadings[headingIndex];
      headingIndex += 1;
      const original = visibleHeading
        ? headings.find(
            (heading) =>
              heading.level === visibleHeading.level &&
              heading.text === visibleHeading.text &&
              heading.from <= visibleHeading.from,
          ) ?? visibleHeading
        : undefined;
      const id = original?.id ?? visibleHeading?.id;
      const canCollapse = Boolean(original && original.sectionTo > original.contentFrom);
      const isCollapsed = Boolean(id && collapsed.has(id));

      return (
        <HeadingTag id={id} data-heading-id={id}>
          {canCollapse ? (
            <Button
              type="button"
              variant="ghost"
              className="group/heading h-auto w-full justify-start whitespace-normal px-0 py-0 text-left font-inherit"
              aria-expanded={!isCollapsed}
              aria-label={`${isCollapsed ? "Expand" : "Collapse"} ${original?.text}`}
              onClick={() => {
                if (!id) return;
                setCollapsed((current) => {
                  const next = new Set(current);
                  if (next.has(id)) next.delete(id);
                  else next.add(id);
                  return next;
                });
              }}
            >
              {isCollapsed ? (
                <ChevronRight className="mr-1 text-muted-foreground" />
              ) : (
                <ChevronDown className="mr-1 text-muted-foreground" />
              )}
              <span>{children}</span>
            </Button>
          ) : (
            children
          )}
        </HeadingTag>
      );
    };
  };

  return (
    <div 
      className={cn("prose prose-sm dark:prose-invert max-w-none", className)}
      onClick={handleClick}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        rehypePlugins={[rehypeRaw]}
        components={{
          h1: renderHeading(1),
          h2: renderHeading(2),
          h3: renderHeading(3),
          h4: renderHeading(4),
          h5: renderHeading(5),
          h6: renderHeading(6),
          // Custom checkbox rendering
          input: ({ node, ...props }) => {
            if (props.type === 'checkbox') {
              return (
                <input
                  {...props}
                  className="mr-2 rounded border-border"
                  disabled
                />
              );
            }
            return <input {...props} />;
          },
          // Custom link rendering
          a: ({ node, ...props }) => (
            <a 
              {...props} 
              className="text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            />
          ),
          // Custom code block rendering
          code: ({ node, className, children, ...props }) => {
            const isInline = !className?.includes('language-');
            return isInline ? (
              <code {...props} className="bg-muted px-1.5 py-0.5 rounded text-sm">
                {children}
              </code>
            ) : (
              <code {...props} className="block bg-muted p-4 rounded-lg overflow-x-auto">
                {children}
              </code>
            );
          },
        }}
      >
        {processedWithTags}
      </ReactMarkdown>
    </div>
  );
};
