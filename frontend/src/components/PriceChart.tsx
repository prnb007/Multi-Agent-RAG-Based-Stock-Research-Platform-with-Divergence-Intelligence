import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';

export interface PriceChartProps {
  ticker: string;
  priceHistory?: Array<{
    date: string;
    close: number;
    volume: number;
  }>;
}

export function PriceChart({ ticker, priceHistory }: PriceChartProps) {
  const returnInfo = useMemo(() => {
    if (!priceHistory || priceHistory.length < 2) return null;
    const first = priceHistory[0].close;
    const last = priceHistory[priceHistory.length - 1].close;
    const pct = ((last - first) / first) * 100;
    return {
      value: pct,
      isPositive: pct >= 0,
      formatted: `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
    };
  }, [priceHistory]);

  if (!priceHistory || priceHistory.length === 0) {
    return (
      <div className="w-full h-[400px] flex items-center justify-center border border-dashed border-border/50 rounded-xl bg-card/30">
        <p className="text-muted-foreground text-center px-6">
          Price data unavailable — provider rate limit hit. Try again in a few minutes.
        </p>
      </div>
    );
  }

  // Format date for X-axis to show short month (Jan, Feb, etc.)
  const formatXAxis = (tickItem: string) => {
    const d = new Date(tickItem);
    return d.toLocaleDateString('en-US', { month: 'short' });
  };

  const formatYAxisPrice = (val: number) => {
    return `$${val.toFixed(2)}`;
  };

  const formatVolume = (val: number) => {
    if (val >= 1e9) return (val / 1e9).toFixed(1) + 'B';
    if (val >= 1e6) return (val / 1e6).toFixed(1) + 'M';
    if (val >= 1e3) return (val / 1e3).toFixed(1) + 'K';
    return val.toString();
  };

  return (
    <div className="w-full relative bg-card/50 backdrop-blur-sm border border-border/50 rounded-xl p-4 sm:p-6 shadow-sm">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-xl font-bold tracking-tight">{ticker.toUpperCase()}</h3>
          <p className="text-sm text-muted-foreground">6-Month Price & Volume</p>
        </div>
        
        {returnInfo && (
          <div className={`px-3 py-1 rounded-md text-sm font-bold flex items-center shadow-sm ${
            returnInfo.isPositive 
              ? 'bg-green-500/20 text-green-500 border border-green-500/30' 
              : 'bg-red-500/20 text-red-500 border border-red-500/30'
          }`}>
            {returnInfo.formatted}
          </div>
        )}
      </div>

      <div className="w-full h-[350px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={priceHistory} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
            <XAxis 
              dataKey="date" 
              tickFormatter={formatXAxis} 
              tick={{ fill: '#888', fontSize: 12 }}
              tickMargin={10}
              minTickGap={30}
              stroke="#333"
            />
            <YAxis 
              yAxisId="price"
              domain={['auto', 'auto']}
              tickFormatter={formatYAxisPrice}
              tick={{ fill: '#888', fontSize: 12 }}
              stroke="#333"
              width={60}
            />
            <YAxis 
              yAxisId="volume"
              orientation="right"
              tickFormatter={formatVolume}
              tick={{ fill: '#888', fontSize: 12 }}
              stroke="#333"
              width={50}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e1e1e', borderColor: '#333', borderRadius: '8px', color: '#fff' }}
              itemStyle={{ color: '#fff' }}
              labelStyle={{ color: '#aaa', marginBottom: '8px' }}
              formatter={(value: any, name: any) => {
                if (name === 'close') return [`$${Number(value).toFixed(2)}`, 'Close Price'];
                if (name === 'volume') return [Number(value).toLocaleString(), 'Volume'];
                return [value, name];
              }}
              labelFormatter={(label) => new Date(label).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
            />
            <Bar 
              yAxisId="volume" 
              dataKey="volume" 
              fill="#1D9E75" 
              fillOpacity={0.4} 
              isAnimationActive={true}
              animationDuration={1200}
              animationEasing="ease-out"
              radius={[2, 2, 0, 0]} 
            />
            <Line 
              yAxisId="price" 
              type="monotone" 
              dataKey="close" 
              stroke="#534AB7" 
              strokeWidth={2}
              dot={false}
              isAnimationActive={true}
              animationDuration={1200}
              animationEasing="ease-out"
              activeDot={{ r: 6, fill: '#534AB7', stroke: '#fff', strokeWidth: 2 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
