"use client";
import { useEffect, useState } from "react";

interface Article {
  headline: string;
  source:   string;
  url:      string;
  category: string;
  ago:      string;
}

const CATEGORY_COLORS: Record<string, string> = {
  GENERAL:   "bg-muted text-foreground",
  FOREX:     "bg-blue-900/60 text-blue-300",
  CRYPTO:    "bg-orange-900/60 text-orange-300",
  MERGER:    "bg-purple-900/60 text-purple-300",
  TECH:      "bg-red-900/60 text-red-300",
  MACRO:     "bg-emerald-900/60 text-emerald-300",
  EARNINGS:  "bg-amber-900/60 text-amber-300",
  ENERGY:    "bg-yellow-900/60 text-yellow-300",
};

function ArticleSkeleton() {
  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <div className="flex justify-between mb-4">
        <div className="h-5 w-16 bg-muted rounded animate-pulse" />
        <div className="h-4 w-12 bg-muted rounded animate-pulse" />
      </div>
      <div className="h-4 w-full bg-muted rounded animate-pulse mb-2" />
      <div className="h-4 w-3/4 bg-muted rounded animate-pulse mb-6" />
      <div className="h-3 w-20 bg-muted rounded animate-pulse" />
    </div>
  );
}

export default function BreakingNews() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    const fetch_ = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res  = await fetch(`${apiBase}/news/market?limit=4`);
        const data = await res.json();
        setArticles(data.articles || []);
      } catch (e) {
        console.error("[BreakingNews] fetch failed:", e);
      } finally {
        setLoading(false);
      }
    };
    fetch_();
  }, []);

  return (
    <div>
      <h2 className="font-serif italic text-3xl text-foreground mb-6">
        Breaking News
      </h2>
      <div className="grid grid-cols-2 gap-4">
        {loading
          ? [1,2,3,4].map(i => <ArticleSkeleton key={i} />)
          : articles.slice(0, 4).map((a, i) => {
              const colorClass =
                CATEGORY_COLORS[a.category] || CATEGORY_COLORS.GENERAL;
              return (
                <a
                  key={i}
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-card border border-border rounded-2xl p-6 flex flex-col justify-between hover:bg-muted/60 transition-colors cursor-pointer"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className={`text-xs px-2.5 py-1 rounded font-medium ${colorClass}`}>
                        {a.category}
                      </span>
                      <span className="text-xs text-muted-foreground">{a.ago}</span>
                    </div>
                    <p className="text-foreground font-medium leading-snug text-base">
                      {a.headline}
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground mt-6">{a.source}</p>
                </a>
              );
            })}
      </div>
    </div>
  );
}
