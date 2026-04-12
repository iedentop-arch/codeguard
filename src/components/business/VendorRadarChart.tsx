/**
 * 供应商SLA评分雷达图组件
 * Phase 2 功能：可视化展示供应商7维度SLA评分
 */
import React from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// SLA评分维度定义
interface DimensionData {
  dimension: string;
  score: number;
  target: number;
  fullMark: number;
}

interface VendorRadarChartProps {
  /** 供应商名称 */
  vendorName?: string;
  /** 维度评分数据 */
  data: DimensionData[];
  /** 与其他供应商对比数据（可选） */
  comparisonData?: DimensionData[];
  /** 对比供应商名称 */
  comparisonName?: string;
  /** 是否显示目标线 */
  showTarget?: boolean;
  /** 总分（可选） */
  totalScore?: number;
  /** 等级（可选） */
  grade?: 'A' | 'B' | 'C' | 'D';
  /** 自定义样式 */
  className?: string;
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg';
}

// 维度中文名称映射
const DIMENSION_NAMES: Record<string, string> = {
  critical: '严重问题',
  warning: '警告问题',
  code_quality: '代码质量',
  compliance: '合规性',
  pr_efficiency: 'PR效率',
  ai_marking: 'AI标记',
  ci_success: 'CI成功率',
};

// 等级颜色映射
const GRADE_COLORS: Record<string, { bg: string; text: string }> = {
  A: { bg: 'bg-green-100', text: 'text-green-700' },
  B: { bg: 'bg-blue-100', text: 'text-blue-700' },
  C: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
  D: { bg: 'bg-red-100', text: 'text-red-700' },
};

// 尺寸配置
const SIZE_CONFIG = {
  sm: { height: 250, fontSize: 10 },
  md: { height: 350, fontSize: 12 },
  lg: { height: 450, fontSize: 14 },
};

/**
 * 供应商雷达图组件
 * 展示供应商在7个SLA维度上的评分表现
 */
export const VendorRadarChart: React.FC<VendorRadarChartProps> = ({
  vendorName,
  data,
  comparisonData,
  comparisonName,
  showTarget = true,
  totalScore,
  grade,
  className,
  size = 'md',
}) => {
  const config = SIZE_CONFIG[size];

  // 处理数据，将维度键转为中文显示名
  const processedData = data.map(item => ({
    ...item,
    dimension: DIMENSION_NAMES[item.dimension] || item.dimension,
  }));

  const processedComparisonData = comparisonData?.map(item => ({
    ...item,
    dimension: DIMENSION_NAMES[item.dimension] || item.dimension,
  }));

  // 合并数据用于对比模式
  const mergedData = comparisonData
    ? processedData.map((item, index) => ({
        dimension: item.dimension,
        current: item.score,
        comparison: processedComparisonData?.[index]?.score || 0,
        target: item.target,
        fullMark: item.fullMark,
      }))
    : processedData;

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-base font-medium">
            {vendorName ? `${vendorName} SLA评分` : 'SLA评分雷达图'}
          </CardTitle>
          <CardDescription>
            7维度综合评估
          </CardDescription>
        </div>
        {grade && totalScore && (
          <div className="flex items-center gap-2">
            <span className={cn(
              'px-2 py-1 rounded font-semibold',
              GRADE_COLORS[grade]?.bg || 'bg-gray-100',
              GRADE_COLORS[grade]?.text || 'text-gray-700'
            )}>
              {grade}级
            </span>
            <span className="text-lg font-bold">
              {totalScore.toFixed(1)}分
            </span>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={config.height}>
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={mergedData}>
            <PolarGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fontSize: config.fontSize, fill: '#374151' }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#6b7280' }}
              tickCount={5}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
              formatter={(value: number) => [`${value.toFixed(1)}分`, '']}
            />
            {comparisonData ? (
              <>
                {/* 当前供应商数据 */}
                <Radar
                  name={vendorName || '当前'}
                  dataKey="current"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
                {/* 对比供应商数据 */}
                <Radar
                  name={comparisonName || '对比'}
                  dataKey="comparison"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              </>
            ) : (
              <>
                {/* 供应商评分 */}
                <Radar
                  name="实际得分"
                  dataKey="score"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
                {/* 目标线 */}
                {showTarget && (
                  <Radar
                    name="目标值"
                    dataKey="target"
                    stroke="#10b981"
                    fill="transparent"
                    strokeWidth={1.5}
                    strokeDasharray="5 5"
                  />
                )}
              </>
            )}
            <Legend
              wrapperStyle={{ paddingTop: '20px', fontSize: config.fontSize }}
            />
          </RadarChart>
        </ResponsiveContainer>

        {/* 维度详情列表 */}
        <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
          {processedData.map((item) => (
            <div key={item.dimension} className="flex items-center justify-between p-2 bg-muted rounded">
              <span className="text-muted-foreground">{item.dimension}</span>
              <span className={cn(
                'font-medium',
                item.score >= item.target ? 'text-green-600' : 'text-red-600'
              )}>
                {item.score.toFixed(1)} / {item.target}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * 多供应商雷达图对比组件
 */
interface VendorComparisonRadarProps {
  vendors: Array<{
    name: string;
    data: DimensionData[];
    color?: string;
  }>;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const VendorComparisonRadar: React.FC<VendorComparisonRadarProps> = ({
  vendors,
  className,
  size = 'md',
}) => {
  const config = SIZE_CONFIG[size];

  // 合并所有供应商数据
  const mergedData = vendors[0]?.data.map((item, index) => {
    const result: Record<string, number | string> = {
      dimension: DIMENSION_NAMES[item.dimension] || item.dimension,
      fullMark: 100,
    };
    vendors.forEach((vendor) => {
      result[vendor.name] = vendor.data[index]?.score || 0;
    });
    return result as DimensionData & Record<string, number>;
  }) || [];

  // 颜色配置
  const COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4'];

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <CardTitle>供应商评分对比</CardTitle>
        <CardDescription>
          {vendors.length}家供应商7维度对比
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={config.height}>
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={mergedData}>
            <PolarGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fontSize: config.fontSize, fill: '#374151' }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#6b7280' }}
              tickCount={5}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
              formatter={(value: number) => [`${value.toFixed(1)}分`, '']}
            />
            {vendors.map((vendor, index) => (
              <Radar
                key={vendor.name}
                name={vendor.name}
                dataKey={vendor.name}
                stroke={vendor.color || COLORS[index % COLORS.length]}
                fill={vendor.color || COLORS[index % COLORS.length]}
                fillOpacity={0.2 + (0.1 * index)}
                strokeWidth={2}
              />
            ))}
            <Legend
              wrapperStyle={{ paddingTop: '20px', fontSize: config.fontSize }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

/**
 * SLA评分趋势雷达图
 * 展示供应商在不同月份的评分变化
 */
interface SLATrendRadarProps {
  vendorName: string;
  months: Array<{
    month: string;
    data: DimensionData[];
  }>;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const SLATrendRadar: React.FC<SLATrendRadarProps> = ({
  vendorName,
  months,
  className,
  size = 'md',
}) => {
  const config = SIZE_CONFIG[size];

  // 合并月份数据
  const mergedData = months[0]?.data.map((item, index) => {
    const result: Record<string, number | string> = {
      dimension: DIMENSION_NAMES[item.dimension] || item.dimension,
      fullMark: 100,
    };
    months.forEach((month) => {
      result[month.month] = month.data[index]?.score || 0;
    });
    return result as DimensionData & Record<string, number>;
  }) || [];

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <CardTitle>{vendorName} SLA评分趋势</CardTitle>
        <CardDescription>
          近{months.length}个月评分变化
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={config.height}>
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={mergedData}>
            <PolarGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fontSize: config.fontSize, fill: '#374151' }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#6b7280' }}
              tickCount={5}
            />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(1)}分`, '']}
            />
            {months.map((month, index) => (
              <Radar
                key={month.month}
                name={month.month}
                dataKey={month.month}
                stroke={COLORS[index % COLORS.length]}
                fill={COLORS[index % COLORS.length]}
                fillOpacity={0.15 + (0.05 * index)}
                strokeWidth={2}
              />
            ))}
            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default VendorRadarChart;