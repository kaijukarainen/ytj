import { Loader2, Clock } from 'lucide-react';

export default function ProgressBar({ 
  progress, 
  total, 
  percent, 
  currentItem, 
  estimatedTime 
}) {
  return (
    <>
      <div className="flex justify-between items-center text-sm text-gray-700 mb-2">
        <span className="font-semibold">Progress</span>
        <span className="font-mono">{progress} / {total}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
        <div 
          className="bg-gradient-to-r from-cyan-500 to-blue-600 h-3 rounded-full transition-all duration-300 flex items-center justify-end pr-2"
          style={{width: `${percent}%`}}
        >
          <span className="text-xs font-bold text-white">{Math.round(percent)}%</span>
        </div>
      </div>
      <div className="space-y-2">
        {currentItem && (
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Loader2 size={16} className="animate-spin text-cyan-600" />
            <span className="truncate">{currentItem}</span>
          </div>
        )}
        {estimatedTime && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock size={16} />
            <span>Est. time remaining: {estimatedTime}</span>
          </div>
        )}
      </div>
    </>
  );
}
