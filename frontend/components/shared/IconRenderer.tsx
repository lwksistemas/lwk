import Image from "next/image";

interface IconRendererProps {
  icone?: string;
  imagem?: string;
  alt?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const ICON_MAP: Record<string, string> = {
  Users: "👥",
  BarChart: "📊",
  ShoppingCart: "🛒",
  DollarSign: "💰",
  Settings: "⚙️",
  Calendar: "📅",
  FileText: "📄",
  Package: "📦",
  TrendingUp: "📈",
  Heart: "❤️",
  Star: "⭐",
  Check: "✅",
};

const SIZE_CLASSES = {
  sm: { container: "w-12 h-12", emoji: "text-2xl" },
  md: { container: "w-16 h-16", emoji: "text-4xl" },
  lg: { container: "w-24 h-24", emoji: "text-6xl" },
};

export function IconRenderer({
  icone,
  imagem,
  alt = "Ícone",
  size = 'md',
  className = "",
}: IconRendererProps) {
  const sizeClass = SIZE_CLASSES[size];

  // Prioridade: imagem > ícone > fallback
  if (imagem) {
    return (
      <div className={`relative ${sizeClass.container} ${className}`}>
        <Image
          src={imagem}
          alt={alt}
          fill
          className="object-contain"
        />
      </div>
    );
  }

  // Se é emoji (1-2 caracteres) ou não está no mapa, renderizar direto
  if (!icone || icone.length <= 2) {
    return (
      <span className={`${sizeClass.emoji} ${className}`}>
        {icone || "📦"}
      </span>
    );
  }

  // Se está no mapa de ícones, converter
  const emoji = ICON_MAP[icone] || "📦";
  return (
    <span className={`${sizeClass.emoji} ${className}`}>
      {emoji}
    </span>
  );
}

export { ICON_MAP };
