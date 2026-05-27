"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface AgentData {
  agent: string;
  score: number;
  confidence: number;
  summary: string;
  evidence: string[];
  raw_data?: any;
}

export interface SynthesisData {
  divergence_score: number;
  highest_gap_pair: string;
  bull_thesis: string;
  bear_thesis: string;
  overall_score: number;
}

interface AnalysisContextType {
  ticker: string;
  setTicker: (ticker: string) => void;
  isAnalyzing: boolean;
  agents: Record<string, AgentData>;
  synthesis: SynthesisData | null;
  error: string | null;
  progress: number;
  analyzeTicker: (ticker: string) => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [ticker, setTicker] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [agents, setAgents] = useState<Record<string, AgentData>>({});
  const [synthesis, setSynthesis] = useState<SynthesisData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const analyzeTicker = useCallback((targetTicker: string) => {
    setIsAnalyzing(true);
    setAgents({});
    setSynthesis(null);
    setError(null);
    setProgress(10);

    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const eventSource = new EventSource(`${apiBase}/analyze/${targetTicker}`);

    eventSource.addEventListener('agent_complete', (event) => {
      try {
        const data = JSON.parse(event.data) as AgentData;
        setAgents((prev) => {
          const newAgents = { ...prev, [data.agent]: data };
          const doneCount = Object.keys(newAgents).length;
          setProgress(10 + (doneCount / 5) * 80);
          return newAgents;
        });
      } catch (err) {
        console.error("Failed to parse agent_complete event:", err);
      }
    });

    eventSource.addEventListener('report_complete', (event) => {
      try {
        const data = JSON.parse(event.data) as SynthesisData;
        setSynthesis(data);
        setProgress(100);
        setIsAnalyzing(false);
        eventSource.close();
      } catch (err) {
        console.error("Failed to parse report_complete event:", err);
      }
    });

    eventSource.addEventListener('error', (event) => {
      let errorMessage = "Connection to analysis server failed.";
      if ((event as any).data) {
        try {
          const data = JSON.parse((event as any).data);
          if (data.error) errorMessage = data.error;
        } catch (e) {
            // Ignored
        }
      }
      setError(errorMessage);
      setIsAnalyzing(false);
      eventSource.close();
    });

  }, []);

  return (
    <AnalysisContext.Provider
      value={{
        ticker,
        setTicker,
        isAnalyzing,
        agents,
        synthesis,
        error,
        progress,
        analyzeTicker
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysisContext() {
  const context = useContext(AnalysisContext);
  if (context === undefined) {
    throw new Error('useAnalysisContext must be used within an AnalysisProvider');
  }
  return context;
}
