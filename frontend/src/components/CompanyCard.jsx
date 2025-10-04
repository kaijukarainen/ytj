import { CheckCircle, ShieldCheck, TrendingUp, Sparkles } from 'lucide-react';
import FinderDataSection from './FinderDataSection';

export default function CompanyCard({ company }) {
  const hasEnrichedData = company.contact_info?.emails?.length > 0 || 
                          company.contact_info?.contacts?.length > 0;
  const isVerifiedOnFinder = company.finder_data?.verified_on_finder;
  
  return (
    <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
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

      {/* Finder.fi Data */}
      {company.finder_data && (
        <FinderDataSection finderData={company.finder_data} />
      )}

      {/* Website */}
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

      {/* Enriched Contacts */}
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

      {/* Additional Emails */}
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

      {/* Phone Numbers */}
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
}
