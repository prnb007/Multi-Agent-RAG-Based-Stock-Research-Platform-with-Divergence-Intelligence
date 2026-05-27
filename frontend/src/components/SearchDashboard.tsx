"use client"

import React, { useRef } from 'react';
import { useAnalysis } from '@/hooks/useAnalysis';
import { AgentCard } from './AgentCard';
import { SynthesisPanel } from './SynthesisPanel';
import { ScoreChart } from './ScoreChart';
import { DivergencePanel } from './DivergencePanel';
import { NarrativeTracker } from './NarrativeTracker';
import { motion } from 'framer-motion';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

const AGENT_NAMES = ['fundamentals', 'sentiment', 'insider', 'technical', 'macro'];

export function SearchDashboard() {
  const { ticker, setTicker, isAnalyzing, agents, synthesis, error, progress, analyzeTicker } = useAnalysis();
  const searchInputRef = useRef<HTMLInputElement>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      analyzeTicker(ticker.toUpperCase());
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8">
      <div className="text-center space-y-4 max-w-2xl mx-auto mb-12">
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          StockLens
        </h1>
        <p className="text-muted-foreground text-lg">
          Multi-agent AI stock research with Divergence Intelligence.
        </p>
        
        <form onSubmit={handleSearch} className="relative mt-8 group">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <span className="material-symbols-outlined h-5 w-5 text-[20px] text-muted-foreground group-focus-within:text-primary transition-colors">search</span>
          </div>
          <input
            type="text"
            className="block w-full pl-12 pr-4 py-4 bg-secondary/50 border border-white/10 rounded-2xl text-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none"
            placeholder="Enter a ticker (e.g. AAPL, TSLA)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            disabled={isAnalyzing}
          />
          <button 
            type="submit"
            disabled={isAnalyzing || !ticker.trim()}
            className="absolute inset-y-2 right-2 px-6 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 disabled:opacity-70 transition-all flex items-center justify-center min-w-[120px]"
          >
            {isAnalyzing ? (
              <span className="material-symbols-outlined h-5 w-5 text-[20px] animate-spin">sync</span>
            ) : (
              'Analyze'
            )}
          </button>
        </form>
        {error && (
          <div className="text-red-500 mt-4 text-sm bg-red-500/10 py-2 rounded-lg border border-red-500/20">
            {error}
          </div>
        )}
      </div>

      {(isAnalyzing || Object.keys(agents).length > 0) && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          {isAnalyzing && (
            <div className="max-w-md mx-auto space-y-2">
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Gathering intelligence...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}

          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-3 md:w-auto md:inline-flex md:grid-cols-none">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="divergence">Divergence</TabsTrigger>
              <TabsTrigger value="agents">Agent Details</TabsTrigger>
            </TabsList>
            
            <TabsContent value="overview" className="space-y-6 mt-6">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}>
                {synthesis ? (
                  <SynthesisPanel synthesis={synthesis} agents={agents} ticker={ticker} />
                ) : (
                  <div className="p-12 text-center border rounded-xl bg-card/30 border-dashed text-muted-foreground">
                    Synthesis report will appear here once all agents complete their analysis.
                  </div>
                )}
                
                {synthesis && <ScoreChart agents={Object.values(agents)} overallScore={synthesis.overall_score} />}
                
                <NarrativeTracker agents={agents} />
              </motion.div>
            </TabsContent>
            
            <TabsContent value="divergence" className="mt-6">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}>
                {synthesis ? (
                  <DivergencePanel 
                    agents={Object.values(agents)} 
                    divergenceScore={synthesis.divergence_score} 
                    highestGapPair={synthesis.highest_gap_pair} 
                  />
                ) : (
                  <div className="p-12 text-center border rounded-xl bg-card/30 border-dashed text-muted-foreground">
                    Divergence intelligence will appear here once all agents complete their analysis.
                  </div>
                )}
              </motion.div>
            </TabsContent>

            <TabsContent value="agents" className="mt-6">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {AGENT_NAMES.map(name => (
                  <AgentCard 
                    key={name}
                    name={name}
                    ticker={ticker}
                    data={agents[name]}
                    isLoading={isAnalyzing && !agents[name]}
                  />
                ))}
              </motion.div>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}
