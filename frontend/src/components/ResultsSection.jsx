import { Download, FileSpreadsheet, Trash2, Database, CheckCircle, ShieldCheck } from 'lucide-react';
import CompanyCard from './CompanyCard';
import ValidationPanel from './ValidationPanel';

export default function ResultsSection({ 
  results, 
  cacheStats, 
  onDownloadJSON, 
  onDownloadCSV, 
  onDownloadValidatedCSV,
  onClearCache,
  validationConfig,
  setValidationConfig,
  onValidate,
  status
}) {
  const isValidating = status?.validation?.is_running;
  const validationProgress = status?.validation?.progress || 0;
  const validationTotal = status?.validation?.total || 0;

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
      <div className="flex flex-col gap-4 mb-6">
        {/* Header Row */}
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Results ({results.length})
            </h2>
            {cacheStats.entries > 0 && (
              <p className="text-sm text-gray-600 mt-1 flex items-center gap-2">
                <Database size={14} />
                Cache: {cacheStats.entries} entries ({cacheStats.size_kb.toFixed(1)} KB)
              </p>
            )}
          </div>
          
          <div className="flex gap-2">
            {/* Download Dropdown */}
            <div className="relative group">
              <button className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 flex items-center gap-2 shadow-md">
                <Download size={18} />
                Download
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                <div className="py-2">
                  <button
                    onClick={onDownloadJSON}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center gap-2"
                  >
                    <Download size={16} className="text-blue-600" />
                    Download JSON
                  </button>
                  <button
                    onClick={onDownloadCSV}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-green-50 flex items-center gap-2"
                  >
                    <FileSpreadsheet size={16} className="text-green-600" />
                    Download CSV
                  </button>
                  <div className="border-t border-gray-200 my-1"></div>
                  <button
                    onClick={onDownloadValidatedCSV}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-violet-50 flex items-center gap-2"
                  >
                    <FileSpreadsheet size={16} className="text-violet-600" />
                    Validated Results (CSV)
                  </button>
                </div>
              </div>
            </div>

            {/* Cache Management */}
            {cacheStats.entries > 0 && (
              <button
                onClick={onClearCache}
                className="bg-gradient-to-r from-red-500 to-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:from-red-600 hover:to-red-700 flex items-center gap-2 shadow-md"
                title="Clear Finder.fi cache"
              >
                <Trash2 size={18} />
                Clear Cache
              </button>
            )}
          </div>
        </div>

        {/* Info Cards Row */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-3 border border-blue-200">
            <div className="flex items-center gap-2 text-blue-700 mb-1">
              <Database size={16} />
              <span className="text-xs font-semibold">Total Results</span>
            </div>
            <p className="text-2xl font-bold text-blue-900">{results.length}</p>
          </div>

          <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-lg p-3 border border-emerald-200">
            <div className="flex items-center gap-2 text-emerald-700 mb-1">
              <CheckCircle size={16} />
              <span className="text-xs font-semibold">With Contacts</span>
            </div>
            <p className="text-2xl font-bold text-emerald-900">
              {results.filter(r => 
                r.contact_info?.emails?.length > 0 || 
                r.contact_info?.contacts?.length > 0
              ).length}
            </p>
          </div>

          <div className="bg-gradient-to-br from-violet-50 to-violet-100 rounded-lg p-3 border border-violet-200">
            <div className="flex items-center gap-2 text-violet-700 mb-1">
              <ShieldCheck size={16} />
              <span className="text-xs font-semibold">Verified on Finder</span>
            </div>
            <p className="text-2xl font-bold text-violet-900">
              {results.filter(r => r.finder_data?.verified_on_finder).length}
            </p>
          </div>
        </div>

        {/* Validation Panel */}
        <ValidationPanel
          config={validationConfig}
          setConfig={setValidationConfig}
          onValidate={onValidate}
          isValidating={isValidating}
          status={status}
          progress={validationProgress}
          total={validationTotal}
        />
      </div>

      {/* Results List */}
      <div className="space-y-4 max-h-96 overflow-y-auto mt-4">
        {results.map((company, idx) => (
          <CompanyCard key={idx} company={company} />
        ))}
      </div>
    </div>
  );
}
