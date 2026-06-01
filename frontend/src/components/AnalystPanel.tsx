"use client";
import { useEffect, useState } from "react";
import { InfoTooltip } from "@/components/InfoTooltip";

interface Recommendation {
  ticker:          string;
  period:          string;
  strong_buy:      number;
  buy:             number;
  hold:            number;
  sell:            number;
  strong_sell:     number;
  total:           number;
  consensus_score: number;
}

function useRecommendations(ticker: string) {
  const [data, setData]       = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    const fetch_ = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res  = await fetch(`${apiBase}/recommendations/${ticker}`);
        const json = await res.json();
        if (!json.error) setData(json);
      } catch (e) {
        console.error("[AnalystPanel] failed:", e);
      } finally {
        setLoading(false);
      }
    };
    fetch_();
  }, [ticker]);

  return { data, loading };
}

function ConsensusLabel({ score }: { score: number }) {
  if (score >= 0.6)  return <span className="text-emerald-400 font-semibold">Strong Buy</span>;
  if (score >= 0.2)  return <span className="text-emerald-400 font-medium">Buy</span>;
  if (score >= -0.2) return <span className="text-yellow-400 font-medium">Hold</span>;
  if (score >= -0.6) return <span className="text-rose-400 font-medium">Sell</span>;
  return <span className="text-rose-500 font-semibold">Strong Sell</span>;
}

function RatingBar({
  label, count, total, color
}: {
  label: string; count: number; total: number; color: string
}) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-neutral-500 w-20 shrink-0">{label}</span>
      <div className="flex-1 bg-neutral-800 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-neutral-400 w-6 text-right">{count}</span>
    </div>
  );
}

export default function AnalystPanel({ ticker }: { ticker: string }) {
  const { data, loading } = useRecommendations(ticker);

  if (loading) {
    return (
      <div className="rounded-2xl bg-neutral-900/40 border border-neutral-800/60 p-6">
        <div className="h-4 w-40 bg-neutral-800 rounded animate-pulse mb-6" />
        <div className="space-y-3">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="h-3 bg-neutral-800 rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const score = data.consensus_score;
  // Gauge: convert -1.0 to +1.0 into 0-100 for display
  const gaugePct = ((score + 1) / 2) * 100;

  return (
    <div className="rounded-2xl bg-neutral-900/40 border border-neutral-800/60 p-6">

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-sm font-medium text-neutral-100 tracking-wide flex items-center">
            Wall Street Consensus <InfoTooltip termKey="wall_street_consensus" />
          </h3>
          <p className="text-xs text-neutral-500 mt-0.5">
            {data.total} analysts · {data.period}
          </p>
        </div>
        <div className="text-right">
          <ConsensusLabel score={score} />
          <p className="text-xs text-neutral-500 mt-0.5">
            score {score.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Consensus score bar */}
      <div className="mb-6">
        <div className="flex justify-between text-xs text-neutral-600 mb-1">
          <span>Strong Sell</span>
          <span>Strong Buy</span>
        </div>
        <div className="relative h-2 bg-neutral-800 rounded-full overflow-hidden">
          {/* Color gradient track */}
          <div className="absolute inset-0 rounded-full"
            style={{
              background: "linear-gradient(to right, #ef4444, #f97316, #eab308, #22c55e, #16a34a)"
            }}
            aria-hidden="true"
          />
          {/* Position indicator */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-neutral-900 shadow"
            style={{ left: `calc(${gaugePct}% - 6px)` }}
          />
        </div>
      </div>

      {/* Rating distribution */}
      <div className="space-y-2.5">
        <RatingBar
          label="Strong Buy" count={data.strong_buy}
          total={data.total} color="bg-emerald-500"
        />
        <RatingBar
          label="Buy"        count={data.buy}
          total={data.total} color="bg-emerald-400"
        />
        <RatingBar
          label="Hold"       count={data.hold}
          total={data.total} color="bg-yellow-400"
        />
        <RatingBar
          label="Sell"       count={data.sell}
          total={data.total} color="bg-rose-400"
        />
        <RatingBar
          label="Strong Sell" count={data.strong_sell}
          total={data.total} color="bg-rose-600"
        />
      </div>

      {/* Totals summary */}
      <div className="mt-5 pt-4 border-t border-neutral-800/60 grid grid-cols-3 gap-2">
        {[
          {
            label: "Bullish",
            count: data.strong_buy + data.buy,
            color: "text-emerald-400"
          },
          {
            label: "Neutral",
            count: data.hold,
            color: "text-yellow-400"
          },
          {
            label: "Bearish",
            count: data.sell + data.strong_sell,
            color: "text-rose-400"
          },
        ].map(({ label, count, color }) => (
          <div key={label} className="text-center">
            <div className={`text-xl font-semibold ${color}`}>{count}</div>
            <div className="text-xs text-neutral-500 mt-0.5">{label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
