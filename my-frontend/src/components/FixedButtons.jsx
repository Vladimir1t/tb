import React, { useEffect } from 'react';

const FixedButtons = () => {
  useEffect(() => {
    // В React DOM-манипуляции лучше делать через useEffect
    const handleScroll = () => {
      const toTopBtn = document.getElementById("toTopBtn");
      if (toTopBtn) {
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
          toTopBtn.style.display = "block";
        } else {
          toTopBtn.style.display = "none";
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="tg-button-container">
      <button className="btn profile-btn" id="profileBtn">Мой профиль</button>
      <button id="toTopBtn" className="to-top-btn" onClick={scrollToTop}>↑</button>
    </div>
  );
};

export default FixedButtons;