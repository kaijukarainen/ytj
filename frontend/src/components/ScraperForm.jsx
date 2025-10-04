import { Search, Play, Loader2, Clock } from 'lucide-react';
import ProgressBar from './ProgressBar';

export default function ScraperForm({ 
  params, 
  setParams, 
  businessLines, 
  onStart, 
  status,
  estimatedTime 
}) {
  const isScraping = status?.scraping?.is_running;
  const scrapingProgress = status?.scraping?.progress || 0;
  const scrapingTotal = status?.scraping?.total || 0;
  const progressPercent = scrapingTotal > 0 ? (scrapingProgress / scrapingTotal) * 100 : 0;

  return (
    <div className="lg:col-span-2 bg-white rounded-xl shadow-lg p-6 border border-gray-200">
      <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        <Search size={24} className="text-cyan-600" />
        Scraper Parameters
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Business Line
          </label>
          <select
            value={params.main_business_line}
            onChange={(e) => setParams({...params, main_business_line: e.target.value})}
            className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
          >
            <option value="">Select business line...</option>
            {businessLines.map(bl => (
              <option key={bl.code} value={bl.code}>
                {bl.code} - {bl.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location
          </label>
          <input
            type="text"
            value={params.location}
            onChange={(e) => setParams({...params, location: e.target.value})}
            className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
            placeholder="Kuopio"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company Form
          </label>
          <input
            type="text"
            value={params.company_form}
            onChange={(e) => setParams({...params, company_form: e.target.value})}
            className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
            placeholder="OY"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Max Companies
          </label>
          <input
            type="number"
            value={params.max_companies}
            onChange={(e) => setParams({...params, max_companies: parseInt(e.target.value)})}
            className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
            min="1"
            max="100"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Output Filename
          </label>
          <input
            type="text"
            value={params.output_file}
            onChange={(e) => setParams({...params, output_file: e.target.value})}
            className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg text-gray-900 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
            placeholder="companies_leads.json"
          />
        </div>
      </div>

      <button
        onClick={onStart}
        disabled={isScraping}
        className="mt-6 w-full bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-cyan-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg"
      >
        {isScraping ? (
          <>
            <Loader2 size={20} className="animate-spin" />
            Scraping in Progress...
          </>
        ) : (
          <>
            <Play size={20} />
            Start Scraping
          </>
        )}
      </button>

      {isScraping && (
        <div className="mt-4 bg-blue-50 rounded-lg p-4 border-2 border-blue-200">
          <ProgressBar 
            progress={scrapingProgress}
            total={scrapingTotal}
            percent={progressPercent}
            currentItem={status?.scraping?.current_company}
            estimatedTime={estimatedTime}
          />
        </div>
      )}
    </div>
  );
}
