// Renders arbitrary pipeline stage input/output as labeled fields instead of a raw
// JSON.stringify dump — SQL-shaped keys get a code block, LLM-authored prose fields
// (answer/approach) get markdown rendering, lists get a comma line or nested rows,
// everything else gets a plain label/value row.

import { MarkdownText } from "./MarkdownText";

const SQL_KEY_RE = /sql/i;
const MARKDOWN_KEYS = new Set(["answer", "approach"]);

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function renderScalarList(items: unknown[]) {
  return <span className="field-value">{items.map(String).join(", ")}</span>;
}

function FieldValue({ fieldKey, value }: { fieldKey: string; value: unknown }) {
  if (value === null || value === undefined || value === "") {
    return <span className="field-empty">—</span>;
  }

  if (fieldKey === "error") {
    return <span className="stage-error-msg">{String(value)}</span>;
  }

  if (typeof value === "string" && SQL_KEY_RE.test(fieldKey)) {
    return <pre className="sql-block field-sql">{value}</pre>;
  }

  if (typeof value === "string" && MARKDOWN_KEYS.has(fieldKey)) {
    return <MarkdownText text={value} />;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="field-empty">—</span>;
    if (value.every((v) => !isPlainObject(v) && !Array.isArray(v))) {
      return renderScalarList(value);
    }
    return (
      <div className="field-list">
        {value.map((v, i) => (
          <div className="field-list-item" key={i}>
            <DetailFields data={v} />
          </div>
        ))}
      </div>
    );
  }

  if (isPlainObject(value)) {
    return <DetailFields data={value} />;
  }

  return <span className="field-value">{String(value)}</span>;
}

interface Props {
  data: unknown;
}

export function DetailFields({ data }: Props) {
  if (data === null || data === undefined) return <span className="field-empty">—</span>;
  if (!isPlainObject(data)) return <span className="field-value">{String(data)}</span>;

  const entries = Object.entries(data);
  if (entries.length === 0) return <span className="field-empty">—</span>;

  return (
    <dl className="field-rows">
      {entries.map(([key, value]) => (
        <div className="field-row" key={key}>
          <dt>{key.replace(/_/g, " ")}</dt>
          <dd>
            <FieldValue fieldKey={key} value={value} />
          </dd>
        </div>
      ))}
    </dl>
  );
}
