import { ReactNode } from 'react';

interface SectionContainerProps {
  children: ReactNode;
  id?: string;
  className?: string;
  background?: 'white' | 'gray' | 'gradient';
  padding?: 'sm' | 'md' | 'lg';
}

const BG_CLASSES = {
  white: 'bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50',
  gray: 'bg-gradient-to-br from-slate-100 via-gray-50 to-slate-100',
  gradient: 'bg-gradient-to-br from-blue-100 via-blue-50 to-indigo-100',
};

const PADDING_CLASSES = {
  sm: 'py-12',
  md: 'py-16 md:py-20',
  lg: 'py-20 md:py-24',
};

export function SectionContainer({
  children,
  id,
  className = '',
  background = 'white',
  padding = 'md',
}: SectionContainerProps) {
  return (
    <section
      id={id}
      className={`w-full ${BG_CLASSES[background]} ${PADDING_CLASSES[padding]} ${className}`}
    >
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {children}
      </div>
    </section>
  );
}
