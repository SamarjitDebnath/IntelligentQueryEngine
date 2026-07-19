import ReactMarkdown from "react-markdown";

// LLM-authored free text (answers, plan summaries) sometimes comes back with markdown
// (**bold**, bullet lists) even though the prompt asks for plain prose. Rendering it
// properly here — instead of dumping the raw string into a <p> — is more robust than
// trying to prompt the formatting away entirely.
interface Props {
  text: string;
  className?: string;
}

export function MarkdownText({ text, className }: Props) {
  return (
    <div className={`markdown-text${className ? ` ${className}` : ""}`}>
      <ReactMarkdown>{text}</ReactMarkdown>
    </div>
  );
}
