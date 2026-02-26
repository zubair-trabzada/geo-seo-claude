'use client';

import { useEffect, useState, useRef } from 'react';

interface ScoreGaugeProps {
  score: number;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

const SIZE_MAP = {
  sm: 120,
  md: 180,
  lg: 240,
};

function getColorForScore(score: number): string {
  if (score < 40) return '#ef4444'; // red-500
  if (score < 60) return '#f59e0b'; // amber-500
  if (score < 80) return '#10b981'; // emerald-500
  return '#6366f1'; // indigo-500
}

function getTierLabel(score: number): string {
  if (score < 40) return 'Needs Attention';
  if (score < 60) return 'Developing';
  if (score < 80) return 'Optimized';
  return 'Leader';
}

/**
 * Semi-circle gauge that sits flat at the bottom.
 * The arc sweeps from left (9 o'clock) to right (3 o'clock) going over the top.
 *
 * Coordinate convention (SVG standard: y increases downward):
 *   angle=0   => top    (cx,   cy - r)
 *   angle=90  => right  (cx+r, cy    )
 *   angle=180 => bottom (cx,   cy + r)
 *   angle=-90 => left   (cx-r, cy    )
 *
 * We map score 0→100 to arc sweep 0→180 degrees, starting from the left point.
 */
function arcPath(
  cx: number,
  cy: number,
  r: number,
  /** 0–180: how many degrees of the semicircle to fill (0 = empty, 180 = full) */
  sweepDeg: number
): string {
  if (sweepDeg <= 0) {
    // Just a degenerate point; return empty path segment
    return `M ${cx - r} ${cy}`;
  }

  // Clamp
  const sweep = Math.min(180, sweepDeg);

  // Start is always the left point
  const startX = cx - r;
  const startY = cy;

  // End point: start from left (-180° in standard math), add sweepDeg counter-clockwise
  // In SVG coords (y flipped): left is angle=180° standard => for SVG -90° offset
  // We parameterise simply: the arc starts at (cx-r, cy) and sweeps clockwise by `sweep` degrees.
  const endRad = Math.PI - (sweep * Math.PI) / 180; // start of arc in standard math
  const endX = cx + r * Math.cos(endRad);
  const endY = cy - r * Math.sin(endRad); // negate because SVG y is flipped

  const largeArc = sweep > 180 ? 1 : 0;
  // sweep-flag=1 means clockwise in SVG
  return `M ${startX} ${startY} A ${r} ${r} 0 ${largeArc} 1 ${endX} ${endY}`;
}

export function ScoreGauge({ score, label = 'GEO Score', size = 'md' }: ScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const duration = 1200;

  const px = SIZE_MAP[size];
  const strokeWidth = size === 'sm' ? 8 : size === 'md' ? 12 : 16;
  const cx = px / 2;

  // The arc lives in the top half of the SVG.
  // cy = halfway through the full circle, but we only render the top half.
  // SVG height = radius + strokeWidth padding top and bottom of semicircle.
  const r = px / 2 - strokeWidth;
  const cy = px / 2; // center of the notional full circle

  // SVG canvas: width=px, height=half-circle + stroke padding
  const svgHeight = r + strokeWidth * 2;

  const color = getColorForScore(score);
  const tierLabel = getTierLabel(score);

  const scoreFontSize = size === 'sm' ? 20 : size === 'md' ? 32 : 44;
  const labelFontSize = size === 'sm' ? 9 : size === 'md' ? 12 : 15;
  const tierFontSize = size === 'sm' ? 8 : size === 'md' ? 11 : 13;

  // Text sits just below the centre of the arc (which is at cy in SVG coords,
  // but cy is clipped to svgHeight = r + padding, so cy = r + strokeWidth).
  // We place it relative to the bottom of the SVG.
  const textCy = svgHeight - strokeWidth * 0.5;

  useEffect(() => {
    startTimeRef.current = null;
    const clampedScore = Math.min(100, Math.max(0, score));

    const animate = (timestamp: number) => {
      if (startTimeRef.current === null) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(eased * clampedScore));
      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [score]);

  const trackPath = arcPath(cx, cy, r, 180);
  const fillPath = arcPath(cx, cy, r, (animatedScore / 100) * 180);
  const filterId = `glow-gauge-${size}`;

  return (
    <div className="flex flex-col items-center select-none">
      <svg
        width={px}
        height={svgHeight}
        viewBox={`0 0 ${px} ${svgHeight}`}
      >
        <defs>
          <filter id={filterId} x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background track */}
        <path
          d={trackPath}
          fill="none"
          stroke="#1e293b"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Filled arc */}
        <path
          d={fillPath}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          filter={`url(#${filterId})`}
          style={{ transition: 'stroke 0.4s ease' }}
        />

        {/* Score number */}
        <text
          x={cx}
          y={textCy - scoreFontSize * 0.35}
          textAnchor="middle"
          dominantBaseline="auto"
          fill="white"
          fontWeight="700"
          fontSize={scoreFontSize}
          fontFamily="inherit"
        >
          {animatedScore}
        </text>

        {/* Label */}
        <text
          x={cx}
          y={textCy + labelFontSize * 0.3}
          textAnchor="middle"
          dominantBaseline="auto"
          fill="#94a3b8"
          fontSize={labelFontSize}
          fontFamily="inherit"
        >
          {label}
        </text>
      </svg>

      {/* Tier badge */}
      <div
        className={`mt-2 px-3 py-0.5 rounded-full font-semibold tracking-wide border ${
          score < 40
            ? 'bg-red-950/60 border-red-800 text-red-400'
            : score < 60
            ? 'bg-amber-950/60 border-amber-800 text-amber-400'
            : score < 80
            ? 'bg-emerald-950/60 border-emerald-800 text-emerald-400'
            : 'bg-indigo-950/60 border-indigo-800 text-indigo-400'
        }`}
        style={{ fontSize: tierFontSize }}
      >
        {tierLabel}
      </div>
    </div>
  );
}
