import type { Metadata } from 'next';

type Props = {
  children: React.ReactNode;
  params: { slug: string };
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = params.slug;
  return {
    manifest: `/api/manifest/loja?slug=${encodeURIComponent(slug)}`,
  };
}

export default function LojaSlugAuthLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
