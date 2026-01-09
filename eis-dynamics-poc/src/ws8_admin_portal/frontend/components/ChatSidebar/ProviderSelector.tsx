'use client';

interface Provider {
  name: string;
  enabled: boolean;
  model: string;
}

interface ProvidersData {
  providers: Record<string, Provider>;
  enabled: string[];
}

interface ProviderSelectorProps {
  providers: ProvidersData;
  selected: string | null;
  onChange: (provider: string) => void;
}

export default function ProviderSelector({ providers, selected, onChange }: ProviderSelectorProps) {
  if (!providers?.enabled?.length) return null;

  const enabledProviders = providers.enabled;

  // If only one provider, just show info
  if (enabledProviders.length === 1) {
    const provider = providers.providers[enabledProviders[0]];
    return (
      <div className="flex items-center gap-2 text-sm text-indigo-100">
        <span className="w-2 h-2 rounded-full bg-green-400"></span>
        <span>{provider?.name} ({provider?.model})</span>
      </div>
    );
  }

  // Multiple providers - show toggle
  return (
    <div className="flex items-center gap-2">
      {enabledProviders.map(key => {
        const provider = providers.providers[key];
        const isSelected = selected === key;

        return (
          <button
            key={key}
            onClick={() => onChange(key)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
              isSelected
                ? 'bg-white text-indigo-600'
                : 'bg-indigo-500/30 text-indigo-100 hover:bg-indigo-500/50'
            }`}
          >
            {key === 'openai' ? 'GPT-4o' : 'Claude'}
          </button>
        );
      })}
    </div>
  );
}
