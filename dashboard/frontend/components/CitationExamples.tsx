'use client';

import { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  SearchX,
} from 'lucide-react';

type Severity = 'critical' | 'high' | 'medium';

interface Finding {
  severity: Severity;
  title: string;
  description: string;
}

interface CitationExamplesProps {
  findings: Finding[];
}

const SEVERITY_CONFIG: Record<
  Severity,
  {
    borderClass: string;
    badgeBg: string;
    badgeText: string;
    badgeBorder: string;
    headerBg: string;
    icon: React.ElementType;
    iconColor: string;
    label: string;
    citationNote: string;
  }
> = {
  critical: {
    borderClass: 'border-red-700/60',
    badgeBg: 'bg-red-950/70',
    badgeText: 'text-red-400',
    badgeBorder: 'border-red-800',
    headerBg: 'bg-red-950/20',
    icon: AlertCircle,
    iconColor: 'text-red-500',
    label: 'Critical',
    citationNote:
      'Critical issues actively block AI systems from understanding, indexing, or citing your content. Fixing these has the highest immediate impact on your AI visibility score.',
  },
  high: {
    borderClass: 'border-amber-700/60',
    badgeBg: 'bg-amber-950/70',
    badgeText: 'text-amber-400',
    badgeBorder: 'border-amber-800',
    headerBg: 'bg-amber-950/20',
    icon: AlertTriangle,
    iconColor: 'text-amber-500',
    label: 'High Priority',
    citationNote:
      'High-priority issues significantly reduce your chances of being cited by AI models. Addressing these improves your authority and relevance signals across all major AI platforms.',
  },
  medium: {
    borderClass: 'border-slate-600',
    badgeBg: 'bg-slate-700/60',
    badgeText: 'text-slate-300',
    badgeBorder: 'border-slate-600',
    headerBg: 'bg-slate-700/20',
    icon: Info,
    iconColor: 'text-slate-400',
    label: 'Medium',
    citationNote:
      'Medium-severity improvements strengthen your overall GEO profile. While not urgent, resolving these incrementally builds the trust and clarity that AI models reward with citations.',
  },
};

const SEVERITY_ORDER: Record<Severity, number> = { critical: 0, high: 1, medium: 2 };

interface FindingCardProps {
  finding: Finding;
  rank: number;
}

function FindingCard({ finding, rank }: FindingCardProps) {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERITY_CONFIG[finding.severity];
  const SeverityIcon = config.icon;

  const shortDescription =
    finding.description.length > 120
      ? finding.description.slice(0, 120).trim() + '\u2026'
      : finding.description;

  const isLong = finding.description.length > 120;

  return (
    <div
      className={`bg-slate-800 border rounded-xl overflow-hidden transition-all hover:border-opacity-80 ${config.borderClass}`}
    >
      {/* Card header */}
      <div className={`px-4 py-3 flex items-start gap-3 ${config.headerBg}`}>
        <div className="mt-0.5 shrink-0">
          <SeverityIcon size={16} className={config.iconColor} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span
              className={`inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full border ${config.badgeBg} ${config.badgeText} ${config.badgeBorder}`}
            >
              {config.label}
            </span>
            <span className="text-xs text-slate-500">#{rank}</span>
          </div>
          <p className="text-white font-semibold text-sm leading-snug">{finding.title}</p>
        </div>
      </div>

      {/* Description */}
      <div className="px-4 py-3 border-t border-slate-700/60">
        <p className="text-slate-300 text-sm leading-relaxed">
          {expanded || !isLong ? finding.description : shortDescription}
        </p>

        {isLong && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 mt-2 transition-colors font-medium"
          >
            {expanded ? (
              <>
                <ChevronUp size={13} />
                Show less
              </>
            ) : (
              <>
                <ChevronDown size={13} />
                Read more
              </>
            )}
          </button>
        )}
      </div>

      {/* Why this matters section */}
      <div className="mx-4 mb-4 rounded-lg bg-slate-700/30 border border-slate-700 px-3.5 py-3">
        <div className="flex items-center gap-1.5 mb-1.5">
          <Lightbulb size={13} className="text-indigo-400 shrink-0" />
          <span className="text-xs font-semibold text-indigo-300 uppercase tracking-wide">
            Why this matters for AI citations
          </span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">{config.citationNote}</p>
      </div>
    </div>
  );
}

export function CitationExamples({ findings }: CitationExamplesProps) {
  if (!findings || findings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 px-6 bg-slate-800/40 border border-slate-700 rounded-xl gap-3">
        <div className="w-12 h-12 rounded-full bg-slate-700/60 border border-slate-600 flex items-center justify-center">
          <SearchX size={22} className="text-slate-500" />
        </div>
        <div className="text-center">
          <p className="text-slate-300 font-medium text-sm">No findings to display</p>
          <p className="text-slate-500 text-xs mt-1">Run an audit to surface actionable issues</p>
        </div>
      </div>
    );
  }

  // Sort by severity, then take top 3
  const topFindings = [...findings]
    .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])
    .slice(0, 3);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-slate-200 font-semibold text-sm tracking-wide uppercase">
          Top Actionable Findings
        </h3>
        {findings.length > 3 && (
          <span className="text-xs text-slate-500">
            Showing 3 of {findings.length}
          </span>
        )}
      </div>

      <div className="space-y-3">
        {topFindings.map((finding, index) => (
          <FindingCard
            key={`${finding.severity}-${index}`}
            finding={finding}
            rank={index + 1}
          />
        ))}
      </div>
    </div>
  );
}
