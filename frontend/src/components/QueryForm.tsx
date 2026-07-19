import { useState } from "react";

interface Props {
  onSubmit: (question: string) => void;
  loading: boolean;
  suggestions: string[];
}

export function QueryForm({ onSubmit, loading, suggestions }: Props) {
  const [question, setQuestion] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);

  const submit = (q: string) => {
    const trimmed = q.trim();
    if (!trimmed || loading) return;
    setShowSuggestions(false);
    onSubmit(trimmed);
  };

  return (
    <form
      className="query-form"
      onSubmit={(e) => {
        e.preventDefault();
        submit(question);
      }}
    >
      <div className="query-input-wrap">
        <textarea
          value={question}
          onChange={(e) => {
            setQuestion(e.target.value);
            if (e.target.value.trim()) setShowSuggestions(false);
          }}
          onFocus={() => {
            if (!question.trim()) setShowSuggestions(true);
          }}
          onBlur={() => setShowSuggestions(false)}
          placeholder="Ask a question about the t-shirt inventory..."
          rows={3}
        />
        {showSuggestions && suggestions.length > 0 && (
          <div className="suggestions-dropdown">
            <div className="suggestions-label">Try asking</div>
            {suggestions.map((q) => (
              <button
                key={q}
                type="button"
                className="suggestion-item"
                // onMouseDown (not onClick) fires before the textarea's onBlur closes
                // this dropdown, so the click still lands on the intended suggestion.
                onMouseDown={(e) => {
                  e.preventDefault();
                  setQuestion(q);
                  submit(q);
                }}
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="query-form-row">
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? "Thinking…" : "Ask"}
        </button>
        <span className="query-hint">Click the box for example questions</span>
      </div>
    </form>
  );
}
