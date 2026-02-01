
import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Home from './views/Home';
import ProductListView from './views/ProductListView';
import CycleInvesting from './views/CycleInvesting';
import { ViewType, Product, CycleData } from './types';

const dataBase = import.meta.env.BASE_URL ?? '/';

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<ViewType>('home');
  const [wealthProducts, setWealthProducts] = useState<Product[]>([]);
  const [fundProducts, setFundProducts] = useState<Product[]>([]);
  const [cycleAnalysis, setCycleAnalysis] = useState<CycleData[]>([]);

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

  useEffect(() => {
    let cancelled = false;
    const fetchJson = async <T,>(fileName: string): Promise<T> => {
      const response = await fetch(`${dataBase}data/${fileName}`);
      if (!response.ok) {
        throw new Error(`Failed to load ${fileName}: ${response.status}`);
      }
      return response.json() as Promise<T>;
    };

    const loadData = async () => {
      try {
        const [wealth, fund, cycle] = await Promise.all([
          fetchJson<Product[]>('wealth.json'),
          fetchJson<Product[]>('fund.json'),
          fetchJson<CycleData[]>('cycle.json')
        ]);
        if (cancelled) return;
        setWealthProducts(wealth);
        setFundProducts(fund);
        setCycleAnalysis(cycle);
      } catch (error) {
        console.error('Failed to load data files', error);
      }
    };

    loadData();
    return () => {
      cancelled = true;
    };
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
        return <ProductListView products={wealthProducts} title="理财产品" type="wealth" />;
      case 'fund':
        return <ProductListView products={fundProducts} title="基金产品" type="fund" />;
      case 'cycle':
        return <CycleInvesting data={cycleAnalysis} />;
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
