import { EditorState, Extension, Compartment } from "@codemirror/state";
import {
  EditorView,
  keymap,
  drawSelection,
  highlightActiveLine,
  lineNumbers,
  placeholder as placeholderExt,
  rectangularSelection,
  crosshairCursor,
} from "@codemirror/view";
import {
  history,
  defaultKeymap,
  historyKeymap,
  indentWithTab,
} from "@codemirror/commands";
import { searchKeymap, highlightSelectionMatches } from "@codemirror/search";
import {
  autocompletion,
  completionKeymap,
  closeBrackets,
  closeBracketsKeymap,
} from "@codemirror/autocomplete";
import { markdown, markdownLanguage } from "@codemirror/lang-markdown";
import { languages } from "@codemirror/language-data";
import {
  bracketMatching,
  foldGutter,
  foldKeymap,
  foldService,
  indentOnInput,
  indentUnit,
} from "@codemirror/language";

import { editorTheme, markdownHighlight } from "./theme";
import { livePreview, sourceHighlighting } from "./extensions/livePreview";
import {
  wikilinkExtension,
  type LinkHandlers,
} from "./extensions/wikilinkField";
import {
  frontmatterField,
  wordCountField,
} from "./extensions/frontmatterField";
import {
  wikilinkCompletion,
  tagCompletion,
  slashCommandCompletion,
  type SuggestSource,
} from "@/core/editor/suggest/suggestions";
import type {
  EditorAppearanceConfig,
  EditorBehaviorConfig,
  EditorSuggestionsConfig,
} from "@/shared/stores/useEditorSettingsStore";
import { FONT_FAMILY_CSS } from "@/shared/stores/useEditorSettingsStore";

export interface EditorSettingsSnapshot {
  appearance: EditorAppearanceConfig;
  behavior: EditorBehaviorConfig;
  suggestions: EditorSuggestionsConfig;
}

export interface EditorSetupOptions {
  mode: "source" | "live";
  placeholder?: string;
  settings: EditorSettingsSnapshot;
  getSuggestSource: () => SuggestSource;
  handlers: LinkHandlers;
  onChange: (value: string) => void;
  onSave?: () => void;
}

/** Font / size / spacing driven by user settings. */
export function appearanceTheme(appearance: EditorAppearanceConfig): Extension {
  return EditorView.theme({
    "&": { fontSize: `${appearance.fontSize}px` },
    ".cm-scroller": {
      fontFamily: FONT_FAMILY_CSS[appearance.fontFamily],
      lineHeight: String(appearance.lineHeight),
    },
    ".cm-content": appearance.limitContentWidth
      ? {
          maxWidth: `${appearance.contentWidth}ch`,
          marginLeft: "auto",
          marginRight: "auto",
        }
      : {},
  });
}

export const appearanceCompartment = new Compartment();

export function createEditorExtensions(
  options: EditorSetupOptions,
): Extension[] {
  const { appearance, behavior, suggestions } = options.settings;

  const overrides = [
    suggestions.wikilinks ? wikilinkCompletion(options.getSuggestSource) : null,
    suggestions.tags ? tagCompletion(options.getSuggestSource) : null,
    suggestions.slashCommands ? slashCommandCompletion() : null,
  ].filter(Boolean) as ReturnType<typeof wikilinkCompletion>[];

  return [
    history(),
    drawSelection(),
    rectangularSelection(),
    crosshairCursor(),
    ...(appearance.showLineNumbers ? [lineNumbers()] : []),
    ...(appearance.highlightActiveLine ? [highlightActiveLine()] : []),
    ...(appearance.highlightSelectionMatches
      ? [highlightSelectionMatches()]
      : []),
    ...(behavior.indentOnInput ? [indentOnInput()] : []),
    ...(behavior.bracketMatching ? [bracketMatching()] : []),
    ...(behavior.autoCloseBrackets ? [closeBrackets()] : []),
    ...(behavior.lineWrapping ? [EditorView.lineWrapping] : []),
    indentUnit.of(" ".repeat(Math.max(1, behavior.indentUnit))),
    EditorState.tabSize.of(Math.max(1, behavior.indentUnit)),
    EditorView.contentAttributes.of({
      spellcheck: behavior.spellcheck ? "true" : "false",
    }),
    placeholderExt(options.placeholder ?? "Start writing..."),
    markdown({
      base: markdownLanguage,
      codeLanguages: languages,
      addKeymap: true,
    }),
    foldService.of((state, lineStart, lineEnd) => {
      const line = state.doc.lineAt(lineStart);
      const match = /^(#{1,6})[\t ]+/.exec(line.text);
      if (!match) return null;
      const level = match[1].length;
      let to = state.doc.length;
      for (let number = line.number + 1; number <= state.doc.lines; number += 1) {
        const next = state.doc.line(number);
        const nextMatch = /^(#{1,6})[\t ]+/.exec(next.text);
        if (nextMatch && nextMatch[1].length <= level) {
          to = Math.max(lineEnd, next.from - 1);
          break;
        }
      }
      return to > lineEnd ? { from: lineEnd, to } : null;
    }),
    foldGutter({ openText: "⌄", closedText: "›" }),
    markdownHighlight,
    editorTheme,
    appearanceCompartment.of(appearanceTheme(appearance)),
    frontmatterField,
    wordCountField,
    ...(suggestions.enabled && overrides.length
      ? [
          autocompletion({
            activateOnTyping: suggestions.activateOnTyping,
            icons: false,
            override: overrides,
          }),
        ]
      : []),
    ...wikilinkExtension(options.handlers),
    ...(options.mode === "live" ? livePreview() : sourceHighlighting()),
    keymap.of([
      {
        key: "Mod-s",
        preventDefault: true,
        run: () => {
          options.onSave?.();
          return true;
        },
      },
      ...(behavior.autoCloseBrackets ? closeBracketsKeymap : []),
      ...completionKeymap,
      ...searchKeymap,
      ...historyKeymap,
      ...foldKeymap,
      ...defaultKeymap,
      ...(behavior.tabIndents ? [indentWithTab] : []),
    ]),
    EditorView.updateListener.of((update) => {
      if (update.docChanged) options.onChange(update.state.doc.toString());
    }),
  ];
}

export function createEditorState(
  doc: string,
  extensions: Extension[],
): EditorState {
  return EditorState.create({ doc, extensions });
}
