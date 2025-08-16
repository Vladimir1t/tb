import React from 'react';

const Tabs = ({ activeTab, onTabClick }) => {
  return (
    <div className="tabs">
      <div 
        className={`tab ${activeTab === 'channels' ? 'active' : ''}`} 
        onClick={() => onTabClick('channels')}
      >
        Каналы
      </div>
      <div 
        className={`tab ${activeTab === 'bots' ? 'active' : ''}`} 
        onClick={() => onTabClick('bots')}
      >
        Боты
      </div>
      <div 
        className={`tab ${activeTab === 'apps' ? 'active' : ''}`} 
        onClick={() => onTabClick('apps')}
      >
        Мини-приложения
      </div>
    </div>
  );
};

export default Tabs;