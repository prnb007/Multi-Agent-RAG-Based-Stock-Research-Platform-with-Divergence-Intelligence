"use client";
import React, { useState, useRef, useEffect } from "react";
import { GLOSSARY } from "@/lib/glossary";

interface InfoTooltipProps {
  termKey: string;
  size?: "sm" | "md";
}

export function InfoTooltip({ termKey, size = "sm" }: InfoTooltipProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const term = GLOSSARY[termKey];

  // Close on outside click (handles mobile tap-away)
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  if (!term) return null;

  const iconSize = size === "sm" ? "w-3.5 h-3.5" : "w-4 h-4";

  return (
    <span ref={ref} className="relative inline-flex items-center">
      <button
        type="button"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onClick={() => setOpen(v => !v)}
        className="ml-1.5 text-neutral-500 hover:text-neutral-300 transition-colors shrink-0"
        aria-label={`Info about ${term.term}`}
      >
        <svg className={iconSize} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" strokeWidth="1.5" />
          <path strokeWidth="1.5" strokeLinecap="round" d="M12 16v-4m0-4h.01" />
        </svg>
      </button>

      {open && (
        <div className="absolute z-50 left-0 top-full mt-2 w-72 p-4 rounded-xl bg-neutral-900 border border-neutral-700 shadow-2xl text-left pointer-events-none">
          <div className="text-sm font-medium text-neutral-100 mb-1.5">
            {term.term}
          </div>
          <div className="text-xs text-neutral-400 leading-relaxed">
            {term.full}
          </div>
          {term.example && (
            <div className="text-xs text-violet-300 italic leading-relaxed mt-2 pt-2 border-t border-neutral-800">
              Example: {term.example}
            </div>
          )}
        </div>
      )}
    </span>
  );
}

// Financial terms to detect in evidence text strings
const EVIDENCE_TERM_PATTERNS: Array<{ regex: RegExp; key: string }> = [
  { regex: /\bRSI\b/g,                         key: "rsi" },
  { regex: /\bMACD\b/g,                         key: "macd" },
  { regex: /\bBollinger Bands?\b/gi,            key: "bollinger_bands" },
  { regex: /\bP\/E(?: Ratio)?\b/gi,            key: "pe_ratio" },
  { regex: /\bROE\b/g,                          key: "roe" },
  { regex: /\bNet Margin\b/gi,                  key: "net_margin" },
  { regex: /\bFree Cash Flow\b|\bFCF\b/gi,     key: "free_cash_flow" },
];

// Renders an evidence string with inline InfoTooltips for known financial terms
export function EvidenceWithTooltips({ text }: { text: string }) {
  const matches: { start: number; end: number; key: string }[] = [];

  for (const { regex, key } of EVIDENCE_TERM_PATTERNS) {
    regex.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = regex.exec(text)) !== null) {
      matches.push({ start: m.index, end: m.index + m[0].length, key });
    }
  }

  if (matches.length === 0) return <span>{text}</span>;

  // Sort by position and remove overlaps
  matches.sort((a, b) => a.start - b.start);
  const filtered = matches.filter((m, i) => i === 0 || m.start >= matches[i - 1].end);

  const parts: React.ReactNode[] = [];
  let pos = 0;

  for (const { start, end, key } of filtered) {
    if (start > pos) parts.push(text.slice(pos, start));
    parts.push(
      <span key={start} className="inline-flex items-baseline">
        {text.slice(start, end)}
        <InfoTooltip termKey={key} />
      </span>
    );
    pos = end;
  }

  if (pos < text.length) parts.push(text.slice(pos));

  return <span>{parts}</span>;
}
