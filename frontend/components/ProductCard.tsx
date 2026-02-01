
import React from 'react';
import { Product } from '../types';

interface ProductCardProps {
  product: Product;
  isFavorited: boolean;
  onToggleFavorite: (id: string) => void;
  onShare: (product: Product) => void;
}

const ProductCard: React.FC<ProductCardProps> = ({ product, isFavorited, onToggleFavorite, onShare }) => {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow group">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900 group-hover:text-indigo-600 transition-colors">{product.name}</h3>
          <p className="text-sm text-gray-500 font-mono mt-0.5">{product.code}</p>
        </div>
        <div className="flex space-x-1">
          <button 
            onClick={() => onShare(product)}
            className="p-2 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 rounded-full transition-colors"
            title="分享"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </button>
          <button 
            onClick={() => onToggleFavorite(product.id)}
            className={`p-2 rounded-full transition-colors ${isFavorited ? 'text-rose-500 bg-rose-50' : 'text-gray-400 hover:text-rose-500 hover:bg-rose-50'}`}
            title={isFavorited ? "取消收藏" : "加入收藏"}
          >
            <svg className="w-5 h-5" fill={isFavorited ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4 bg-gray-50 p-3 rounded-xl text-center">
        <div>
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">近1月</p>
          <p className={`font-bold ${product.returns['1m'] >= 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
            {product.returns['1m'].toFixed(2)}%
          </p>
        </div>
        <div>
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">近3月</p>
          <p className={`font-bold ${product.returns['3m'] >= 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
            {product.returns['3m'].toFixed(2)}%
          </p>
        </div>
        <div>
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">近6月</p>
          <p className={`font-bold ${product.returns['6m'] >= 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
            {product.returns['6m'].toFixed(2)}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4 text-xs text-gray-600">
        <div className="flex items-center justify-between bg-gray-50 rounded-lg px-2 py-1">
          <span className="text-gray-400">币种</span>
          <span className="font-medium text-gray-700">{product.currency ?? '—'}</span>
        </div>
        <div className="flex items-center justify-between bg-gray-50 rounded-lg px-2 py-1">
          <span className="text-gray-400">风险</span>
          <span className="font-medium text-gray-700">{product.riskLevel ?? '—'}</span>
        </div>
        <div className="flex items-center justify-between bg-gray-50 rounded-lg px-2 py-1 col-span-2">
          <span className="text-gray-400">发行方</span>
          <span className="font-medium text-gray-700 truncate" title={product.issuer ?? '—'}>
            {product.issuer ?? '—'}
          </span>
        </div>
        <div className="flex items-center justify-between bg-gray-50 rounded-lg px-2 py-1 col-span-2">
          <span className="text-gray-400">数据源</span>
          {product.url ? (
            <a
              href={product.url}
              target="_blank"
              rel="noreferrer"
              className="font-medium text-indigo-600 hover:text-indigo-500"
              title={product.url}
            >
              查看官网
            </a>
          ) : (
            <span className="font-medium text-gray-700">—</span>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] text-gray-400 font-medium">代销渠道</span>
          {product.banks.map((bank) => (
            <span key={bank} className="px-2 py-0.5 bg-indigo-50 text-indigo-600 text-[10px] font-medium rounded-md">
              {bank}
            </span>
          ))}
        </div>
        {product.manager && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] text-gray-400 font-medium">经理</span>
            <span className="px-2 py-0.5 bg-amber-50 text-amber-600 text-[10px] font-medium rounded-md">
              {product.manager}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductCard;
