import React, { useState, useEffect } from 'react';
import { Download, Search, Sparkles, Play, CheckCircle, Loader2, Clock, TrendingUp, ShieldCheck, FileSpreadsheet, Trash2, Database } from 'lucide-react';

export default function App() {
  const [params, setParams] = useState({
    main_business_line: '6201',
    location: 'Kuopio',
    company_form: 'OY',
    max_companies: 15,
    output_file: 'companies_leads.json'
  });
  
  const [openaiKey, setOpenaiKey] = useState('');
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState([]);
  const [businessLines, setBusinessLines] = useState([]);
  const [startTime, setStartTime] = useState(null);
  const [cacheStats, setCacheStats] = useState({ entries: 0, size_kb: 0 });
  const [validationConfig, setValidationConfig] = useState({
    retry_delay: 5,
    between_delay: 4
  });

  useEffect(() => {
    fetch('http://localhost:5001/api/business-lines')
      .then(res => res.json())
      .then(data => setBusinessLines(data))
      .catch(err => console.error('Error fetching business lines:', err));

    const interval = setInterval(() => {
      fetch('http://localhost:5001/api/status')
        .then(res => res.json())
        .then(data => {
          setStatus(data);
          if (data.scraping.results && data.scraping.results.length > 0) {
            setResults(data.scraping.results);
          }
          if (data.scraping.is_running && !startTime) {
            setStartTime(Date.now());
          }
          if (!data.scraping.is_running && startTime) {
            setStartTime(null);
          }
        })
        .catch(err => console.error('Error fetching status:', err));
      
      // Fetch cache stats
      fetch('http://localhost:5001/api/cache/stats')
        .then(res => res.json())
        .then(data => setCacheStats(data))
        .catch(err => console.error('Error fetching cache stats:', err));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  const startScraping = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      const data = await response.json();
      setStartTime(Date.now());
    } catch (err) {
      alert('Error starting scraper: ' + err.message);
    }
  };

  const enrichWithAgent = async () => {
    if (!openaiKey) {
      alert('Please enter your OpenAI API key');
      return;
    }

    try {
      const response = await fetch('http://localhost:5001/api/enrich', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ leads: results, openai_api_key: openaiKey })
      });
      const data = await response.json();
    } catch (err) {
      alert('Error starting agent: ' + err.message);
    }
  };

  const validateWithFinder = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          leads: results,
          config: validationConfig
        })
      });
      const data = await response.json();
    } catch (err) {
      alert('Error starting validation: ' + err.message);
    }
  };

  const downloadResults = () => {
    window.location.href = `http://localhost:5001/api/download?filename=${params.output_file}`;
  };

  const downloadCSV = () => {
    const csvFilename = params.output_file.replace('.json', '.csv');
    window.location.href = `http://localhost:5001/api/download-csv?filename=${csvFilename}`;
  };

  const downloadValidatedCSV = () => {
    window.location.href = 'http://localhost:5001/api/download-csv?filename=companies_leads_validated.csv';
  };

  const clearCache = async () => {
    if (!confirm('Are you sure you want to clear the Finder.fi cache? This will remove all cached company data.')) {
      return;
    }
    
    try {
      const response = await fetch('http://localhost:5001/api/cache/clear', {
        method: 'POST'
      });
      const data = await response.json();
      alert(data.message || 'Cache cleared successfully');
      
      // Refresh cache stats
      const statsResponse = await fetch('http://localhost:5001/api/cache/stats');
      const statsData = await statsResponse.json();
      setCacheStats(statsData);
    } catch (err) {
      alert('Error clearing cache: ' + err.message);
    }
  };

  const isScraping = status?.scraping?.is_running;
  const isEnriching = status?.agent?.is_running;
  const isValidating = status?.validation?.is_running;
  const scrapingProgress = status?.scraping?.progress || 0;
  const scrapingTotal = status?.scraping?.total || 0;
  const agentProgress = status?.agent?.progress || 0;
  const agentTotal = status?.agent?.total || 0;
  const validationProgress = status?.validation?.progress || 0;
  const validationTotal = status?.validation?.total || 0;

  const getEstimatedTime = (progress, total, startTime) => {
    if (!startTime || progress === 0) return null;
    const elapsed = (Date.now() - startTime) / 1000;
    const avgTimePerItem = elapsed / progress;
    const remaining = (total - progress) * avgTimePerItem;
    const minutes = Math.floor(remaining / 60);
    const seconds = Math.floor(remaining % 60);
    return `${minutes}m ${seconds}s`;
  };

  const estimatedTime = isScraping ? getEstimatedTime(scrapingProgress, scrapingTotal, startTime) : null;
  const progressPercent = scrapingTotal > 0 ? (scrapingProgress / scrapingTotal) * 100 : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Finnish Company Lead Scraper
          </h1>
          <p className="text-gray-600">Scrape Finnish company data with AI-powered contact enrichment</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
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
              onClick={startScraping}
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
                <div className="flex justify-between items-center text-sm text-gray-700 mb-2">
                  <span className="font-semibold">Progress</span>
                  <span className="font-mono">{scrapingProgress} / {scrapingTotal}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                  <div 
                    className="bg-gradient-to-r from-cyan-500 to-blue-600 h-3 rounded-full transition-all duration-300 flex items-center justify-end pr-2"
                    style={{width: `${progressPercent}%`}}
                  >
                    <span className="text-xs font-bold text-white">{Math.round(progressPercent)}%</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-gray-700">
                    <Loader2 size={16} className="animate-spin text-cyan-600" />
                    <span className="truncate">{status?.scraping?.current_company}</span>
                  </div>
                  {estimatedTime && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Clock size={16} />
                      <span>Est. time remaining: {estimatedTime}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

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
              onClick={enrichWithAgent}
              disabled={isEnriching || results.length === 0}
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
                    <span className="text-xs font-bold text-white">{Math.round((agentProgress / agentTotal) * 100)}%</span>
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
        </div>

        {results.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <div className="flex flex-col gap-4 mb-6">
              {/* Header Row with Download and Cache buttons */}
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
                    <button
                      className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 flex items-center gap-2 shadow-md"
                    >
                      <Download size={18} />
                      Download
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                      <div className="py-2">
                        <button
                          onClick={downloadResults}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center gap-2"
                        >
                          <Download size={16} className="text-blue-600" />
                          Download JSON
                        </button>
                        <button
                          onClick={downloadCSV}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-green-50 flex items-center gap-2"
                        >
                          <FileSpreadsheet size={16} className="text-green-600" />
                          Download CSV
                        </button>
                        <div className="border-t border-gray-200 my-1"></div>
                        <button
                          onClick={downloadValidatedCSV}
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
                      onClick={clearCache}
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

              {/* Validation Settings */}
              <div className="bg-violet-50 rounded-lg p-4 border-2 border-violet-200">
                <h3 className="text-sm font-semibold text-violet-700 mb-3">Validation Settings</h3>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Retry Delay (seconds)
                    </label>
                    <select
                      value={validationConfig.retry_delay}
                      onChange={(e) => setValidationConfig({...validationConfig, retry_delay: parseInt(e.target.value)})}
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
                      value={validationConfig.between_delay}
                      onChange={(e) => setValidationConfig({...validationConfig, between_delay: parseInt(e.target.value)})}
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

                {/* Validate Button */}
                <button
                  onClick={validateWithFinder}
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
              </div>
            </div>

            {isValidating && (
              <div className="mb-4 bg-violet-50 rounded-lg p-4 border-2 border-violet-200">
                <div className="flex justify-between items-center text-sm text-gray-700 mb-2">
                  <span className="font-semibold">Validating on Finder.fi</span>
                  <span className="font-mono">{validationProgress} / {validationTotal}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                  <div 
                    className="bg-gradient-to-r from-violet-500 to-purple-600 h-3 rounded-full transition-all duration-300 flex items-center justify-end pr-2"
                    style={{width: `${(validationProgress / validationTotal) * 100}%`}}
                  >
                    <span className="text-xs font-bold text-white">{Math.round((validationProgress / validationTotal) * 100)}%</span>
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

            <div className="space-y-4 max-h-96 overflow-y-auto mt-4">
              {results.map((company, idx) => {
                const hasEnrichedData = company.contact_info?.emails?.length > 0 || company.contact_info?.contacts?.length > 0;
                const isVerifiedOnFinder = company.finder_data?.verified_on_finder;
                
                return (
                  <div key={idx} className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-bold text-gray-900">{company.name}</h3>
                          {isVerifiedOnFinder && (
                            <span className="text-xs bg-violet-100 text-violet-700 px-2 py-1 rounded font-medium flex items-center gap-1">
                              <ShieldCheck size={12} />
                              Verified
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{company.business_id}</p>
                      </div>
                      {hasEnrichedData && (
                        <div className="flex items-center gap-2">
                          <CheckCircle className="text-emerald-500" size={20} />
                          {company.contact_info?.contacts?.length > 0 && (
                            <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded font-medium">
                              {company.contact_info.contacts.length} contact{company.contact_info.contacts.length > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-700 mb-3">
                      {company.main_business_line}
                    </p>

                    {/* Enhanced Finder.fi Data Section */}
                    {company.finder_data && (
                      <div className="mb-3 bg-gradient-to-br from-violet-50 to-purple-50 rounded-lg p-3 border border-violet-200 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm font-bold text-violet-700 flex items-center gap-1">
                            <TrendingUp size={14} />
                            Finder.fi Business Intelligence
                          </p>
                          <a 
                            href={company.finder_data.finder_url} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="text-xs text-violet-600 hover:text-violet-800 hover:underline font-medium"
                          >
                            View Full Profile →
                          </a>
                        </div>

                        {/* Basic Info Grid */}
                        {company.finder_data.basic_info && Object.keys(company.finder_data.basic_info).length > 0 && (
                          <div className="grid grid-cols-2 gap-2 mb-2">
                            {company.finder_data.basic_info.founded && (
                              <div className="bg-white rounded p-2 border border-violet-100">
                                <p className="text-xs text-gray-500 mb-0.5">Founded</p>
                                <p className="text-sm font-semibold text-gray-900">
                                  📅 {company.finder_data.basic_info.founded}
                                </p>
                              </div>
                            )}
                            {company.finder_data.basic_info.employees && (
                              <div className="bg-white rounded p-2 border border-violet-100">
                                <p className="text-xs text-gray-500 mb-0.5">Employees</p>
                                <p className="text-sm font-semibold text-gray-900">
                                  👥 {company.finder_data.basic_info.employees}
                                </p>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Financial Info */}
                        {company.finder_data.financials && Object.keys(company.finder_data.financials).length > 0 && (
                          <div className="bg-white rounded p-2 border border-violet-100 mb-2">
                            <p className="text-xs font-semibold text-violet-600 mb-1.5">Financial Data</p>
                            <div className="space-y-1">
                              {company.finder_data.financials.revenue && (
                                <div className="flex justify-between items-center">
                                  <span className="text-xs text-gray-600">💰 Revenue:</span>
                                  <span className="text-sm font-semibold text-gray-900">
                                    {company.finder_data.financials.revenue}
                                  </span>
                                </div>
                              )}
                              {company.finder_data.financials.operating_profit && (
                                <div className="flex justify-between items-center">
                                  <span className="text-xs text-gray-600">📊 Operating Profit:</span>
                                  <span className="text-sm font-semibold text-gray-900">
                                    {company.finder_data.financials.operating_profit}
                                  </span>
                                </div>
                              )}
                              {company.finder_data.financials.financial_year && (
                                <div className="flex justify-between items-center">
                                  <span className="text-xs text-gray-600">📅 Financial Year:</span>
                                  <span className="text-xs text-gray-700">
                                    {company.finder_data.financials.financial_year}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Contact Info from Finder */}
                        {company.finder_data.contact && Object.keys(company.finder_data.contact).length > 0 && (
                          <div className="bg-white rounded p-2 border border-violet-100 mb-2">
                            <p className="text-xs font-semibold text-violet-600 mb-1.5">Contact Information</p>
                            <div className="space-y-1 text-xs">
                              {company.finder_data.contact.address && (
                                <div className="text-gray-700">📍 {company.finder_data.contact.address}</div>
                              )}
                              {company.finder_data.contact.phone && (
                                <div className="text-gray-700">📞 {company.finder_data.contact.phone}</div>
                              )}
                              {company.finder_data.contact.email && (
                                <div className="text-blue-600 font-medium">
                                  ✉️ {company.finder_data.contact.email}
                                </div>
                              )}
                              {company.finder_data.contact.website && (
                                <a 
                                  href={company.finder_data.contact.website} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline block"
                                >
                                  🌐 {company.finder_data.contact.website}
                                </a>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Key People */}
                        {company.finder_data.key_people && company.finder_data.key_people.length > 0 && (
                          <div className="bg-white rounded p-2 border border-violet-100">
                            <p className="text-xs font-semibold text-violet-600 mb-1.5">
                              Key People ({company.finder_data.key_people.length})
                            </p>
                            <div className="space-y-1.5">
                              {company.finder_data.key_people.slice(0, 5).map((person, pidx) => (
                                <div key={pidx} className="text-xs border-l-2 border-violet-300 pl-2">
                                  <div className="font-semibold text-gray-900">{person.name}</div>
                                  {person.title && (
                                    <div className="text-gray-600">{person.title}</div>
                                  )}
                                  {person.email && (
                                    <div className="text-blue-600 font-medium">{person.email}</div>
                                  )}
                                </div>
                              ))}
                              {company.finder_data.key_people.length > 5 && (
                                <p className="text-xs text-gray-500 italic">
                                  +{company.finder_data.key_people.length - 5} more...
                                </p>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Original website */}
                    {company.website && (
                      <a 
                        href={company.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:text-blue-800 hover:underline block mb-2 font-medium"
                      >
                        🌐 {company.website}
                      </a>
                    )}

                    {/* Enriched contacts from website scraping */}
                    {company.contact_info?.contacts?.length > 0 && (
                      <div className="mt-3 bg-emerald-50 rounded p-3 border border-emerald-200">
                        <p className="text-xs font-semibold text-emerald-700 mb-2 flex items-center gap-1">
                          <TrendingUp size={14} />
                          Direct Contacts from Website:
                        </p>
                        {company.contact_info.contacts.map((contact, cidx) => (
                          <div key={cidx} className="text-sm text-gray-800 ml-2 mb-1.5 border-l-2 border-emerald-400 pl-2">
                            {contact.name && <span className="font-medium text-gray-900">{contact.name}</span>}
                            {contact.title && <span className="text-gray-600"> • {contact.title}</span>}
                            {contact.email && <span className="text-emerald-600 block">{contact.email}</span>}
                            {contact.phone && <span className="text-gray-700 block">{contact.phone}</span>}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Additional emails */}
                    {company.contact_info?.emails?.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-semibold text-gray-700 mb-1">Additional Emails:</p>
                        <div className="flex flex-wrap gap-1">
                          {company.contact_info.emails.map((email, eidx) => (
                            <span key={eidx} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded font-medium">
                              {email}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Phone numbers */}
                    {company.contact_info?.phones?.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-semibold text-gray-700 mb-1">Phone Numbers:</p>
                        <p className="text-xs text-gray-600 ml-2">
                          {company.contact_info.phones.join(', ')}
                        </p>
                      </div>
                    )}

                    {/* AI Insights */}
                    {company.ai_insights && (
                      <div className="mt-3 bg-blue-50 rounded p-3 border border-blue-200">
                        <p className="text-xs font-semibold text-blue-700 mb-2 flex items-center gap-1">
                          <Sparkles size={14} />
                          AI Business Insights:
                        </p>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {company.ai_insights.company_size && (
                            <div>
                              <span className="text-gray-600">Size:</span>
                              <span className="ml-1 font-medium text-gray-900">{company.ai_insights.company_size}</span>
                            </div>
                          )}
                          {company.ai_insights.growth_stage && (
                            <div>
                              <span className="text-gray-600">Stage:</span>
                              <span className="ml-1 font-medium text-gray-900">{company.ai_insights.growth_stage}</span>
                            </div>
                          )}
                          {company.ai_insights.priority_score && (
                            <div className="col-span-2">
                              <span className="text-gray-600">Priority:</span>
                              <span className={`ml-1 font-medium ${
                                company.ai_insights.priority_score === 'High' ? 'text-green-600' :
                                company.ai_insights.priority_score === 'Medium' ? 'text-yellow-600' :
                                'text-gray-600'
                              }`}>{company.ai_insights.priority_score}</span>
                            </div>
                          )}
                          {company.ai_insights.best_contact_approach && (
                            <div className="col-span-2">
                              <span className="text-gray-600">Contact Approach:</span>
                              <p className="text-gray-900 mt-1">{company.ai_insights.best_contact_approach}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}