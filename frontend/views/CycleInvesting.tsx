
import React from 'react';
import { CYCLE_ANALYSIS } from '../constants';

const CycleInvesting: React.FC = () => {
  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="text-center max-w-2xl mx-auto space-y-4">
        <h2 className="text-4xl font-extrabold text-gray-900">万物皆有周期</h2>
        <p className="text-gray-500 leading-relaxed">
          市场就像鐘摆，总是在过度乐观与过度悲观之间摇摆。理解周期，是为了在恐惧中看到希望，在贪婪中保持理智。
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {CYCLE_ANALYSIS.map((item, idx) => (
          <div key={idx} className="bg-white rounded-3xl p-8 border border-gray-100 shadow-sm hover:shadow-lg transition-all">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-800">{item.asset}</h3>
              <span className={`
                px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider
                ${item.stage === '底部复苏' ? 'bg-emerald-100 text-emerald-700' : 
                  item.stage === '成长期' ? 'bg-blue-100 text-blue-700' :
                  item.stage === '过热期' ? 'bg-rose-100 text-rose-700' :
                  item.stage === '衰退期' ? 'bg-amber-100 text-amber-700' : 'bg-purple-100 text-purple-700'}
              `}>
                {item.stage}
              </span>
            </div>

            <div className="space-y-6">
              {/* Progress Bar / Cycle Indicator */}
              <div>
                <div className="flex justify-between text-xs font-semibold text-gray-400 mb-2">
                  <span>周期起点</span>
                  <span>当前位置: {item.progress}%</span>
                  <span>周期终点</span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-1000 ${
                      item.stage === '过热期' ? 'bg-rose-500' : 
                      item.stage === '筑底期' ? 'bg-purple-500' : 'bg-indigo-500'
                    }`}
                    style={{ width: `${item.progress}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-2xl border-l-4 border-indigo-400">
                  <h4 className="text-xs font-bold text-gray-400 uppercase mb-1">当前分析</h4>
                  <p className="text-gray-700 text-sm leading-relaxed">{item.description}</p>
                </div>

                <div className="bg-indigo-50 p-4 rounded-2xl border-l-4 border-indigo-600">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase mb-1">投资策略</h4>
                  <p className="text-indigo-900 text-sm font-semibold leading-relaxed">{item.suggestion}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 rounded-3xl p-10 text-white text-center relative overflow-hidden">
        <div className="relative z-10">
          <h3 className="text-2xl font-bold mb-4">耐心，是投资者最好的武器</h3>
          <p className="text-gray-400 max-w-2xl mx-auto mb-8">
            大多数投资者输在了黎明前的黑暗。穿越周期不仅需要资金，更需要一颗不被短期波动所迷惑的心。
          </p>
          <div className="flex justify-center space-x-4">
            <span className="px-4 py-2 bg-gray-800 rounded-lg text-xs border border-gray-700">长期主义</span>
            <span className="px-4 py-2 bg-gray-800 rounded-lg text-xs border border-gray-700">价值发现</span>
            <span className="px-4 py-2 bg-gray-800 rounded-lg text-xs border border-gray-700">情绪控制</span>
          </div>
        </div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500 opacity-10 blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-500 opacity-10 blur-3xl translate-y-1/2 -translate-x-1/2"></div>
      </div>
    </div>
  );
};

export default CycleInvesting;
