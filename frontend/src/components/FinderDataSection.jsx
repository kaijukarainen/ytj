import { TrendingUp } from 'lucide-react';

export default function FinderDataSection({ finderData }) {
  return (
    <div className="mb-3 bg-gradient-to-br from-violet-50 to-purple-50 rounded-lg p-3 border border-violet-200 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-bold text-violet-700 flex items-center gap-1">
          <TrendingUp size={14} />
          Finder.fi Business Intelligence
        </p>
        <a 
          href={finderData.finder_url} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="text-xs text-violet-600 hover:text-violet-800 hover:underline font-medium"
        >
          View Full Profile →
        </a>
      </div>

      {/* Basic Info Grid */}
      {finderData.basic_info && Object.keys(finderData.basic_info).length > 0 && (
        <div className="grid grid-cols-2 gap-2 mb-2">
          {finderData.basic_info.founded && (
            <div className="bg-white rounded p-2 border border-violet-100">
              <p className="text-xs text-gray-500 mb-0.5">Founded</p>
              <p className="text-sm font-semibold text-gray-900">
                📅 {finderData.basic_info.founded}
              </p>
            </div>
          )}
          {finderData.basic_info.employees && (
            <div className="bg-white rounded p-2 border border-violet-100">
              <p className="text-xs text-gray-500 mb-0.5">Employees</p>
              <p className="text-sm font-semibold text-gray-900">
                👥 {finderData.basic_info.employees}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Financial Info */}
      {finderData.financials && Object.keys(finderData.financials).length > 0 && (
        <div className="bg-white rounded p-2 border border-violet-100 mb-2">
          <p className="text-xs font-semibold text-violet-600 mb-1.5">Financial Data</p>
          <div className="space-y-1">
            {finderData.financials.revenue && (
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">💰 Revenue:</span>
                <span className="text-sm font-semibold text-gray-900">
                  {finderData.financials.revenue}
                </span>
              </div>
            )}
            {finderData.financials.operating_profit && (
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">📊 Operating Profit:</span>
                <span className="text-sm font-semibold text-gray-900">
                  {finderData.financials.operating_profit}
                </span>
              </div>
            )}
            {finderData.financials.financial_year && (
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">📅 Financial Year:</span>
                <span className="text-xs text-gray-700">
                  {finderData.financials.financial_year}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Contact Info from Finder */}
      {finderData.contact && Object.keys(finderData.contact).length > 0 && (
        <div className="bg-white rounded p-2 border border-violet-100 mb-2">
          <p className="text-xs font-semibold text-violet-600 mb-1.5">Contact Information</p>
          <div className="space-y-1 text-xs">
            {finderData.contact.address && (
              <div className="text-gray-700">📍 {finderData.contact.address}</div>
            )}
            {finderData.contact.phone && (
              <div className="text-gray-700">📞 {finderData.contact.phone}</div>
            )}
            {finderData.contact.email && (
              <div className="text-blue-600 font-medium">
                ✉️ {finderData.contact.email}
              </div>
            )}
            {finderData.contact.website && (
              <a 
                href={finderData.contact.website} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline block"
              >
                🌐 {finderData.contact.website}
              </a>
            )}
          </div>
        </div>
      )}

      {/* Key People */}
      {finderData.key_people && finderData.key_people.length > 0 && (
        <div className="bg-white rounded p-2 border border-violet-100">
          <p className="text-xs font-semibold text-violet-600 mb-1.5">
            Key People ({finderData.key_people.length})
          </p>
          <div className="space-y-1.5">
            {finderData.key_people.slice(0, 5).map((person, pidx) => (
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
            {finderData.key_people.length > 5 && (
              <p className="text-xs text-gray-500 italic">
                +{finderData.key_people.length - 5} more...
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
