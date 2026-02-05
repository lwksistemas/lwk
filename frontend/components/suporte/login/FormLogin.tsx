interface FormLoginProps {
  credentials: { username: string; password: string };
  onChange: (credentials: { username: string; password: string }) => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  loading: boolean;
  error: string;
}

export function FormLogin({ credentials, onChange, onSubmit, loading, error }: FormLoginProps) {
  return (
    <form className="mt-8 space-y-6" onSubmit={onSubmit}>
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded">
          {error}
        </div>
      )}
      <div className="space-y-4">
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700">
            Usuário
          </label>
          <input
            id="username"
            type="text"
            required
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={credentials.username}
            onChange={(e) =>
              onChange({ ...credentials, username: e.target.value })
            }
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Senha
          </label>
          <input
            id="password"
            type="password"
            required
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={credentials.password}
            onChange={(e) =>
              onChange({ ...credentials, password: e.target.value })
            }
          />
        </div>
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md disabled:opacity-50 transition-colors"
      >
        {loading ? 'Entrando...' : 'Entrar no Suporte'}
      </button>
    </form>
  );
}
