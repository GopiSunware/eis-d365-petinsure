'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { formatCurrency } from '@/lib/utils';

interface DailyCost {
  date: string;
  cost: number;
}

interface CostTrendChartProps {
  azureData: DailyCost[];
  awsData: DailyCost[];
}

export function CostTrendChart({ azureData, awsData }: CostTrendChartProps) {
  // Combine data by date
  const combinedData: Record<string, { date: string; azure: number; aws: number; total: number }> = {};

  azureData.forEach((item) => {
    if (!combinedData[item.date]) {
      combinedData[item.date] = { date: item.date, azure: 0, aws: 0, total: 0 };
    }
    combinedData[item.date].azure = item.cost;
    combinedData[item.date].total += item.cost;
  });

  awsData.forEach((item) => {
    if (!combinedData[item.date]) {
      combinedData[item.date] = { date: item.date, azure: 0, aws: 0, total: 0 };
    }
    combinedData[item.date].aws = item.cost;
    combinedData[item.date].total += item.cost;
  });

  const chartData = Object.values(combinedData)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map((item) => ({
      ...item,
      dateLabel: new Date(item.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
    }));

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500">
        No cost data available
      </div>
    );
  }

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="dateLabel"
            tick={{ fill: '#64748b', fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis
            tickFormatter={(value) => `$${value}`}
            tick={{ fill: '#64748b', fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
            formatter={(value: number) => [formatCurrency(value), '']}
            labelStyle={{ color: '#1e293b', fontWeight: 500 }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="azure"
            name="Azure"
            stroke="#0ea5e9"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="aws"
            name="AWS"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="total"
            name="Total"
            stroke="#8b5cf6"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
