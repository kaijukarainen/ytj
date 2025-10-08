import { Database, Save, Trash2, Calendar, TrendingUp } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function DatabasePanel({ results, params }) {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/db/sessions?limit=10');
      const data = await response.json();
      if (data.success) {
        setSessions(data.sessions);
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
    }
  };

  const saveToDatabase = async () => {
    if (!results || results.length === 0) {
      alert('No results to save');
      return;
    }

    setSaving(true);
    try {
      const response = await fetch('http://localhost:5001/api/db/save-results', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          companies: results,
          business_line: params.main_business_line,
          location: params.location,
          company_form: params.company_form
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert(`✓ Saved ${data.count} companies to database (Session #${data.session_id})`);
        fetchSessions(); // Refresh session list
      } else {
        alert('Error: ' + data.error);
      }
    } catch (err) {
      alert('Error saving to database: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const response = await fetch(`http://localhost:5001/api/db/companies/session/${sessionId}`);
      const data = await response.json();
      
      if (data.success) {
        setSelectedSession({
          id: sessionId,
          companies: data.companies,
          count: data.count
        });
      }
    } catch (err) {
      console.error('Error loading session:', err);
    }
  };

  const deleteSession = async (sessionId) => {
    if (!confirm('Are you sure you want to delete this session and all its companies?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:5001/api/db/sessions/${sessionId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
        alert('✓ Session deleted successfully');
        fetchSessions();
        if (selectedSession?.id === sessionId) {
          setSelectedSession(null);
        }
      } else {
        alert('Error: ' + data.error);
      }
    } catch (err) {
      alert('Error deleting session: ' + err.message);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('fi-FI');
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Database size={24} className="text-purple-600" />
          Database
        </h2>
        
        <button
          onClick={saveToDatabase}
          disabled={saving || !results || results.length === 0}
          className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-md"
        >
          {saving ? (
            <>
              <Database size={18} className="animate-pulse" />
              Saving...
            </>
          ) : (
            <>
              <Save size={18} />
              Save to DB
            </>
          )}
        </button>
      </div>

      {/* Recent Sessions */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Calendar size={16} />
          Recent Sessions ({sessions.length})
        </h3>
        
        {sessions.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No saved sessions yet</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-3 border-2 cursor-pointer transition-all ${
                  selectedSession?.id === session.id
                    ? 'border-purple-400 shadow-md'
                    : 'border-purple-200 hover:border-purple-300'
                }`}
                onClick={() => loadSession(session.id)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-purple-700">
                        Session #{session.id}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                        session.status === 'completed' 
                          ? 'bg-green-100 text-green-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {session.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      {formatDate(session.timestamp)}
                    </p>
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.id);
                    }}
                    className="text-red-500 hover:text-red-700 p-1"
                    title="Delete session"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {session.business_line && (
                    <div>
                      <span className="text-gray-500">Business Line:</span>
                      <span className="ml-1 font-medium text-gray-900">
                        {session.business_line}
                      </span>
                    </div>
                  )}
                  {session.location && (
                    <div>
                      <span className="text-gray-500">Location:</span>
                      <span className="ml-1 font-medium text-gray-900">
                        {session.location}
                      </span>
                    </div>
                  )}
                  <div className="col-span-2">
                    <span className="text-gray-500">Companies:</span>
                    <span className="ml-1 font-bold text-purple-700">
                      {session.total_companies}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Session Details */}
      {selectedSession && (
        <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-4 border-2 border-purple-300">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-bold text-purple-900 flex items-center gap-2">
              <TrendingUp size={16} />
              Session #{selectedSession.id} Details
            </h4>
            <button
              onClick={() => setSelectedSession(null)}
              className="text-xs text-purple-600 hover:text-purple-800"
            >
              Close
            </button>
          </div>
          
          <div className="bg-white rounded p-3 mb-3">
            <p className="text-xs font-semibold text-gray-700 mb-2">
              Loaded {selectedSession.count} companies
            </p>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {selectedSession.companies.slice(0, 10).map((company, idx) => (
                <div key={idx} className="text-xs bg-gray-50 rounded p-2 border border-gray-200">
                  <div className="font-semibold text-gray-900">{company.name}</div>
                  <div className="text-gray-600">{company.business_id}</div>
                  {company.website && (
                    <div className="text-blue-600 truncate">{company.website}</div>
                  )}
                </div>
              ))}
              {selectedSession.count > 10 && (
                <p className="text-xs text-gray-500 italic text-center pt-2">
                  ... and {selectedSession.count - 10} more
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
