import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setProjects, setLoading, setError } from './store/projectsSlice';

import Header from './Header';
import Tabs from './Tabs';
import SearchBar from './SearchBar';
import Card from './Card';
import HelpSection from './HelpSection';
import FixedButtons from './FixedButtons';
import Loading from './Loading';
import NoResults from './NoResults';

import './styles.css';

const API_URL = 'https://telegram-bot-chi-lyart.vercel.app/'; // Ваш URL
const project = { icon: 'https://via.placeholder.com/40' };

const App = () => {
  const dispatch = useDispatch();
  const projects = useSelector(state => state.projects.items);
  const loading = useSelector(state => state.projects.loading);
  const error = useSelector(state => state.projects.error);
  
  const [activeTab, setActiveTab] = useState('channels');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchProjects = async () => {
      dispatch(setLoading(true));
      dispatch(setError(null));
      const typeMap = {
        'channels': 'channel',
        'bots': 'bot',
        'apps': 'mini_app',
      };
      const apiType = typeMap[activeTab];

      try {
        const response = await fetch(`${API_URL}/projects/?type=${apiType}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        dispatch(setProjects(data));
      } catch (e) {
        dispatch(setError(e.message));
      } finally {
        dispatch(setLoading(false));
      }
    };

    fetchProjects();
  }, [activeTab, dispatch]);

  const filteredProjects = projects.filter(project => {
    const title = project.name.toLowerCase();
    const theme = (project.theme || '').toLowerCase();
    const query = searchQuery.toLowerCase().trim();

    return title.includes(query) || theme.includes(query);
  });

  return (
    <div className="container">
      <Header icon={project.icon} />
      <Tabs activeTab={activeTab} onTabClick={setActiveTab} />
      <SearchBar onSearchChange={setSearchQuery} />

      <div id={`${activeTab}-tab`} className="tab-content active">
        {loading && <Loading />}
        {error && <div className="loading">Ошибка: {error}</div>}
        {!loading && !error && filteredProjects.length === 0 && <NoResults />}
        
        {filteredProjects.map((proj, index) => (
          <Card key={index} project={proj} />
        ))}
      </div>

      <HelpSection />
      <FixedButtons />
    </div>
  );
};

export default App;