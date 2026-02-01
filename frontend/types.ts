
export interface Product {
  id: string;
  name: string;
  code: string;
  returns: {
    '1m': number;
    '3m': number;
    '6m': number;
  };
  banks: string[];
  type: 'wealth' | 'fund';
  manager?: string;
}

export interface CycleData {
  asset: string;
  stage: '底部复苏' | '成长期' | '过热期' | '衰退期' | '筑底期';
  progress: number; // 0 to 100
  description: string;
  suggestion: string;
}

export type ViewType = 'home' | 'wealth' | 'fund' | 'cycle';
