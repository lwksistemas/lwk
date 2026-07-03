import type { LoginColorPreset } from "./login-config-page-types";
import { isColorPresetSelected, normalizeHexColor } from "./login-config-page-utils";

interface LoginConfigColorSectionProps {
  colorPresets: LoginColorPreset[];
  corPrimaria: string;
  corSecundaria: string;
  accentColor: string;
  onApplyPreset: (primaria: string, secundaria: string) => void;
  onCorPrimariaChange: (value: string) => void;
  onCorSecundariaChange: (value: string) => void;
}

export function LoginConfigColorSection({
  colorPresets,
  corPrimaria,
  corSecundaria,
  accentColor,
  onApplyPreset,
  onCorPrimariaChange,
  onCorSecundariaChange,
}: LoginConfigColorSectionProps) {
  const corPrimariaHex = normalizeHexColor(corPrimaria);
  const corSecundariaHex = normalizeHexColor(corSecundaria);

  return (
    <>
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Cores pré-definidas
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {colorPresets.map((cor) => (
            <button
              key={cor.nome}
              type="button"
              onClick={() => onApplyPreset(cor.primaria, cor.secundaria)}
              className={`p-3 rounded-lg border-2 transition-all ${
                isColorPresetSelected(corPrimariaHex, cor.primaria)
                  ? "border-current bg-opacity-10"
                  : "border-gray-200 dark:border-gray-600"
              }`}
              style={
                isColorPresetSelected(corPrimariaHex, cor.primaria)
                  ? { borderColor: accentColor, backgroundColor: `${accentColor}15` }
                  : undefined
              }
            >
              <div className="flex items-center gap-2">
                <div
                  className="w-6 h-6 rounded-full shrink-0"
                  style={{ backgroundColor: cor.primaria }}
                />
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {cor.nome}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Cor primária
          </label>
          <div className="flex gap-2">
            <input
              type="color"
              value={corPrimariaHex}
              onChange={(e) => onCorPrimariaChange(e.target.value)}
              className="w-12 h-10 border rounded cursor-pointer"
            />
            <input
              type="text"
              value={corPrimariaHex}
              onChange={(e) => onCorPrimariaChange(normalizeHexColor(e.target.value))}
              className="flex-1 px-3 py-2 border rounded-md text-sm dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Cor secundária
          </label>
          <div className="flex gap-2">
            <input
              type="color"
              value={corSecundariaHex}
              onChange={(e) => onCorSecundariaChange(e.target.value)}
              className="w-12 h-10 border rounded cursor-pointer"
            />
            <input
              type="text"
              value={corSecundariaHex}
              onChange={(e) => onCorSecundariaChange(normalizeHexColor(e.target.value))}
              className="flex-1 px-3 py-2 border rounded-md text-sm dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
        </div>
      </div>
    </>
  );
}
