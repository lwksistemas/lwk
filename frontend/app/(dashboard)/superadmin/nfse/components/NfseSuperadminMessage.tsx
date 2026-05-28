'use client';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

export function NfseSuperadminMessage({
  type,
  text,
}: {
  type: 'success' | 'error';
  text: string;
}) {
  return (
    <Alert variant={type === 'error' ? 'destructive' : 'default'}>
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>{text}</AlertDescription>
    </Alert>
  );
}
