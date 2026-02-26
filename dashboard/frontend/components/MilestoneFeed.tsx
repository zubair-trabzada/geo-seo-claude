'use client';

import { format, parseISO, isValid } from 'date-fns';
import { Trophy, Star, Globe, FileCode2, TrendingUp } from 'lucide-react';

interface AuditEntry {
  timestamp: string;
  geoScore: number;
  rawData: string;
  isBaseline: boolean;
}

interface MilestoneFeedProps {
  audits: AuditEntry[];
  currentScore: number;
  baselineScore: number;
}

interface Milestone {
  id: string;
  icon: React.ElementType;
  iconColor: string;
  iconBg: string;
  text: string;
  sub?: string;
  date: string;
  highlight?: boolean;
}

const SCORE_MILESTONES = [50, 60, 70, 80];

function formatDate(dateStr: string): string {
  try {
    const parsed = parseISO(dateStr);
    if (isValid(parsed)) return format(parsed, 'MMM d, yyyy');
    return dateStr;
  } catch {
    return dateStr;
  }
}

function safeParse(raw: string): Record<string, any> | null {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function extractPlatforms(data: Record<string, any>): Record<string, number> {
  return data?.platforms ?? {};
}

function extractLlmsTxt(data: Record<string, any>): boolean {
  // Check various possible paths for llms.txt status
  return (
    data?.crawler_access?.llms_txt_present === true ||
    data?.crawler_access?.llmstxt === true ||
    data?.llms_txt === true ||
    false
  );
}

function buildMilestones(audits: AuditEntry[], currentScore: number, baselineScore: number): Milestone[] {
  const milestones: Milestone[] = [];
  const sorted = [...audits].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  if (sorted.length === 0) return milestones;

  // Track state across audits
  const seenScoreMilestones = new Set<number>();
  const seenPlatforms = new Set<string>();
  let llmsTxtSeen = false;

  sorted.forEach((audit, index) => {
    const data = safeParse(audit.rawData);

    // Baseline milestone
    if (audit.isBaseline || index === 0) {
      milestones.push({
        id: `baseline-${audit.timestamp}`,
        icon: Star,
        iconColor: 'text-amber-300',
        iconBg: 'bg-amber-950/60 border-amber-700',
        text: 'Baseline established',
        sub: `Starting GEO score: ${audit.geoScore}`,
        date: formatDate(audit.timestamp),
        highlight: true,
      });
    }

    // Score crossing milestones
    for (const threshold of SCORE_MILESTONES) {
      if (audit.geoScore >= threshold && !seenScoreMilestones.has(threshold)) {
        seenScoreMilestones.add(threshold);
        if (!audit.isBaseline || index > 0) {
          milestones.push({
            id: `score-${threshold}-${audit.timestamp}`,
            icon: Trophy,
            iconColor: 'text-yellow-300',
            iconBg: 'bg-yellow-950/60 border-yellow-700',
            text: `Crossed the ${threshold} milestone!`,
            sub: `GEO score reached ${audit.geoScore}`,
            date: formatDate(audit.timestamp),
            highlight: true,
          });
        }
      }
    }

    // Platform first-citation milestones
    if (data) {
      const platforms = extractPlatforms(data);
      for (const [platform, score] of Object.entries(platforms)) {
        if (typeof score === 'number' && score > 0 && !seenPlatforms.has(platform)) {
          seenPlatforms.add(platform);
          if (index > 0) {
            milestones.push({
              id: `platform-${platform}-${audit.timestamp}`,
              icon: Globe,
              iconColor: 'text-indigo-300',
              iconBg: 'bg-indigo-950/60 border-indigo-700',
              text: `First citation on ${platform}!`,
              sub: `Score: ${score}`,
              date: formatDate(audit.timestamp),
            });
          } else {
            seenPlatforms.add(platform);
          }
        }
      }

      // llms.txt deployment
      const hasLlmsTxt = extractLlmsTxt(data);
      if (hasLlmsTxt && !llmsTxtSeen) {
        llmsTxtSeen = true;
        if (index > 0) {
          milestones.push({
            id: `llmstxt-${audit.timestamp}`,
            icon: FileCode2,
            iconColor: 'text-emerald-300',
            iconBg: 'bg-emerald-950/60 border-emerald-700',
            text: 'llms.txt deployed!',
            sub: 'AI crawlers can now read your site manifest',
            date: formatDate(audit.timestamp),
          });
        }
      }
    }
  });

  // Net improvement from baseline (show as summary at end)
  const improvement = currentScore - baselineScore;
  if (improvement > 0 && sorted.length > 1) {
    const latest = sorted[sorted.length - 1];
    milestones.push({
      id: 'improvement-total',
      icon: TrendingUp,
      iconColor: 'text-emerald-300',
      iconBg: 'bg-emerald-950/60 border-emerald-700',
      text: `+${improvement} points since you started`,
      sub: `From ${baselineScore} to ${currentScore}`,
      date: formatDate(latest.timestamp),
      highlight: true,
    });
  }

  // Sort by date descending so newest is at top
  return milestones.sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
}

interface MilestoneItemProps {
  milestone: Milestone;
  isLast: boolean;
}

function MilestoneItem({ milestone, isLast }: MilestoneItemProps) {
  const Icon = milestone.icon;

  return (
    <div className="flex gap-3 group">
      {/* Icon + connector */}
      <div className="flex flex-col items-center">
        <div
          className={`w-9 h-9 rounded-full border-2 flex items-center justify-center shrink-0 z-10 transition-transform group-hover:scale-110 ${milestone.iconBg}`}
        >
          <Icon size={16} className={milestone.iconColor} />
        </div>
        {!isLast && <div className="w-px flex-1 bg-slate-700 mt-1 mb-0" />}
      </div>

      {/* Content */}
      <div className={`pb-5 flex-1 min-w-0 ${isLast ? '' : ''}`}>
        <div
          className={`rounded-lg px-3.5 py-2.5 border transition-colors group-hover:border-slate-600 ${
            milestone.highlight
              ? 'bg-slate-800 border-slate-600'
              : 'bg-slate-800/50 border-slate-700'
          }`}
        >
          <p
            className={`text-sm font-semibold leading-snug ${
              milestone.highlight ? 'text-white' : 'text-slate-200'
            }`}
          >
            {milestone.text}
          </p>
          {milestone.sub && (
            <p className="text-xs text-slate-400 mt-0.5">{milestone.sub}</p>
          )}
          <p className="text-xs text-slate-500 mt-1.5">{milestone.date}</p>
        </div>
      </div>
    </div>
  );
}

export function MilestoneFeed({ audits, currentScore, baselineScore }: MilestoneFeedProps) {
  const milestones = buildMilestones(audits, currentScore, baselineScore);

  if (milestones.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 px-6 bg-slate-800/40 border border-slate-700 rounded-xl gap-3">
        <div className="w-12 h-12 rounded-full bg-slate-700/60 border border-slate-600 flex items-center justify-center">
          <Trophy size={22} className="text-slate-500" />
        </div>
        <div className="text-center">
          <p className="text-slate-300 font-medium text-sm">Your milestones will appear here</p>
          <p className="text-slate-500 text-xs mt-1">as you improve your GEO score</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      <h3 className="text-slate-200 font-semibold text-sm tracking-wide uppercase mb-4">
        Achievement Timeline
      </h3>
      <div>
        {milestones.map((milestone, index) => (
          <MilestoneItem
            key={milestone.id}
            milestone={milestone}
            isLast={index === milestones.length - 1}
          />
        ))}
      </div>
    </div>
  );
}
