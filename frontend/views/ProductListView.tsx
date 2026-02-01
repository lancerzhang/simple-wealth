
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
  const [issuerFilter, setIssuerFilter] = useState('all');
  const [bankFilter, setBankFilter] = useState('all');
  const [currencyFilter, setCurrencyFilter] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');

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

  const filterOptions = useMemo(() => {
    const issuers = new Set<string>();
    const banks = new Set<string>();
    const currencies = new Set<string>();
    const riskLevels = new Set<string>();

    products.forEach((p) => {
      if (p.issuer) issuers.add(p.issuer);
      if (p.currency) currencies.add(p.currency);
      if (p.riskLevel) riskLevels.add(p.riskLevel);
      p.banks?.forEach((bank) => banks.add(bank));
    });

    const toSorted = (values: Set<string>) =>
      Array.from(values).sort((a, b) => a.localeCompare(b));

    return {
      issuers: toSorted(issuers),
      banks: toSorted(banks),
      currencies: toSorted(currencies),
      riskLevels: toSorted(riskLevels),
    };
  }, [products]);

  const lastUpdatedAt = useMemo(() => {
    const timestamps = products
      .map((p) => p.updatedAt)
      .filter(Boolean)
      .map((value) => Date.parse(value as string))
      .filter((value) => !Number.isNaN(value));
    if (timestamps.length === 0) return null;
    return new Date(Math.max(...timestamps));
  }, [products]);

  const formatUpdatedAt = (value: Date | null) => {
    if (!value) return '—';
    return value.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  const filteredAndSortedProducts = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    const getSearchableText = (p: Product) => {
      const values: Array<string | number | undefined> = [
        p.name,
        p.id,
        p.code,
        p.type,
        p.manager,
        p.issuer,
        p.currency,
        p.minHoldDays,
        p.riskLevel,
        p.url,
        p.registrationCode,
        p.fundCode,
        p.realProductCode,
        p.updatedAt,
        p.returns?.['1m'],
        p.returns?.['3m'],
        p.returns?.['6m'],
      ];
      if (p.banks) values.push(...p.banks);
      return values
        .filter((v) => v !== undefined && v !== null)
        .join(' ')
        .toLowerCase();
    };

    let result = products.filter(p => {
      if (query && !getSearchableText(p).includes(query)) return false;
      if (showOnlyFavorites && !favorites.includes(p.id)) return false;
      if (issuerFilter !== 'all' && p.issuer !== issuerFilter) return false;
      if (bankFilter !== 'all' && !(p.banks || []).includes(bankFilter)) return false;
      if (currencyFilter !== 'all' && p.currency !== currencyFilter) return false;
      if (riskFilter !== 'all' && p.riskLevel !== riskFilter) return false;
      return true;
    });

    result.sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      const aReturn = a.returns?.[sortBy] ?? -Infinity;
      const bReturn = b.returns?.[sortBy] ?? -Infinity;
      return bReturn - aReturn;
    });

    return result;
  }, [
    products,
    searchTerm,
    sortBy,
    showOnlyFavorites,
    favorites,
    issuerFilter,
    bankFilter,
    currencyFilter,
    riskFilter,
  ]);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-3xl font-extrabold text-gray-900">{title}</h2>
        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500">
          <span>共 {filteredAndSortedProducts.length} 款产品</span>
          <span className="text-gray-400">|</span>
          <span>数据更新时间：{formatUpdatedAt(lastUpdatedAt)}</span>
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
              placeholder="搜索任意字段：名称 / 代码 / 发行方 / 渠道 / 风险 / 币种 / 更新时间..."
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

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-gray-500 mb-1">发行方</label>
            <select
              className="bg-gray-50 border-none rounded-xl px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              value={issuerFilter}
              onChange={(e) => setIssuerFilter(e.target.value)}
            >
              <option value="all">全部发行方</option>
              {filterOptions.issuers.map((issuer) => (
                <option key={issuer} value={issuer}>
                  {issuer}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-gray-500 mb-1">渠道银行</label>
            <select
              className="bg-gray-50 border-none rounded-xl px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              value={bankFilter}
              onChange={(e) => setBankFilter(e.target.value)}
            >
              <option value="all">全部银行</option>
              {filterOptions.banks.map((bank) => (
                <option key={bank} value={bank}>
                  {bank}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-gray-500 mb-1">币种</label>
            <select
              className="bg-gray-50 border-none rounded-xl px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              value={currencyFilter}
              onChange={(e) => setCurrencyFilter(e.target.value)}
            >
              <option value="all">全部币种</option>
              {filterOptions.currencies.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-gray-500 mb-1">风险等级</label>
            <select
              className="bg-gray-50 border-none rounded-xl px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
            >
              <option value="all">全部等级</option>
              {filterOptions.riskLevels.map((risk) => (
                <option key={risk} value={risk}>
                  {risk}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-100 text-amber-700 text-sm rounded-2xl p-4">
        免责声明：数据来自互联网，无法保证完全准确与实时。使用这些数据造成的任何损失，我们概不负责。仅供参考，以各产品官网披露为准。
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
