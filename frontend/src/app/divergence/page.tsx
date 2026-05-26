import React from 'react';
import { DivergenceMatrix } from '@/components/DivergenceMatrix';

export default function DivergencePage() {
  return (
    <main className="pt-24 pb-24 px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto w-full min-h-screen">
      <div className="mb-16">
        <h1 className="font-headline-md text-display-lg-mobile md:text-display-lg text-primary mb-2">Pairwise Agent Divergence</h1>
        <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl mt-4">
          Analyzing consensus gaps across specialized intelligence vectors. Highlighted cells indicate significant conflicting signals between agents evaluating the same asset.
        </p>
      </div>
      
      <DivergenceMatrix />
    </main>
  );
}
