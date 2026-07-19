import { useEffect, useRef, useState } from "react";
import type { SchemaTable } from "../types/api";

export type Tab = "answer" | "trace" | "eval";

const VIEW_ITEMS: { id: Tab; label: string }[] = [
  { id: "answer", label: "Answer" },
  { id: "trace", label: "Pipeline trace" },
  { id: "eval", label: "Validation" },
];

interface Props {
  tables: SchemaTable[];
  activeTab: Tab;
  onSelectTab: (tab: Tab) => void;
}

export function MenuPanel({ tables, activeTab, onSelectTab }: Props) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onOutsideClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onOutsideClick);
    return () => document.removeEventListener("mousedown", onOutsideClick);
  }, [open]);

  return (
    <div className="menu-wrap" ref={wrapRef}>
      <button type="button" className="menu-trigger" onClick={() => setOpen((o) => !o)}>
        [ menu ]
      </button>
      {open && (
        <div className="menu-dropdown">
          <div className="menu-section-label">view</div>
          {VIEW_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`menu-item ${activeTab === item.id ? "active" : ""}`}
              onClick={() => {
                onSelectTab(item.id);
                setOpen(false);
              }}
            >
              {item.label}
            </button>
          ))}

          <div className="menu-section-label">schema</div>
          {tables.length === 0 && <p className="menu-empty">no tables loaded</p>}
          {tables.map((table) => (
            <details key={table.name} className="menu-schema-table">
              <summary>{table.name}</summary>
              <ul>
                {table.columns.map((col) => (
                  <li key={col}>{col}</li>
                ))}
              </ul>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
