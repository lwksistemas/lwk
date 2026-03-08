'use client';

import type { LucideIcon } from 'lucide-react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon?: LucideIcon;
  iconColor?: string;
  iconBgColor?: string;
  className?: string;
  trend?: 'up' | 'down';
  trendValue?: string;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-[#0176d3]',
  iconBgColor = 'bg-[#e3f3ff]',
  className = '',
  trend,
  trendValue,
}: StatCardProps) {
  return (
    <div
      className={`
        bg-white dark:bg-[#16325c] p-5 rounded-lg 
        border border-gray-200 dark:border-[#0d1f3c] 
        shadow-sm hover:shadow-md transition-all
        ${className}
      `}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Title - Estilo Salesforce */}
          <p className="text-gray-600 dark:text-gray-400 text-xs font-medium uppercase tracking-wide mb-2">
            {title}
          </p>
          
          {/* Value - Destaque */}
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight mb-1">
            {value}
          </h2>
          
          {/* Subtitle ou Trend */}
          {(subtitle || trend) && (
            <div className="flex items-center gap-2 flex-wrap">
              {trend && trendValue && (
                <div className={`flex items-center gap-1 text-xs font-medium ${
                  trend === 'up' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}>
                  {trend === 'up' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  <span>{trendValue}</span>
                </div>
              )}
              {subtitle && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {subtitle}
                </p>
              )}
            </div>
          )}
        </div>
        
        {/* Icon - Estilo Salesforce Lightning */}
        {Icon && (
          <div className={`p-3 rounded-lg ${iconBgColor} dark:bg-opacity-20 ${iconColor} shrink-0`}>
            <Icon size={24} strokeWidth={2} />
          </div>
        )}
      </div>
    </div>
  );
}
