
import React from 'react';

const Home: React.FC = () => {
  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="bg-indigo-600 rounded-3xl p-8 md:p-12 text-white relative overflow-hidden shadow-xl shadow-indigo-100">
        <div className="relative z-10 max-w-2xl">
          <h2 className="text-3xl md:text-5xl font-extrabold mb-4 leading-tight">投资理财，<br/>本该如此简单。</h2>
          <p className="text-indigo-100 text-lg md:text-xl font-medium leading-relaxed opacity-90">
            这是一个专注个人理财数据的开源网站，提供清爽、无广告、极速的理财和基金查询体验。
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <button className="px-6 py-3 bg-white text-indigo-600 font-bold rounded-xl hover:bg-indigo-50 transition-colors">
              开始使用
            </button>
            <a 
              href="https://github.com" 
              className="px-6 py-3 bg-indigo-500 text-white font-bold rounded-xl hover:bg-indigo-400 transition-colors"
            >
              提交 PR
            </a>
          </div>
        </div>
        <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-indigo-500 rounded-full opacity-20 blur-3xl"></div>
        <div className="absolute right-10 top-10 w-40 h-40 bg-indigo-400 rounded-full opacity-20 blur-2xl"></div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center mb-4">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
          </div>
          <h3 className="text-xl font-bold mb-2">个人开发 · 自用</h3>
          <p className="text-gray-500 text-sm leading-relaxed">
            作者因不满市面理财 App 的臃肿与广告，利用业余时间开发此网站，旨在回归理财最纯粹的模样。
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center mb-4">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
          </div>
          <h3 className="text-xl font-bold mb-2">无广告 · 开源</h3>
          <p className="text-gray-500 text-sm leading-relaxed">
            核心逻辑全前端运行，完全免费且无任何商业套路。如果你喜欢这个项目，欢迎点一个 Star 或者提交优化代码。
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mb-4">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
          </div>
          <h3 className="text-xl font-bold mb-2">社区驱动</h3>
          <p className="text-gray-500 text-sm leading-relaxed">
            理财数据维护由社区共同参与，如果你发现更好的理财产品或基金，欢迎通过 GitHub 提交 JSON 数据更新。
          </p>
        </div>
      </div>

      <div className="bg-white border border-gray-100 p-8 rounded-3xl text-center">
        <h3 className="text-2xl font-bold mb-4 text-gray-800">想要加入我们？</h3>
        <p className="text-gray-500 max-w-xl mx-auto mb-6">
          "简单理财" 不仅仅是一个工具，更是一种理性的理财态度。我们追求长期稳健的回报，而非短期的投机。
        </p>
        <button className="bg-gray-900 text-white px-8 py-3 rounded-xl font-semibold hover:bg-black transition-colors">
          前往 GitHub 贡献
        </button>
      </div>

      <div className="bg-amber-50 border border-amber-100 text-amber-700 text-sm rounded-2xl p-5">
        免责声明：本网站数据来源于互联网公开信息，可能存在延迟或误差，不保证完全准确与实时。使用本网站数据造成的任何损失，本站不承担责任。仅供参考，具体以各产品官网披露为准。
      </div>
    </div>
  );
};

export default Home;
