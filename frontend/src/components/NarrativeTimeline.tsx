"use client";
import { useEffect, useState } from "react";

interface Quarter {
  quarter:            string;
  filing_date:        string;
  management_tone:    string;
  margin_language:    string;
  ai_monetization:    string;
  demand_signals:     string;
  hiring_language:    string;
  regulatory_concern: string;
  recurring_concerns: string[];
  key_quotes:         string[];
  confidence:         number;
}

interface NarrativeData {
  ticker:   string;
  quarters: Quarter[];
  summary:  {
    tone_trend:   string[];
    ai_trend:     string[];
    margin_trend: string[];
  };
}

// Signal value → numeric score for trend rendering
const SIGNAL_SCORES: Record<string, number> = {
  // tone
  optimistic: 2, cautious: 1, defensive: 0,
  // margins
  expanding: 2, stable: 1, pressured: 0,
  // ai
  strong: 2, emerging: 1, absent: 0,
  // demand
  // strong = 2, mixed = 1, weak = 0
  mixed: 1, weak: 0,
  // hiring
  // expanding = 2, stable = 1, freezing = 0
  freezing: 0,
  // regulatory (inverted — low concern is good)
  low: 2, moderate: 1, high: 0,
};

const SIGNAL_COLORS: Record<string, string> = {
  optimistic: "text-emerald-400", cautious: "text-yellow-400",
  defensive:  "text-rose-400",
  expanding:  "text-emerald-400", stable: "text-neutral-300",
  pressured:  "text-rose-400",
  strong:     "text-emerald-400", emerging: "text-yellow-400",
  absent:     "text-neutral-500",
  mixed:      "text-yellow-400",  weak: "text-rose-400",
  freezing:   "text-rose-400",
  low:        "text-emerald-400", moderate: "text-yellow-400",
  high:       "text-rose-400",
};

const SIGNAL_DOTS: Record<string, string> = {
  optimistic: "bg-emerald-400", cautious: "bg-yellow-400",
  defensive:  "bg-rose-400",
  expanding:  "bg-emerald-400", stable: "bg-neutral-500",
  pressured:  "bg-rose-400",
  strong:     "bg-emerald-400", emerging: "bg-yellow-400",
  absent:     "bg-neutral-700",
  mixed:      "bg-yellow-400",  weak: "bg-rose-400",
  freezing:   "bg-rose-400",
  low:        "bg-emerald-400", moderate: "bg-yellow-400",
  high:       "bg-rose-400",
};

const SIGNALS = [
  { key: "management_tone",    label: "Management Tone"    },
  { key: "margin_language",    label: "Margin Language"    },
  { key: "ai_monetization",    label: "AI Monetization"    },
  { key: "demand_signals",     label: "Demand Signals"     },
  { key: "hiring_language",    label: "Hiring Language"    },
  { key: "regulatory_concern", label: "Regulatory Concern" },
];

function SignalDot({ value }: { value: string }) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className={`w-3 h-3 rounded-full ${SIGNAL_DOTS[value] || "bg-neutral-700"}`} />
      <span className={`text-xs ${SIGNAL_COLORS[value] || "text-neutral-500"}`}>
        {value}
      </span>
    </div>
  );
}

function TrendLine({ values }: { values: string[] }) {
  const scores = values.map(v => SIGNAL_SCORES[v] ?? 1);
  return (
    <div className="flex items-center gap-0">
      {scores.map((score, i) => (
        <div key={i} className="flex items-center">
          <div
            className={`w-2 h-2 rounded-full ${
              score === 2 ? "bg-emerald-400" :
              score === 1 ? "bg-yellow-400"  : "bg-rose-400"
            }`}
          />
          {i < scores.length - 1 && (
            <div className={`h-0.5 w-8 ${
              scores[i+1] > score ? "bg-emerald-400/50" :
              scores[i+1] < score ? "bg-rose-400/50"    :
              "bg-neutral-700"
            }`} />
          )}
        </div>
      ))}
    </div>
  );
}

export default function NarrativeTimeline({ ticker }: { ticker: string }) {
  const [data, setData]         = useState<NarrativeData | null>(null);
  const [loading, setLoading]   = useState(false);
  const [processing, setProc]   = useState(false);
  const [selected, setSelected] = useState<Quarter | null>(null);

  useEffect(() => {
    if (!ticker) return;
    fetchNarrative();
  }, [ticker]);

  const fetchNarrative = async () => {
    setLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res  = await fetch(`${apiBase}/narrative/${ticker}`);
      const json = await res.json();
      if (json.quarters?.length > 0) {
        setData(json);
        setSelected(json.quarters[json.quarters.length - 1]);
      } else {
        setData(null);
      }
    } catch (e) {
      console.error("[Narrative] fetch failed:", e);
    } finally {
      setLoading(false);
    }
  };

  const triggerProcess = async () => {
    setProc(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${apiBase}/narrative/${ticker}/preprocess`);
      // Poll every 10s for up to 90s
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        const res  = await fetch(`${apiBase}/narrative/${ticker}`);
        const json = await res.json();
        if (json.quarters?.length > 0 || attempts > 9) {
          clearInterval(poll);
          setProc(false);
          if (json.quarters?.length > 0) {
            setData(json);
            setSelected(json.quarters[json.quarters.length - 1]);
          }
        }
      }, 10000);
    } catch (e) {
      setProc(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        {[1,2,3].map(i => (
          <div key={i} className="h-12 bg-muted rounded-xl" />
        ))}
      </div>
    );
  }

  if (!data || data.quarters.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">📄</div>
        <h3 className="text-lg font-medium text-foreground mb-2">
          No narrative data yet for {ticker}
        </h3>
        <p className="text-sm text-muted-foreground mb-6">
          Process SEC 10-Q filings to extract management language signals
        </p>
        <button
          onClick={triggerProcess}
          disabled={processing}
          className="px-6 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium disabled:opacity-50 transition-colors"
        >
          {processing
            ? "Processing filings... (~60s)"
            : "Extract Narrative Signals"}
        </button>
        {processing && (
          <p className="text-xs text-muted-foreground mt-3">
            Downloading SEC filings and running LLM analysis...
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-8">

      {/* Introduction block */}
      <div className="mb-8">
        <h2 className="text-2xl font-medium text-foreground mb-3">
          Narrative Intelligence for {ticker?.toUpperCase() || "—"}
        </h2>
        <p className="text-sm text-muted-foreground leading-relaxed max-w-3xl">
          Tracks how management language shifts across the last {data.quarters.length} quarterly SEC 10-Q filings.
          By analyzing the Management Discussion &amp; Analysis (MD&amp;A) section of each filing,
          we extract standardized signals — tone, margin language, AI monetization, demand,
          hiring, and regulatory concerns — to surface narrative shifts that often precede
          fundamental changes. Click any quarter column to see specific quotes and concerns.
        </p>
      </div>

      {/* Header controls */}
      <div className="flex items-center justify-end">
        <button
          onClick={triggerProcess}
          disabled={processing}
          className="text-xs px-3 py-1.5 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:border-foreground/50 disabled:opacity-40 transition-colors"
        >
          {processing ? "Refreshing..." : "↻ Refresh"}
        </button>
      </div>

      {/* Signal trend grid */}
      <div className="bg-card border border-border rounded-2xl p-6">
        <div className="text-xs text-muted-foreground tracking-widest mb-6">
          SIGNAL TRENDS ACROSS QUARTERS
        </div>

        {/* Quarter labels */}
        <div className="grid mb-4"
          style={{ gridTemplateColumns: `160px repeat(${data.quarters.length}, 1fr)` }}
        >
          <div />
          {data.quarters.map(q => (
            <div key={q.quarter} className="text-center">
              <button
                onClick={() => setSelected(q)}
                className={`text-xs px-2 py-1 rounded-lg transition-colors ${
                  selected?.quarter === q.quarter
                    ? "bg-violet-600/30 text-violet-300 border border-violet-500/40"
                    : "text-neutral-500 hover:text-neutral-300"
                }`}
              >
                {q.quarter}
              </button>
            </div>
          ))}
        </div>

        {/* Signal rows */}
        {SIGNALS.map(({ key, label }) => (
          <div
            key={key}
            className="grid items-center py-3 border-b border-border/40"
            style={{ gridTemplateColumns: `160px repeat(${data.quarters.length}, 1fr)` }}
          >
            <span className="text-xs text-muted-foreground">{label}</span>
            {data.quarters.map(q => (
              <div key={q.quarter} className="flex justify-center">
                <SignalDot value={(q as any)[key]} />
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Selected quarter detail */}
      {selected && (
        <div className="bg-card border border-border rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-sm font-medium text-foreground">
                {selected.quarter} · Detailed Analysis
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Filed {selected.filing_date} ·
                {Math.round(selected.confidence * 100)}% confidence
              </p>
            </div>
          </div>

          {/* Key quotes */}
          {selected.key_quotes.length > 0 && (
            <div className="mb-5">
              <div className="text-xs text-muted-foreground tracking-widest mb-3">
                KEY MANAGEMENT LANGUAGE
              </div>
              <div className="space-y-2">
                {selected.key_quotes.map((q, i) => (
                  <div
                    key={i}
                    className="text-sm text-foreground/80 italic border-l-2 border-violet-500/50 pl-3 py-1"
                  >
                    "{q}"
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recurring concerns */}
          {selected.recurring_concerns.length > 0 && (
            <div>
              <div className="text-xs text-muted-foreground tracking-widest mb-3">
                RECURRING CONCERNS
              </div>
              <div className="flex flex-wrap gap-2">
                {selected.recurring_concerns.map((c, i) => (
                  <span
                    key={i}
                    className="text-xs px-3 py-1.5 rounded-full bg-muted text-muted-foreground border border-border"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
