'use client';

import React from 'react';

interface FormFieldProps {
  label: string;
  name: string;
  value: string | number;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
  type?: 'text' | 'email' | 'tel' | 'number' | 'date' | 'time' | 'password' | 'textarea' | 'select';
  required?: boolean;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  options?: { value: string | number; label: string }[];
  rows?: number;
  min?: number;
  max?: number;
  step?: number;
  colSpan?: 1 | 2;
}

export function FormField({
  label,
  name,
  value,
  onChange,
  type = 'text',
  required = false,
  placeholder,
  disabled = false,
  className = '',
  options = [],
  rows = 3,
  min,
  max,
  step,
  colSpan = 1,
}: FormFieldProps) {
  const baseInputClass = 'w-full px-3 py-3 sm:py-2.5 min-h-[44px] text-base sm:text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed dark:bg-gray-700 dark:text-white transition-colors';
  const colSpanClass = colSpan === 2 ? 'sm:col-span-2' : '';

  if (type === 'textarea') {
    return (
      <div className={`${colSpanClass} ${className}`}>
        <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
        <textarea
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          disabled={disabled}
          rows={rows}
          className={baseInputClass}
        />
      </div>
    );
  }

  if (type === 'select') {
    return (
      <div className={`${colSpanClass} ${className}`}>
        <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
        <select
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          disabled={disabled}
          className={baseInputClass}
        >
          <option value="">Selecione...</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }

  return (
    <div className={`${colSpanClass} ${className}`}>
      <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        required={required}
        placeholder={placeholder}
        disabled={disabled}
        min={min}
        max={max}
        step={step}
        className={baseInputClass}
      />
    </div>
  );
}
