"use client";

import CodeMirror from "@uiw/react-codemirror";
import { css } from "@codemirror/lang-css";
import { html } from "@codemirror/lang-html";
import { javascript } from "@codemirror/lang-javascript";
import { json as jsonLang } from "@codemirror/lang-json";
import { markdown } from "@codemirror/lang-markdown";
import { python } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";

function guessLanguage(path: string) {
  const p = (path || "").toLowerCase();
  if (p.endsWith(".json")) return jsonLang();
  if (p.endsWith(".js") || p.endsWith(".jsx")) return javascript({ jsx: true });
  if (p.endsWith(".ts") || p.endsWith(".tsx")) return javascript({ typescript: true, jsx: true });
  if (p.endsWith(".html") || p.endsWith(".htm")) return html();
  if (p.endsWith(".css")) return css();
  if (p.endsWith(".md") || p.endsWith(".markdown")) return markdown();
  if (p.endsWith(".py")) return python();
  return null;
}

export function CodeEditor({
  value,
  path,
  onChange,
  readOnly = false,
  height = 560,
}: {
  value: string;
  path: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  height?: number;
}) {
  const lang = guessLanguage(path);
  const extensions = lang ? [lang] : [];

  return (
    <div className="h-full overflow-hidden rounded-xl border bg-[#0b1020]">
      <CodeMirror
        value={value}
        theme={oneDark}
        extensions={extensions}
        height={`${height}px`}
        basicSetup={{
          lineNumbers: true,
          highlightActiveLine: true,
          highlightActiveLineGutter: true,
          foldGutter: true,
          bracketMatching: true,
          closeBrackets: true,
          autocompletion: true,
          history: true,
          searchKeymap: true,
          defaultKeymap: true,
        }}
        editable={!readOnly}
        onChange={(v) => onChange?.(v)}
      />
    </div>
  );
}

