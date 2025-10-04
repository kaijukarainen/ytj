import { Sparkles, Loader2 } from 'lucide-react';

export default function AIAgentPanel({ 
  openaiKey, 
  setOpenaiKey, 
  onEnrich, 
  status, 
  hasResults 
}) {
  const isEnriching = status?.agent?.is_running;
  const agentProgress = status?.agent?.progress || 0;
  const agentTotal = status?.agent?.total || 0;

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
      <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        <Sparkles size={24} className="text-emerald-600" />
        AI Agent
      </h2>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          OpenAI API Key
        </label>
        <input
          type="password"
          value={openaiKey}
          onChange={(e) => setOpenaiKey(e.target.value)}
          className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          placeholder="sk-..."
        />
      </div>

      <button
        onClick={onEnrich}
        disabled={isEnriching || !hasResults}
        className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-emerald-600 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg"
      >
        {isEnriching ? (
          <>
            <Loader2 size={20} className="animate-spin" />
            Enriching...
          </>
        ) : (
          <>
            <Sparkles size={20} />
            Enrich with AI
          </>
        )}
      </button>

      {isEnriching && (
        <div className="mt-4 bg-emerald-50 rounded-lg p-4 border-2 border-emerald-200">
          <div className="flex justify-between text-sm text-gray-700 mb-1">
            <span className="font-semibold">Progress</span>
            <span className="font-mono">{agentProgress} / {agentTotal}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
            <div 
              className="bg-gradient-to-r from-emerald-500 to-teal-600 h-3 rounded-full transition-all duration-300 flex items-center justify-end pr-2"
              style={{width: `${(agentProgress / agentTotal) * 100}%`}}
            >
              <span className="text-xs font-bold text-white">
                {Math.round((agentProgress / agentTotal) * 100)}%
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Sparkles size={16} className="text-emerald-600" />
            <span className="truncate">{status?.agent?.current_company}</span>
          </div>
        </div>
      )}

      <p className="text-xs text-gray-500 mt-4">
        AI agent finds missing contact emails for scraped leads
      </p>
    </div>
  );
}
