"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from 'next-themes';
import { Sun, Moon } from 'lucide-react';

export function TopNavBar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Avoid hydration mismatch by waiting for mount
  useEffect(() => {
    setMounted(true);
  }, []);

  const navItems = [
    { name: 'Screener', path: '/' },
    { name: 'Overview', path: '/overview' },
    { name: 'Divergence', path: '/divergence' },
    { name: 'Agent Details', path: '/agent-details' },
    { name: 'Narrative', path: '/narrative' },
  ];

  return (
    <nav className="hidden md:flex fixed top-0 w-full z-50 justify-between items-center px-margin-desktop h-20 max-w-container-max mx-auto bg-surface/80 backdrop-blur-[12px] border-b border-white/5">
      <div className="flex gap-4">
        <div className="text-body-lg text-primary mr-12 tracking-[0.02em] font-headline-md italic">StockLens</div>
        {navItems.map((item) => {
          const isActive = pathname === item.path;
          return (
            <Link
              key={item.name}
              href={item.path}
              className={`text-label-caps uppercase transition-colors px-4 py-2 relative flex flex-col items-center justify-center ${
                isActive ? 'text-primary' : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              {item.name}
              {isActive && (
                <span className="w-1 h-1 bg-primary rounded-full absolute bottom-0" />
              )}
            </Link>
          );
        })}
      </div>
      <div className="flex items-center gap-4">
        {mounted && (
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-2 rounded-full hover:bg-surface-variant transition-colors flex items-center justify-center text-on-surface-variant hover:text-primary"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        )}
      </div>
    </nav>
  );
}
