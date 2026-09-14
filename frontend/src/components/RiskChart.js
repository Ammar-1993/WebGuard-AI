import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

/**
 * WebGuard AI — Vulnerability Distribution Chart (Donut)
 */

const COLORS = {
  High: '#EF4444',
  Medium: '#F59E0B',
  Low: '#3B82F6',
  Informational: '#6B7280',
};

export default function RiskChart({ counts }) {
  const data = Object.entries(counts)
    .filter(([, value]) => value > 0)
    .map(([key, value]) => ({
      name: key,
      value,
      color: COLORS[key] || '#6B7280',
    }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500">
        <div className="text-center">
          <span className="text-4xl block mb-2">✅</span>
          <p>No vulnerabilities found!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-48">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={40}
            outerRadius={70}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#E2E8F0',
            }}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-3 mt-2">
        {data.map((entry) => (
          <div key={entry.name} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-xs text-gray-400">{entry.name} ({entry.value})</span>
          </div>
        ))}
      </div>
    </div>
  );
}
