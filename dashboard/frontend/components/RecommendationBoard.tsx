'use client';

import { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Circle,
  ChevronRight,
  CheckCircle2,
  Clock,
  Zap,
} from 'lucide-react';

interface Recommendation {
  id: string;
  clientId: string;
  auditId: string;
  category: string;
  priority: number; // 1=critical, 2=important, 3=nice-to-have
  title: string;
  description: string;
  effort: string;
  impact: string;
  status: string; // "pending"|"in_progress"|"done"
}

interface RecommendationBoardProps {
  recommendations: Recommendation[];
  onStatusChange: (id: string, status: string) => void;
}

const STATUS_ORDER = ['pending', 'in_progress', 'done'] as const;
type Status = typeof STATUS_ORDER[number];

const STATUS_CONFIG: Record<
  Status,
  { label: string; headerClass: string; badgeClass: string; dotClass: string; icon: React.ElementType }
> = {
  pending: {
    label: 'Pending',
    headerClass: 'border-slate-600 bg-slate-700/40',
    badgeClass: 'bg-slate-700 text-slate-300',
    dotClass: 'bg-slate-500',
    icon: Circle,
  },
  in_progress: {
    label: 'In Progress',
    headerClass: 'border-amber-700/60 bg-amber-950/30',
    badgeClass: 'bg-amber-900/60 text-amber-300',
    dotClass: 'bg-amber-400',
    icon: Clock,
  },
  done: {
    label: 'Done',
    headerClass: 'border-emerald-700/60 bg-emerald-950/30',
    badgeClass: 'bg-emerald-900/60 text-emerald-300',
    dotClass: 'bg-emerald-400',
    icon: CheckCircle2,
  },
};

const PRIORITY_CONFIG: Record<
  number,
  { label: string; className: string; icon: React.ElementType }
> = {
  1: { label: 'P1', className: 'bg-red-950/70 border-red-800 text-red-400', icon: AlertCircle },
  2: { label: 'P2', className: 'bg-amber-950/70 border-amber-800 text-amber-400', icon: AlertTriangle },
  3: { label: 'P3', className: 'bg-slate-700/70 border-slate-600 text-slate-400', icon: Circle },
};

function getNextStatus(current: string): string {
  const idx = STATUS_ORDER.indexOf(current as Status);
  if (idx === -1 || idx === STATUS_ORDER.length - 1) return current;
  return STATUS_ORDER[idx + 1];
}

function getNextStatusLabel(current: string): string {
  const next = getNextStatus(current);
  if (next === current) return 'Done';
  return STATUS_CONFIG[next as Status]?.label ?? next;
}

interface RecommendationCardProps {
  rec: Recommendation;
  onStatusChange: (id: string, status: string) => void;
}

function RecommendationCard({ rec, onStatusChange }: RecommendationCardProps) {
  const priority = PRIORITY_CONFIG[rec.priority] ?? PRIORITY_CONFIG[3];
  const PriorityIcon = priority.icon;
  const isDone = rec.status === 'done';
  const nextStatus = getNextStatus(rec.status);
  const nextStatusLabel = getNextStatusLabel(rec.status);

  return (
    <div
      className={`bg-slate-800 border border-slate-700 rounded-lg p-3.5 space-y-2.5 hover:border-slate-600 transition-all ${
        isDone ? 'opacity-60' : ''
      }`}
    >
      {/* Header: priority + category */}
      <div className="flex items-center gap-2 flex-wrap">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold border ${priority.className}`}
        >
          <PriorityIcon size={10} />
          {priority.label}
        </span>
        <span className="px-2 py-0.5 rounded-full text-xs bg-slate-700/80 text-slate-400 border border-slate-600">
          {rec.category}
        </span>
      </div>

      {/* Title */}
      <p className={`text-sm font-semibold leading-snug ${isDone ? 'line-through text-slate-400' : 'text-slate-100'}`}>
        {rec.title}
      </p>

      {/* Effort + Impact */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Zap size={11} className="text-amber-500" />
          <span>Effort:</span>
          <span className="text-slate-300 font-medium">{rec.effort}</span>
        </div>
        <div className="w-px h-3 bg-slate-600" />
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <ChevronRight size={11} className="text-emerald-500" />
          <span>Impact:</span>
          <span className="text-slate-300 font-medium">{rec.impact}</span>
        </div>
      </div>

      {/* Advance button */}
      {!isDone && (
        <button
          onClick={() => onStatusChange(rec.id, nextStatus)}
          className="w-full text-xs font-medium py-1.5 rounded-lg border border-indigo-700/60 bg-indigo-950/40 text-indigo-300 hover:bg-indigo-900/40 hover:border-indigo-600 hover:text-indigo-200 transition-all flex items-center justify-center gap-1.5"
        >
          <ChevronRight size={13} />
          Move to {nextStatusLabel}
        </button>
      )}

      {isDone && (
        <div className="flex items-center gap-1.5 text-xs text-emerald-500 font-medium">
          <CheckCircle2 size={13} />
          Completed
        </div>
      )}
    </div>
  );
}

export function RecommendationBoard({
  recommendations,
  onStatusChange,
}: RecommendationBoardProps) {
  const [localRecs, setLocalRecs] = useState<Recommendation[]>(recommendations);

  const handleStatusChange = (id: string, status: string) => {
    setLocalRecs((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status } : r))
    );
    onStatusChange(id, status);
  };

  const getColumn = (status: Status) =>
    localRecs
      .filter((r) => r.status === status)
      .sort((a, b) => a.priority - b.priority);

  if (!localRecs.length) {
    return (
      <div className="flex flex-col items-center justify-center h-48 bg-slate-800/50 rounded-xl border border-slate-700">
        <CheckCircle2 className="text-slate-600 mb-2" size={32} />
        <p className="text-slate-400 text-sm">No recommendations yet</p>
        <p className="text-slate-500 text-xs mt-1">Run an audit to generate recommendations</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {STATUS_ORDER.map((status) => {
        const config = STATUS_CONFIG[status];
        const StatusIcon = config.icon;
        const column = getColumn(status);

        return (
          <div key={status} className="flex flex-col gap-3">
            {/* Column header */}
            <div
              className={`flex items-center justify-between px-3 py-2 rounded-lg border ${config.headerClass}`}
            >
              <div className="flex items-center gap-2">
                <StatusIcon size={14} className={
                  status === 'pending' ? 'text-slate-400' :
                  status === 'in_progress' ? 'text-amber-400' :
                  'text-emerald-400'
                } />
                <span className="text-sm font-semibold text-slate-200">{config.label}</span>
              </div>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${config.badgeClass}`}>
                {column.length}
              </span>
            </div>

            {/* Cards */}
            <div className="flex flex-col gap-2.5 min-h-[80px]">
              {column.length === 0 ? (
                <div className="flex items-center justify-center h-20 rounded-lg border border-dashed border-slate-700 text-slate-600 text-xs">
                  No items
                </div>
              ) : (
                column.map((rec) => (
                  <RecommendationCard
                    key={rec.id}
                    rec={rec}
                    onStatusChange={handleStatusChange}
                  />
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
