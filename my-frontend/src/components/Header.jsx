import React from 'react';

const Header = ({ icon }) => {
  return (
    <div className="header">
      <img src={icon} className="channel-icon" alt="Project Icon" />
      <h2>Telegram Aggregator</h2>
      <p>Найдите лучшие каналы, боты и мини-приложения</p>
    </div>
  );
};

export default Header;