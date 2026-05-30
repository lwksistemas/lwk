import type { Metadata } from 'next';
import { getLoginBackgroundHintFromSlug } from '@/lib/login-default-backgrounds';

type Props = {
  children: React.ReactNode;
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  return {
    manifest: `/api/manifest/loja?slug=${encodeURIComponent(slug)}`,
  };
}

export default async function LojaSlugAuthLayout({ children, params }: Props) {
  const { slug } = await params;
  const bgHint = getLoginBackgroundHintFromSlug(slug);

  return (
    <>
      <link rel="preload" as="image" href={bgHint} fetchPriority="high" />
      {children}
    </>
  );
}
