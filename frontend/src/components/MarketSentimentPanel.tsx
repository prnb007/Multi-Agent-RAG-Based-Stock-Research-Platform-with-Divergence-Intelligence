"use client";
import { useMarketSentiment } from "@/hooks/useMarketSentiment";

// Color of the gauge arc based on score
function gaugeColor(score: number): string {
  if (score <= 25) return "#ef4444";  // red — extreme fear
  if (score <= 45) return "#f97316";  // orange — fear
  if (score <= 55) return "#eab308";  // yellow — neutral
  if (score <= 75) return "#22c55e";  // green — greed
  return "#16a34a";                   // dark green — extreme greed
}

export default function MarketSentimentPanel() {
  const { data, loading } = useMarketSentiment(60000);

  const score = data?.score ?? 50;
  const label = data?.label ?? "Neutral";
  const color = gaugeColor(score);

  // Arc: 0 = far left (-135deg), 100 = far right (+135deg)
  // Total arc sweep = 270 degrees
  const rotation = -135 + (score / 100) * 270;

  return (
    <div className="rounded-2xl bg-card border border-border p-8">
      <h3 className="font-serif italic text-2xl text-foreground mb-6">
        Market Sentiment
      </h3>

      {/* Gauge */}
      <div className="flex flex-col items-center justify-center mb-8">
        <div className="relative w-48 h-28 flex items-center justify-center">
          {/* Background arc — draw with SVG */}
          <svg viewBox="0 0 200 120" className="absolute inset-0 w-full h-full">
            <path
              d="M 20 110 A 80 80 0 0 1 180 110"
              fill="none" stroke="#262626" strokeWidth="12"
              strokeLinecap="round"
            />
            {!loading && (
              <path
                d="M 20 110 A 80 80 0 0 1 180 110"
                fill="none"
                stroke={color}
                strokeWidth="12"
                strokeLinecap="round"
                strokeDasharray={`${(score / 100) * 251.2} 251.2`}
              />
            )}
          </svg>
          <div className="relative z-10 text-center mt-4">
            {loading ? (
              <div className="h-10 w-16 bg-muted rounded animate-pulse mx-auto" />
            ) : (
              <>
                <div className="text-4xl font-semibold" style={{ color }}>
                  {score}
                </div>
                <div className="text-xs tracking-widest text-muted-foreground mt-1">
                  {label.toUpperCase()}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Signal rows */}
      <div className="space-y-3">
        {[
          { label: "Momentum",     key: "momentum"     },
          { label: "Breadth",      key: "breadth"      },
          { label: "Volatility",   key: "volatility"   },
          { label: "Risk Appetite",key: "risk_appetite"},
        ].map(({ label: rowLabel, key }) => {
          const value = data?.signals?.[key as keyof typeof data.signals];
          const isPositive = value && [
            "Strong","Positive","Broad Advance","Low","Extremely Low","Risk-On"
          ].includes(value);
          return (
            <div key={key} className="flex justify-between items-center py-2 border-b border-border">
              <span className="text-sm text-muted-foreground">{rowLabel}</span>
              {loading ? (
                <div className="h-4 w-16 bg-muted rounded animate-pulse" />
              ) : (
                <span className={`text-sm font-medium ${
                  isPositive ? "text-emerald-400" : "text-neutral-300"
                }`}>
                  {value ?? "—"}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
