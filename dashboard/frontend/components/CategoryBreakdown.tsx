'use client';

import { useEffect, useRef, useState } from 'react';
import {
  Brain,
  Award,
  FileText,
  Settings,
  Code2,
  Layers,
} from 'lucide-react';

interface ScoreBreakdown {
  ai_citability: number;
  brand_authority: number;
  content_eeat: number;
  technical: number;
  schema: number;
  platform_optimization: number;
}

interface CategoryBreakdownProps {
  scores: ScoreBreakdown;
}

interface CategoryConfig {
  key: keyof ScoreBreakdown;
  label: string;
  icon: React.ElementType;
  description: string;
}

const CATEGORIES: CategoryConfig[] = [
  {
    key: 'ai_citability',
    label: 'AI Citability',
    icon: Brain,
    description: 'How likely AI models are to cite your content',
  },
  {
    key: 'brand_authority',
    label: 'Brand Authority',
    icon: Award,
    description: 'Entity recognition and domain trust signals',
  },
  {
    key: 'content_eeat',
    label: 'Content & E-E-A-T',
    icon: FileText,
    description: 'Experience, Expertise, Authoritativeness, Trustworthiness',
  },
  {
    key: 'technical',
    label: 'Technical SEO',
    icon: Settings,
    description: 'Crawlability, speed, and technical foundations',
  },
  {
    key: 'schema',
    label: 'Schema Markup',
    icon: Code2,
    description: 'Structured data for AI and search engines',
  },
  {
    key: 'platform_optimization',
    label: 'Platform Optimization',
    icon: Layers,
    description: 'Tailored signals for each AI platform',
  },
];

function getBarColor(score: number): string {
  if (score < 40) return 'from-red-700 to-red-500';
  if (score < 60) return 'from-amber-700 to-amber-500';
  if (score < 80) return 'from-emerald-700 to-emerald-500';
  return 'from-indigo-700 to-indigo-500';
}

function getScoreTextColor(score: number): string {
  if (score < 40) return 'text-red-400';
  if (score < 60) return 'text-amber-400';
  if (score < 80) return 'text-emerald-400';
  return 'text-indigo-400';
}

function getIconColor(score: number): string {
  if (score < 40) return 'text-red-500';
  if (score < 60) return 'text-amber-500';
  if (score < 80) return 'text-emerald-500';
  return 'text-indigo-500';
}

interface AnimatedBarRowProps {
  config: CategoryConfig;
  score: number;
  index: number;
}

function AnimatedBarRow({ config, score, index }: AnimatedBarRowProps) {
  const [width, setWidth] = useState(0);
  const rafRef = useRef<number | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const duration = 800;
  const delay = index * 80;

  useEffect(() => {
    timeoutRef.current = setTimeout(() => {
      const animate = (timestamp: number) => {
        if (startTimeRef.current === null) startTimeRef.current = timestamp;
        const elapsed = timestamp - startTimeRef.current;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setWidth(eased * score);
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

  const Icon = config.icon;
  const barGradient = getBarColor(score);
  const scoreTextColor = getScoreTextColor(score);
  const iconColor = getIconColor(score);

  return (
    <div className="group flex items-center gap-3">
      {/* Icon */}
      <div
        className={`w-8 h-8 rounded-lg bg-slate-700/60 flex items-center justify-center shrink-0 group-hover:bg-slate-700 transition-colors ${iconColor}`}
      >
        <Icon size={15} />
      </div>

      {/* Label + bar + score */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-slate-200 text-sm font-medium truncate">{config.label}</span>
          <span className={`text-sm font-bold tabular-nums ml-3 shrink-0 ${scoreTextColor}`}>
            {score}
          </span>
        </div>

        {/* Bar track */}
        <div className="h-2 bg-slate-700/60 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${barGradient} transition-none`}
            style={{ width: `${width}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export function CategoryBreakdown({ scores }: CategoryBreakdownProps) {
  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5">
      <h3 className="text-slate-200 font-semibold text-sm tracking-wide uppercase mb-4">
        Score Breakdown
      </h3>
      <div className="space-y-4">
        {CATEGORIES.map((cat, index) => (
          <AnimatedBarRow
            key={cat.key}
            config={cat}
            score={scores[cat.key] ?? 0}
            index={index}
          />
        ))}
      </div>
    </div>
  );
}
