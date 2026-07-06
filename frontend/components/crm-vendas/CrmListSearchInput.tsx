'use client';

import { Search } from 'lucide-react';

interface CrmListSearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export default function CrmListSearchInput({
  value,
  onChange,
  placeholder = 'Buscar por nome, email, CPF/CNPJ...',
  className = '',
}: CrmListSearchInputProps) {
  return (
    <div className={`relative max-w-md ${className}`}>
      <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
        aria-label="Buscar na lista"
      />
    </div>
  );
}
