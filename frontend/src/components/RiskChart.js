import { useState, useCallback } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Sector } from 'recharts';

/**
 * WebGuard AI — Vulnerability Distribution Chart (Donut) v2
 *
 * ─── المشكلة السابقة ───
 * الـ <Tooltip> من recharts لا يعمل في PieChart داخل Next.js بسبب مشاكل SSR/hydration.
 * الـ tooltip يُرنَّج على الـ server بدون إحداثيات الماوس، فيظهر فارغاً أو لا يظهر.
 *
 * ─── الحل ───
 * 1. نستبدل <Tooltip> كلياً بـ activeIndex state مُدار يدوياً.
 * 2. نستخدم renderActiveShape من recharts لتكبير الـ segment النشط + إضافة glow effect.
 * 3. tooltip مخصص (custom) يظهر في مركز الـ donut لا يعتمد على موقع الماوس — أكثر موثوقية.
 * 4. Legend تفاعلية: hover على اللون يُنشّط الـ segment المقابل.
 */

const RISK_CONFIG = {
  High:          { color: '#EF4444', glow: 'rgba(239,68,68,0.4)',   label: 'High Risk',      icon: '🔴' },
  Medium:        { color: '#F59E0B', glow: 'rgba(245,158,11,0.4)',  label: 'Medium Risk',    icon: '🟠' },
  Low:           { color: '#3B82F6', glow: 'rgba(59,130,246,0.4)',  label: 'Low Risk',       icon: '🔵' },
  Informational: { color: '#6B7280', glow: 'rgba(107,114,128,0.4)', label: 'Informational',  icon: '⚪' },
};

// ─── renderActiveShape: يرسم الـ segment النشط بشكل مُكبَّر مع هالة ضوئية ───
function renderActiveShape(props) {
  const {
    cx, cy, innerRadius, outerRadius, startAngle, endAngle,
    fill, payload, percent, value,
  } = props;

  const config = RISK_CONFIG[payload.name] || {};

  return (
    <g>
      {/* الـ segment المُكبَّر (outer radius أكبر بـ 8px) */}
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius - 2}
        outerRadius={outerRadius + 10}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        style={{ filter: `drop-shadow(0 0 8px ${config.glow || fill})` }}
      />
      {/* حلقة خارجية خفيفة (indicator ring) */}
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={outerRadius + 13}
        outerRadius={outerRadius + 16}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        opacity={0.5}
      />
      {/* نص المعلومات في وسط الـ donut */}
      <text x={cx} y={cy - 14} textAnchor="middle" fill="#F1F5F9" fontSize={13} fontWeight="700">
        {config.icon} {payload.name}
      </text>
      <text x={cx} y={cy + 8} textAnchor="middle" fill={fill} fontSize={22} fontWeight="800">
        {value}
      </text>
      <text x={cx} y={cy + 26} textAnchor="middle" fill="#94A3B8" fontSize={11}>
        {(percent * 100).toFixed(1)}% of total
      </text>
    </g>
  );
}

export default function RiskChart({ counts }) {
  const [activeIndex, setActiveIndex] = useState(null);

  const data = Object.entries(counts)
    .filter(([, value]) => value > 0)
    .map(([key, value]) => ({
      name: key,
      value,
      color: RISK_CONFIG[key]?.color || '#6B7280',
    }));

  const total = data.reduce((sum, d) => sum + d.value, 0);

  const onPieEnter = useCallback((_, index) => setActiveIndex(index), []);
  const onPieLeave = useCallback(() => setActiveIndex(null), []);

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
    <div>
      {/* ─── الـ Donut Chart ─── */}
      <div className="h-52 relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={48}
              outerRadius={78}
              paddingAngle={2}
              dataKey="value"
              activeIndex={activeIndex}
              activeShape={renderActiveShape}
              onMouseEnter={onPieEnter}
              onMouseLeave={onPieLeave}
              isAnimationActive={true}
              animationBegin={0}
              animationDuration={800}
              animationEasing="ease-out"
            >
              {data.map((entry, index) => (
                <Cell
                  key={entry.name}
                  fill={entry.color}
                  opacity={activeIndex === null || activeIndex === index ? 1 : 0.4}
                  style={{ cursor: 'pointer', transition: 'opacity 0.2s ease' }}
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* ─── نص الإجمالي في المنتصف (يظهر فقط عندما لا يوجد hover) ─── */}
        {activeIndex === null && (
          <div
            className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
            style={{ paddingBottom: '4px' }}
          >
            <span className="text-2xl font-extrabold text-white leading-none">{total}</span>
            <span className="text-xs text-gray-500 mt-0.5">Total</span>
          </div>
        )}
      </div>

      {/* ─── Legend تفاعلية ─── */}
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 mt-3">
        {data.map((entry, index) => {
          const config = RISK_CONFIG[entry.name] || {};
          const isActive = activeIndex === index;
          const pct = total > 0 ? ((entry.value / total) * 100).toFixed(0) : 0;

          return (
            <button
              key={entry.name}
              onMouseEnter={() => setActiveIndex(index)}
              onMouseLeave={() => setActiveIndex(null)}
              onClick={() => setActiveIndex(activeIndex === index ? null : index)}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1 transition-all duration-200"
              style={{
                background: isActive ? `${entry.color}18` : 'transparent',
                border: `1px solid ${isActive ? entry.color : 'transparent'}`,
              }}
            >
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{
                  backgroundColor: entry.color,
                  boxShadow: isActive ? `0 0 6px ${entry.color}` : 'none',
                }}
              />
              <span
                className="text-xs font-medium transition-colors duration-200"
                style={{ color: isActive ? entry.color : '#94A3B8' }}
              >
                {entry.name}
              </span>
              <span
                className="text-xs font-bold"
                style={{ color: isActive ? entry.color : '#64748B' }}
              >
                {entry.value}
              </span>
              {isActive && (
                <span className="text-xs" style={{ color: entry.color, opacity: 0.8 }}>
                  ({pct}%)
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
