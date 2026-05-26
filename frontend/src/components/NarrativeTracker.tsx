import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { AgentData } from '@/hooks/useAnalysis';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

interface NarrativeTrackerProps {
  agents: Record<string, AgentData>;
}

export function NarrativeTracker({ agents }: NarrativeTrackerProps) {
  const data = useMemo(() => {
    return Object.keys(agents).map(key => ({
      name: key.charAt(0).toUpperCase() + key.slice(1),
      score: agents[key].score,
      confidence: agents[key].confidence
    }));
  }, [agents]);

  if (data.length === 0) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm">
        <CardContent className="p-6 text-center text-muted-foreground">
          Waiting for agent data...
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle>Score Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
              <XAxis dataKey="name" stroke="#888" tick={{fill: '#888'}} />
              <YAxis domain={[-1, 1]} stroke="#888" tick={{fill: '#888'}} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }}
                itemStyle={{ color: '#fff' }}
                formatter={(value: any) => typeof value === 'number' ? value.toFixed(2) : value}
              />
              <ReferenceLine y={0} stroke="#555" />
              <Bar dataKey="score" radius={[4, 4, 4, 4]}>
                {
                  data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.score > 0 ? '#22c55e' : '#ef4444'} />
                  ))
                }
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
