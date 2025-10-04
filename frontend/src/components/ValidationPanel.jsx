import { ShieldCheck, Loader2 } from 'lucide-react';

export default function ValidationPanel({ 
  config, 
  setConfig, 
  onValidate, 
  isValidating,
  status,
  progress,
  total
}) {
  return (
    <div className="bg-violet-50 rounded-lg p-4 border-2 border-violet-200">
      <h3 className="text-sm font-semibold text-violet-700 mb-3">Validation Settings</h3>
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Retry Delay (seconds)
          </label>
          <select
            value={config.retry_delay}
            onChange={(e) => setConfig({...config, retry_delay: parseInt(e.target.value)})}
            className="w-full px-2 py-1 text-sm bg-white border border-violet-300 rounded focus:ring-2 focus:ring-violet-500"
          >
            <option value="0">No wait (fast, risky)</option>
            <option value="3">3 seconds</option>
            <option value="5">5 seconds (default)</option>
            <option value="10">10 seconds (safe)</option>
            <option value="15">15 seconds (very safe)</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">Wait time if rate limited (202)</p>
        </div>
        
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Between Requests (seconds)
          </label>
          <select
            value={config.between_delay}
            onChange={(e) => setConfig({...config, between_delay: parseInt(e.target.value)})}
            className="w-full px-2 py-1 text-sm bg-white border border-violet-300 rounded focus:ring-2 focus:ring-violet-500"
          >
            <option value="2">2 seconds (fast, risky)</option>
            <option value="4">4 seconds (default)</option>
            <option value="6">6 seconds (safe)</option>
            <option value="10">10 seconds (very safe)</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">Delay between each company</p>
        </div>
      </div>

      <button
        onClick={onValidate}
        disabled={isValidating}
        className="bg-gradient-to-r from-violet-600 to-purple-600 text-white px-4 py-2 rounded-lg font-semibold hover:from-violet-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md w-full"
      >
        {isValidating ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Validating...
          </>
        ) : (
          <>
            <ShieldCheck size={18} />
            Validate on Finder.fi
          </>
        )}
      </button>

      {isValidating && (
        <div className="mt-3 bg-white rounded-lg p-3 border border-violet-300">
          <div className="flex justify-between items-center text-sm text-gray-700 mb-2">
            <span className="font-semibold">Validating on Finder.fi</span>
            <span className="font-mono">{progress} / {total}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
            <div 
              className="bg-gradient-to-r from-violet-500 to-purple-600 h-3 rounded-full transition-all duration-300 flex items-center justify-end pr-2"
              style={{width: `${(progress / total) * 100}%`}}
            >
              <span className="text-xs font-bold text-white">
                {Math.round((progress / total) * 100)}%
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-gray-700">
              <ShieldCheck size={16} className="text-violet-600" />
              <span className="truncate">{status?.validation?.current_company}</span>
            </div>
            <div className="flex gap-4 text-xs">
              <span className="text-green-600">✓ {status?.validation?.validated_count || 0} kept</span>
              <span className="text-red-600">✗ {status?.validation?.removed_count || 0} removed</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
