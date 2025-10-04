import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ScraperForm from './components/ScraperForm';
import AIAgentPanel from './components/AIAgentPanel';
import ResultsSection from './components/ResultsSection';

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
    // Fetch business lines
    fetch('http://localhost:5001/api/business-lines')
      .then(res => res.json())
      .then(data => setBusinessLines(data))
      .catch(err => console.error('Error fetching business lines:', err));

    // Poll for status updates
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
      await response.json();
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
      await response.json();
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
      await response.json();
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

  const getEstimatedTime = (progress, total, startTime) => {
    if (!startTime || progress === 0) return null;
    const elapsed = (Date.now() - startTime) / 1000;
    const avgTimePerItem = elapsed / progress;
    const remaining = (total - progress) * avgTimePerItem;
    const minutes = Math.floor(remaining / 60);
    const seconds = Math.floor(remaining % 60);
    return `${minutes}m ${seconds}s`;
  };

  const scrapingProgress = status?.scraping?.progress || 0;
  const scrapingTotal = status?.scraping?.total || 0;
  const estimatedTime = status?.scraping?.is_running 
    ? getEstimatedTime(scrapingProgress, scrapingTotal, startTime) 
    : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <Header />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <ScraperForm
            params={params}
            setParams={setParams}
            businessLines={businessLines}
            onStart={startScraping}
            status={status}
            estimatedTime={estimatedTime}
          />

          <AIAgentPanel
            openaiKey={openaiKey}
            setOpenaiKey={setOpenaiKey}
            onEnrich={enrichWithAgent}
            status={status}
            hasResults={results.length > 0}
          />
        </div>

        {results.length > 0 && (
          <ResultsSection
            results={results}
            cacheStats={cacheStats}
            onDownloadJSON={downloadResults}
            onDownloadCSV={downloadCSV}
            onDownloadValidatedCSV={downloadValidatedCSV}
            onClearCache={clearCache}
            validationConfig={validationConfig}
            setValidationConfig={setValidationConfig}
            onValidate={validateWithFinder}
            status={status}
          />
        )}
      </div>
    </div>
  );
}
