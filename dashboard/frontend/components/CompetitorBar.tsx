'use client';

import { useEffect, useRef, useState } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface CompetitorBarProps {
  clientName: string;
  clientScore: number;
  competitorName: string;
  competitorScore: number;
}

interface AnimatedBarProps {
  name: string;
  score: number;
  color: 'client' | 'competitor';
  delay?: number;
  maxScore: number;
}

function AnimatedBar({ name, score, color, delay = 0, maxScore }: AnimatedBarProps) {
  const [width, setWidth] = useState(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rafRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const duration = 900;

  const targetWidth = (score / 100) * 100; // percentage

  useEffect(() => {
    timeoutRef.current = setTimeout(() => {
      const animate = (timestamp: number) => {
        if (startTimeRef.current === null) startTimeRef.current = timestamp;
        const elapsed = timestamp - startTimeRef.current;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setWidth(eased * targetWidth);
        if (progress < 1) {
          rafRef.current = requestAnimationFrame(animate);
        }
      };
      rafRef.current = requestAnimationFrame(animate);
    }, delay);

    return () => {
      if (timeoutRef.current !== null) clearTimeout(timeoutRef.current);
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [score]);

  const isClient = color === 'client';

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isClient ? 'bg-indigo-400' : 'bg-slate-400'
            }`}
          />
          <span className={`font-medium ${isClient ? 'text-slate-100' : 'text-slate-300'}`}>
            {name}
          </span>
        </div>
        <span
          className={`font-bold tabular-nums ${
            isClient ? 'text-indigo-300' : 'text-slate-300'
          }`}
        >
          {score}
        </span>
      </div>

      {/* Bar track */}
      <div className="h-5 bg-slate-700/60 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full relative ${
            isClient
              ? 'bg-gradient-to-r from-indigo-600 to-indigo-400'
              : 'bg-gradient-to-r from-slate-600 to-slate-400'
          }`}
          style={{ width: `${width}%` }}
        >
          {/* Shimmer effect */}
          <div className="absolute inset-0 overflow-hidden rounded-full">
            <div
              className={`absolute inset-y-0 w-12 bg-white/10 skew-x-12 -translate-x-full ${
                isClient ? 'animate-[shimmer_2s_ease-in-out_1.2s_1]' : ''
              }`}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export function CompetitorBar({
  clientName,
  clientScore,
  competitorName,
  competitorScore,
}: CompetitorBarProps) {
  const diff = clientScore - competitorScore;
  const absDiff = Math.abs(diff);
  const maxScore = Math.max(clientScore, competitorScore, 1);

  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-slate-200 font-semibold text-sm tracking-wide uppercase">
          Competitor Comparison
        </h3>
        <div
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
            diff > 0
              ? 'bg-emerald-950/60 border-emerald-800 text-emerald-400'
              : diff < 0
              ? 'bg-red-950/60 border-red-800 text-red-400'
              : 'bg-slate-700/60 border-slate-600 text-slate-400'
          }`}
        >
          {diff > 0 ? (
            <TrendingUp size={12} />
          ) : diff < 0 ? (
            <TrendingDown size={12} />
          ) : (
            <Minus size={12} />
          )}
          {diff === 0
            ? 'Tied'
            : diff > 0
            ? `${absDiff} pts ahead`
            : `${absDiff} pts behind`}
        </div>
      </div>

      {/* Bars */}
      <div className="space-y-4">
        <AnimatedBar
          name={clientName}
          score={clientScore}
          color="client"
          delay={100}
          maxScore={maxScore}
        />
        <AnimatedBar
          name={competitorName}
          score={competitorScore}
          color="competitor"
          delay={300}
          maxScore={maxScore}
        />
      </div>

      {/* Gap callout */}
      {diff !== 0 && (
        <div
          className={`flex items-start gap-2 text-xs rounded-lg px-3 py-2.5 border ${
            diff > 0
              ? 'bg-emerald-950/30 border-emerald-900/60 text-emerald-300'
              : 'bg-red-950/30 border-red-900/60 text-red-300'
          }`}
        >
          {diff > 0 ? (
            <>
              <TrendingUp size={13} className="shrink-0 mt-0.5" />
              <span>
                <span className="font-semibold">{clientName}</span> leads{' '}
                <span className="font-semibold">{competitorName}</span> by{' '}
                <span className="font-semibold">{absDiff} points</span> — keep building on this
                advantage.
              </span>
            </>
          ) : (
            <>
              <TrendingDown size={13} className="shrink-0 mt-0.5" />
              <span>
                <span className="font-semibold">{competitorName}</span> is{' '}
                <span className="font-semibold">{absDiff} points</span> ahead. Close the gap
                with targeted GEO improvements.
              </span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
