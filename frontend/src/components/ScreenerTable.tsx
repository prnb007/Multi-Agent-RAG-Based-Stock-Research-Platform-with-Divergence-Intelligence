"use client";
import { useScreenerQuotes } from "@/hooks/useScreenerQuotes";

const SCREENER_TICKERS = [
  { ticker: "AAPL",  name: "Apple Inc."          },
  { ticker: "MSFT",  name: "Microsoft Corp."      },
  { ticker: "NVDA",  name: "NVIDIA Corp."         },
  { ticker: "GOOGL", name: "Alphabet Inc."        },
  { ticker: "AMZN",  name: "Amazon.com Inc."      },
  { ticker: "META",  name: "Meta Platforms Inc."  },
  { ticker: "TSLA",  name: "Tesla Inc."           },
  { ticker: "JPM",   name: "JPMorgan Chase"       },
  { ticker: "V",     name: "Visa Inc."            },
  { ticker: "JNJ",   name: "Johnson & Johnson"    },
];

function SkeletonRow() {
  return (
    <tr className="border-b border-neutral-800/60">
      {[1,2,3,4,5,6].map(i => (
        <td key={i} className="px-4 py-4">
          <div className="h-4 bg-neutral-800 rounded animate-pulse w-20" />
        </td>
      ))}
    </tr>
  );
}

export default function ScreenerTable({
  onAnalyze
}: {
  onAnalyze: (ticker: string) => void
}) {
  const { quotes, loading } = useScreenerQuotes(
    SCREENER_TICKERS.map(t => t.ticker)
  );

  return (
    <div className="w-full overflow-x-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-light italic text-neutral-100">
            Screener
          </h2>
          <p className="text-sm text-neutral-500 mt-1">
            {SCREENER_TICKERS.length} stocks · live prices
          </p>
        </div>
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-neutral-800 text-neutral-500 text-xs tracking-widest">
            <th className="text-left px-4 py-3 font-normal">COMPANY</th>
            <th className="text-right px-4 py-3 font-normal">LAST PRICE</th>
            <th className="text-right px-4 py-3 font-normal">CHANGE</th>
            <th className="text-right px-4 py-3 font-normal">DAY RANGE</th>
            <th className="text-right px-4 py-3 font-normal">PREV CLOSE</th>
            <th className="text-center px-4 py-3 font-normal">ANALYZE</th>
          </tr>
        </thead>
        <tbody>
          {loading
            ? SCREENER_TICKERS.map(t => <SkeletonRow key={t.ticker} />)
            : SCREENER_TICKERS.map(({ ticker, name }) => {
                const q = quotes[ticker];
                const pct = q?.percent_change ?? null;
                const isUp   = pct !== null && pct > 0.001;
                const isDown = pct !== null && pct < -0.001;
                const color  = isUp
                  ? "text-emerald-400"
                  : isDown
                  ? "text-rose-400"
                  : "text-neutral-400";

                return (
                  <tr
                    key={ticker}
                    className="border-b border-neutral-800/40 hover:bg-neutral-900/40 transition-colors"
                  >
                    <td className="px-4 py-4">
                      <div className="font-medium text-neutral-100">{ticker}</div>
                      <div className="text-xs text-neutral-500 mt-0.5">{name}</div>
                    </td>
                    <td className="px-4 py-4 text-right font-medium text-neutral-100">
                      {q ? `$${q.current_price.toFixed(2)}` : "—"}
                    </td>
                    <td className={`px-4 py-4 text-right font-medium ${color}`}>
                      {pct !== null
                        ? `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`
                        : "—"}
                    </td>
                    <td className="px-4 py-4 text-right text-neutral-400">
                      {q
                        ? `$${q.day_low.toFixed(2)} – $${q.day_high.toFixed(2)}`
                        : "—"}
                    </td>
                    <td className="px-4 py-4 text-right text-neutral-400">
                      {q ? `$${q.prev_close.toFixed(2)}` : "—"}
                    </td>
                    <td className="px-4 py-4 text-center">
                      <button
                        onClick={() => onAnalyze(ticker)}
                        className="text-xs px-3 py-1.5 rounded-lg border border-neutral-700 text-neutral-300 hover:bg-neutral-800 hover:text-neutral-100 transition-colors"
                      >
                        Analyze ↗
                      </button>
                    </td>
                  </tr>
                );
              })}
        </tbody>
      </table>
    </div>
  );
}
