
import React, { useState, useMemo, useEffect } from 'react';
import { Product } from '../types';
import ProductCard from '../components/ProductCard';

interface ProductListViewProps {
  products: Product[];
  title: string;
  type: 'wealth' | 'fund';
}

const ProductListView: React.FC<ProductListViewProps> = ({ products, title, type }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | '1m' | '3m' | '6m'>('name');
  const [showOnlyFavorites, setShowOnlyFavorites] = useState(false);
  const [favorites, setFavorites] = useState<string[]>([]);

  // Load favorites from local storage on mount
  useEffect(() => {
    const saved = localStorage.getItem('finance_favorites');
    if (saved) {
      try {
        setFavorites(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse favorites", e);
      }
    }
  }, []);

  const toggleFavorite = (id: string) => {
    const newFavorites = favorites.includes(id)
      ? favorites.filter(favId => favId !== id)
      : [...favorites, id];
    
    setFavorites(newFavorites);
    localStorage.setItem('finance_favorites', JSON.stringify(newFavorites));
  };

  const handleShare = (product: Product) => {
    const shareText = `【${title}分享】\n产品名称：${product.name}\n产品编号：${product.code}\n近6月收益：${product.returns['6m']}%\n在售渠道：${product.banks.join('、')}`;
    
    if (navigator.share) {
      navigator.share({
        title: product.name,
        text: shareText,
        url: window.location.href
      }).catch(err => console.log('Error sharing', err));
    } else {
      navigator.clipboard.writeText(shareText);
      alert('产品信息已复制到剪贴板，快去分享吧！');
    }
  };

  const filteredAndSortedProducts = useMemo(() => {
    let result = products.filter(p => 
      (p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
       p.code.toLowerCase().includes(searchTerm.toLowerCase())) &&
      (!showOnlyFavorites || favorites.includes(p.id))
    );

    result.sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      return b.returns[sortBy] - a.returns[sortBy];
    });

    return result;
  }, [products, searchTerm, sortBy, showOnlyFavorites, favorites]);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-3xl font-extrabold text-gray-900">{title}</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <span>共 {filteredAndSortedProducts.length} 款产品</span>
          <button 
            onClick={() => handleShare({ name: title, code: 'FinanceTool', returns: { '1m': 0, '3m': 0, '6m': 0 }, banks: ['Web'], type: 'wealth' } as any)}
            className="p-1.5 hover:bg-gray-100 rounded-lg"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <input 
              type="text" 
              placeholder="搜索产品名称或代码..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-indigo-500 transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <svg className="w-5 h-5 absolute left-3 top-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          </div>
          
          <div className="flex gap-2">
            <select 
              className="bg-gray-50 border-none rounded-xl px-4 py-2 text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
            >
              <option value="name">按名称排序</option>
              <option value="1m">近1月收益率</option>
              <option value="3m">近3月收益率</option>
              <option value="6m">近6月收益率</option>
            </select>

            <button
              onClick={() => setShowOnlyFavorites(!showOnlyFavorites)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${showOnlyFavorites ? 'bg-rose-50 text-rose-600' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
            >
              <svg className={`w-4 h-4 ${showOnlyFavorites ? 'fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
              <span>{showOnlyFavorites ? '显示全部' : '只看收藏'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Grid */}
      {filteredAndSortedProducts.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAndSortedProducts.map((p) => (
            <ProductCard 
              key={p.id}
              product={p}
              isFavorited={favorites.includes(p.id)}
              onToggleFavorite={toggleFavorite}
              onShare={handleShare}
            />
          ))}
        </div>
      ) : (
        <div className="bg-white border border-dashed border-gray-200 rounded-3xl p-20 text-center">
          <div className="w-16 h-16 bg-gray-50 text-gray-300 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 9.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <h3 className="text-xl font-bold text-gray-400">未找到相关产品</h3>
          <p className="text-gray-400 text-sm mt-1">请尝试更换搜索词或取消过滤条件</p>
        </div>
      )}
    </div>
  );
};

export default ProductListView;
