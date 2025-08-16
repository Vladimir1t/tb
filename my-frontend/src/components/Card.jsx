import React from 'react';

const Card = ({ project }) => {
  return (
    <div className={`card ${project.is_premium ? 'premium-card' : ''}`}>
      {project.is_premium && <div className="premium-badge">PREMIUM</div>}
      <img 
        src={project.icon || 'https://via.placeholder.com/40'} 
        className="channel-icon" 
        alt="Channel Icon"
      />
      <h3>{project.name}</h3>
      <p>Тематика: {project.theme}</p>
      {project.subscribers && <p>Подписчиков: {project.subscribers.toLocaleString()}</p>}
      <a href={project.link} className="btn">Перейти</a>
      <div className="likes">
        ❤️ <span>{project.likes || 0}</span>
      </div>
    </div>
  );
};

export default Card;