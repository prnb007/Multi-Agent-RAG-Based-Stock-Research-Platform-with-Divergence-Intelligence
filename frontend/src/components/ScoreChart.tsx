import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ReferenceLine,
  Tooltip,
  Cell,
  CartesianGrid
} from 'recharts';

export interface ScoreChartProps {
  agents: Array<{
    agent: string;
    score: number;
    confidence: number;
  }>;
  overallScore: number;
}

export function ScoreChart({ agents, overallScore = 0 }: ScoreChartProps) {
  const getOverallSignalLabel = (score: number) => {
    if (score >= 0.6) return 'Bullish';
    if (score >= 0.2) return 'Mildly Bullish';
    if (score > -0.2) return 'Neutral';
    if (score > -0.6) return 'Mildly Bearish';
    return 'Bearish';
  };

  const getSignalColor = (score: number) => {
    if (score >= 0.2) return 'text-teal-500';
    if (score <= -0.2) return 'text-red-500';
    return 'text-gray-400';
  };

  const formatScore = (val: number) => {
    return (val > 0 ? '+' : '') + val.toFixed(2);
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#1e1e1e] border border-[#333] p-3 rounded-lg shadow-lg text-sm">
          <p className="font-semibold text-white capitalize mb-1">{data.agent}</p>
          <p className="text-gray-300">
            <span className={data.score > 0 ? 'text-teal-400' : data.score < 0 ? 'text-red-400' : 'text-gray-400'}>
              {formatScore(data.score)}
            </span>
            <span className="text-gray-500 ml-1">
              ({Math.round(data.confidence * 100)}% confidence)
            </span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full bg-card/50 backdrop-blur-sm border border-border/50 rounded-xl p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-xl font-bold tracking-tight">Agent Sentiment Comparison</h3>
        <p className="text-sm text-muted-foreground">Bar width indicates score, opacity indicates confidence</p>
      </div>

      <div className="w-full h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={agents}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#333" />
            <XAxis 
              type="number" 
              domain={[-1.0, 1.0]} 
              tickFormatter={formatScore}
              tick={{ fill: '#888', fontSize: 12 }}
              stroke="#333"
            />
            <YAxis 
              type="category" 
              dataKey="agent" 
              tick={{ fill: '#eee', fontSize: 13 }}
              stroke="#333"
              width={100}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
            <ReferenceLine x={0} stroke="#888" strokeDasharray="3 3" label={{ position: 'top', value: 'Neutral', fill: '#888', fontSize: 12 }} />
            <Bar 
              dataKey="score" 
              isAnimationActive={true}
              animationDuration={1000}
              radius={[0, 4, 4, 0]}
              minPointSize={2}
            >
              {agents.map((entry, index) => {
                let color = '#888';
                if (entry.score > 0) color = '#1D9E75';
                else if (entry.score < 0) color = '#E24B4A';
                
                // Opacity mapped directly to confidence
                const opacity = Math.max(0.1, entry.confidence);
                
                return <Cell key={`cell-${index}`} fill={color} fillOpacity={opacity} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-6 flex flex-col items-center justify-center p-4 bg-muted/30 rounded-lg border border-border/30">
        <p className="text-sm text-muted-foreground uppercase tracking-wider font-semibold mb-1">Overall Signal</p>
        <div className="flex items-center gap-3">
          <span className={`text-2xl font-bold ${getSignalColor(overallScore)}`}>
            {getOverallSignalLabel(overallScore)}
          </span>
          <span className="text-xl font-mono text-muted-foreground">
            ({formatScore(overallScore)})
          </span>
        </div>
      </div>
    </div>
  );
}
