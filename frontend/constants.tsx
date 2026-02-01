
import React from 'react';
import { Product, CycleData } from './types';

export const WEALTH_PRODUCTS: Product[] = [
  {
    id: 'w1',
    name: '中银理财-乐享天天',
    code: 'BOC001',
    returns: { '1m': 2.45, '3m': 2.60, '6m': 2.85 },
    banks: ['中国银行', '招商银行'],
    type: 'wealth'
  },
  {
    id: 'w2',
    name: '招银理财-朝招金',
    code: 'CMB888',
    returns: { '1m': 2.15, '3m': 2.30, '6m': 2.40 },
    banks: ['招商银行'],
    type: 'wealth'
  },
  {
    id: 'w3',
    name: '工银理财-随心快线',
    code: 'ICBC002',
    returns: { '1m': 2.65, '3m': 2.55, '6m': 2.70 },
    banks: ['工商银行', '建设银行'],
    type: 'wealth'
  },
  {
    id: 'w4',
    name: '交银理财-稳健增长',
    code: 'BOCOM321',
    returns: { '1m': 3.10, '3m': 3.45, '6m': 3.80 },
    banks: ['交通银行'],
    type: 'wealth'
  }
];

export const FUND_PRODUCTS: Product[] = [
  {
    id: 'f1',
    name: '易方达蓝筹精选',
    code: '005827',
    returns: { '1m': -1.2, '3m': 5.4, '6m': 12.5 },
    banks: ['招商银行', '天天基金', '蚂蚁理财'],
    type: 'fund',
    manager: '张坤'
  },
  {
    id: 'f2',
    name: '中欧医疗健康混合',
    code: '003095',
    returns: { '1m': 2.5, '3m': -4.2, '6m': -8.1 },
    banks: ['平安银行', '天天基金'],
    type: 'fund',
    manager: '葛兰'
  },
  {
    id: 'f3',
    name: '华夏上证50ETF',
    code: '510050',
    returns: { '1m': 1.8, '3m': 4.5, '6m': 8.2 },
    banks: ['各大券商'],
    type: 'fund',
    manager: '张弘弢'
  }
];

export const CYCLE_ANALYSIS: CycleData[] = [
  {
    asset: 'A股市场',
    stage: '筑底期',
    progress: 20,
    description: '当前估值处于历史低位，政策底已现，市场正在反复磨底。',
    suggestion: '保持耐心，分批布局蓝筹及高股息资产。'
  },
  {
    asset: '美股纳指',
    stage: '过热期',
    progress: 85,
    description: 'AI浪潮推升科技股溢价，估值偏高，需警惕回调风险。',
    suggestion: '适当止盈，关注防御性品种。'
  },
  {
    asset: '实物黄金',
    stage: '成长期',
    progress: 60,
    description: '避险情绪及全球央行增持支撑金价震荡上行。',
    suggestion: '逢低吸纳，作为配置中的压舱石。'
  },
  {
    asset: '房地产市场',
    stage: '衰退期',
    progress: 95,
    description: '人口结构变化及金融周期导致长期调整压力。',
    suggestion: '刚需审慎，投资需避开三四线城市。'
  }
];
