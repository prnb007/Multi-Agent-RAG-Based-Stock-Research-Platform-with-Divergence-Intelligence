import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { AgentData } from '@/hooks/useAnalysis';
import { motion } from 'framer-motion';
import { PriceChart } from './PriceChart';
import { InfoTooltip, EvidenceWithTooltips } from './InfoTooltip';

interface AgentCardProps {
  name: string;
  ticker?: string;
  data?: AgentData;
  isLoading: boolean;
}

export function AgentCard({ name, ticker, data, isLoading }: AgentCardProps) {
  const [barWidth, setBarWidth] = useState(0);

  useEffect(() => {
    if (data) {
      const timer = setTimeout(() => {
        setBarWidth(data.confidence * 100);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [data]);
  const getScoreColor = (score: number) => {
    if (score >= 0.5) return 'text-green-500';
    if (score > -0.5) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getScoreBadge = (score: number) => {
    if (score >= 0.5) return 'success';
    if (score > -0.5) return 'warning';
    return 'destructive';
  };

  return (
    <Card className="flex flex-col h-full bg-transparent border-none shadow-none transition-colors">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-medium capitalize flex items-center gap-2">
          {name}
          <InfoTooltip termKey={`${name.toLowerCase()}_agent`} />
          {!data && isLoading && <span className="material-symbols-outlined text-[16px] animate-spin text-muted-foreground">sync</span>}
          {data && <span className="material-symbols-outlined text-[16px] text-green-500">check_circle</span>}
        </CardTitle>
        {data && (
          <Badge variant={getScoreBadge(data.score)}>
            Score: {data.score.toFixed(2)}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="flex-1">
        {!data ? (
          <div className="flex flex-col gap-2">
            <div className="skeleton h-4 w-24 rounded mb-4" />
            <div className="skeleton h-4 w-full rounded" />
            <div className="skeleton h-4 w-5/6 rounded mb-4" />
            
            <div className="skeleton h-3 w-3/4 rounded mt-4" />
            <div className="skeleton h-3 w-4/5 rounded mt-2" />
            <div className="skeleton h-3 w-2/3 rounded mt-2" />
          </div>
        ) : (
          <div className="space-y-4 agent-card-enter">
            <div>
              <div className="text-sm text-muted-foreground mb-1 flex justify-between">
                <span className="flex items-center">
                  Confidence <InfoTooltip termKey="confidence" />
                </span>
                <span>{(data.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-1.5">
                <div 
                  className="confidence-bar bg-primary h-1.5 rounded-full" 
                  style={{ width: `${barWidth}%` }}
                />
              </div>
            </div>
            
            {name === 'technical' && ticker && (
              <div className="mb-4">
                <PriceChart ticker={ticker} priceHistory={data.raw_data?.priceHistory} />
              </div>
            )}
            
            <p className="text-sm leading-relaxed">{data.summary}</p>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Evidence</h4>
              <ul className="space-y-2">
                {data.evidence.map((ev, i) => (
                  <li key={i} className="text-sm flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span className="text-muted-foreground">
                      <EvidenceWithTooltips text={ev} />
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
