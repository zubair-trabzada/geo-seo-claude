'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format, parseISO, isValid } from 'date-fns';
import { TrendingUp } from 'lucide-react';

interface DataPoint {
  date: string;
  score: number;
  isBaseline?: boolean;
}

interface ProgressChartProps {
  data: Array<DataPoint>;
}

function formatDateSafe(dateStr: string): string {
  try {
    const parsed = parseISO(dateStr);
    if (isValid(parsed)) return format(parsed, 'MMM d');
    return dateStr;
  } catch {
    return dateStr;
  }
}

function formatDateFull(dateStr: string): string {
  try {
    const parsed = parseISO(dateStr);
    if (isValid(parsed)) return format(parsed, 'MMM d, yyyy');
    return dateStr;
  } catch {
    return dateStr;
  }
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; payload: DataPoint }>;
  label?: string;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const point = payload[0].payload;
  const score = payload[0].value;

  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 shadow-xl">
      <p className="text-slate-400 text-xs mb-1">{formatDateFull(point.date)}</p>
      <p className="text-white font-bold text-lg leading-none">
        {score}
        <span className="text-slate-400 font-normal text-sm ml-1">/ 100</span>
      </p>
      {point.isBaseline && (
        <p className="text-amber-400 text-xs mt-1 font-medium">Baseline audit</p>
      )}
    </div>
  );
}

interface CustomDotProps {
  cx?: number;
  cy?: number;
  payload?: DataPoint;
}

function CustomDot({ cx, cy, payload }: CustomDotProps) {
  if (cx === undefined || cy === undefined || !payload) return null;

  if (payload.isBaseline) {
    return (
      <g>
        <circle cx={cx} cy={cy} r={7} fill="#f59e0b" stroke="#1e293b" strokeWidth={2} />
        <circle cx={cx} cy={cy} r={3} fill="#1e293b" />
      </g>
    );
  }

  return (
    <circle cx={cx} cy={cy} r={5} fill="#6366f1" stroke="#1e293b" strokeWidth={2} />
  );
}

export function ProgressChart({ data }: ProgressChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 bg-slate-800/50 rounded-xl border border-slate-700">
        <TrendingUp className="text-slate-600 mb-2" size={32} />
        <p className="text-slate-400 text-sm">No audit data yet</p>
      </div>
    );
  }

  if (data.length === 1) {
    const point = data[0];
    return (
      <div className="flex flex-col items-center justify-center h-48 bg-slate-800/50 rounded-xl border border-slate-700 gap-3 px-6">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-amber-400 shrink-0" />
          <div>
            <p className="text-white font-semibold text-sm">
              Baseline set — Score: <span className="text-indigo-400">{point.score}</span>
            </p>
            <p className="text-slate-500 text-xs">{formatDateFull(point.date)}</p>
          </div>
        </div>
        <p className="text-slate-400 text-xs text-center">
          More data coming with each audit
        </p>
      </div>
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    formattedDate: formatDateSafe(d.date),
  }));

  const minScore = Math.max(0, Math.min(...data.map((d) => d.score)) - 10);
  const maxScore = Math.min(100, Math.max(...data.map((d) => d.score)) + 10);

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 12, right: 16, left: 0, bottom: 8 }}
        >
          <defs>
            <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="100%" stopColor="#6366f1" />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#1e293b"
            vertical={false}
          />

          <XAxis
            dataKey="formattedDate"
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
          />

          <YAxis
            domain={[minScore, maxScore]}
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={32}
          />

          <Tooltip content={<CustomTooltip />} />

          <Line
            type="monotone"
            dataKey="score"
            stroke="url(#lineGradient)"
            strokeWidth={2.5}
            dot={<CustomDot />}
            activeDot={{ r: 7, fill: '#6366f1', stroke: '#1e293b', strokeWidth: 2 }}
            animationDuration={1000}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
