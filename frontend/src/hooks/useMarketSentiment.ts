import { useEffect, useState } from "react";

interface MarketSentiment {
  score:   number;
  label:   string;
  signals: {
    volatility?:    string;
    momentum?:      string;
    breadth?:       string;
    risk_appetite?: string;
  };
  inputs: {
    vxx_price?:   number;
    spy_change?:  number;
    breadth_pct?: number;
  };
}

export function useMarketSentiment(refreshMs = 60000) {
  const [data, setData]       = useState<MarketSentiment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const fetch_ = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res  = await fetch(`${apiBase}/market/sentiment`);
        const json = await res.json();
        if (!cancelled) setData(json);
      } catch (e) {
        console.error("[MarketSentiment] failed:", e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetch_();
    const interval = setInterval(fetch_, refreshMs);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  return { data, loading };
}
