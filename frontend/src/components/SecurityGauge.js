/**
 * WebGuard AI — Security Score Gauge (Circular)
 * Displays the score (0-100) inside an animated SVG circle with grade and color.
 */
export default function SecurityGauge({ score, grade, color, label }) {
  // ─── Calculate SVG circle path ───
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center score-pulse">
      {/* Circle */}
      <div className="relative w-48 h-48">
        <svg className="w-48 h-48 transform -rotate-90" viewBox="0 0 160 160">
          {/* Background */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke="#1E293B"
            strokeWidth="12"
            fill="transparent"
          />
          {/* Animated indicator */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke={color}
            strokeWidth="12"
            fill="transparent"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              transition: 'stroke-dashoffset 1.5s ease-in-out',
              filter: `drop-shadow(0 0 8px ${color}66)`,
            }}
          />
        </svg>

        {/* Score in center */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-extrabold text-white">{score}</span>
          <span className="text-sm text-gray-400">out of 100</span>
        </div>
      </div>

      {/* Grade */}
      <div className="mt-4 text-center">
        <span
          className="text-3xl font-extrabold"
          style={{ color }}
        >
          {grade}
        </span>
        <p className="text-gray-400 text-sm mt-1">{label}</p>
      </div>
    </div>
  );
}
