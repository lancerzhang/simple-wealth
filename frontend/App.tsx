
import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Home from './views/Home';
import ProductListView from './views/ProductListView';
import CycleInvesting from './views/CycleInvesting';
import { ViewType } from './types';
import { WEALTH_PRODUCTS, FUND_PRODUCTS } from './constants';

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<ViewType>('home');

  // Handle back button / hash routing manually for SPA behavior without a router library
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '') as ViewType;
      if (['home', 'wealth', 'fund', 'cycle'].includes(hash)) {
        setActiveView(hash);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    handleHashChange(); // Initial load

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigateTo = (view: ViewType) => {
    window.location.hash = view;
    setActiveView(view);
  };

  const renderContent = () => {
    switch (activeView) {
      case 'home':
        return <Home />;
      case 'wealth':
        return <ProductListView products={WEALTH_PRODUCTS} title="理财产品" type="wealth" />;
      case 'fund':
        return <ProductListView products={FUND_PRODUCTS} title="基金产品" type="fund" />;
      case 'cycle':
        return <CycleInvesting />;
      default:
        return <Home />;
    }
  };

  return (
    <Layout activeView={activeView} onNavigate={navigateTo}>
      {renderContent()}
    </Layout>
  );
};

export default App;
