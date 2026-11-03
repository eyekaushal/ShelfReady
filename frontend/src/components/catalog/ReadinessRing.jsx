import { cn } from '../../lib/cn'

/**
 * Small progress ring for the recognition-readiness score (Linear's project status ring).
 * Scores are computed by the readiness add-on; until then a product shows a dashed
 * "not scored" ring instead of a misleading 0%.
 */
export function ReadinessRing({ score, scored, size = 18, showLabel = true, className }) {
  const radius = (size - 3) / 2
  const circumference = 2 * Math.PI * radius
  const tone = score >= 80 ? 'text-green-600' : score >= 40 ? 'text-amber-500' : 'text-red-500'
  const label = scored ? `Readiness ${score}%` : 'Not scored yet'

  return (
    <span className={cn('inline-flex items-center gap-1.5 tabular', className)} title={label}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={scored ? tone : 'text-gray-300'} aria-label={label}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeDasharray={scored ? undefined : '2 2.5'}
          className={scored ? 'opacity-20' : ''}
        />
        {scored ? (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - score / 100)}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        ) : null}
      </svg>
      {showLabel ? (
        <span className={cn('text-[13px]', scored ? 'text-gray-700' : 'text-gray-400')}>{scored ? `${score}%` : '—'}</span>
      ) : null}
    </span>
  )
}
