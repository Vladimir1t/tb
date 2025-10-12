const tg = window.Telegram.WebApp;
tg.expand();

// Инициализация темы и пользователя
initializeTelegramTheme();
initializeUserProfile();

// API Configuration
const API_URL = 'https://tcatalogbot.ru/api';

// Global State
let searchTimeout;
let currentFilter = 'все';
let currentContentType = 'all';
let currentSubcategory = null;
let page = 0;
let hasMore = true;
let loading = false;
let currentCategoryType = null;
let categoryPage = 0;
let categoryHasMore = true;
let categoryLoading = false;
let isInCategoryPage = false;
let isSearchCollapsed = false;

// DOM Elements
const toTopBtn = document.getElementById('toTopBtn');
const searchInput = document.getElementById('searchInput');
const searchContainer = document.getElementById('searchContainer');
const searchHeader = document.getElementById('searchHeader');
const searchToggle = document.getElementById('searchToggle');
const filterBtn = document.getElementById('filterBtn');
const filterModal = document.getElementById('filterModal');
const filterModalClose = document.getElementById('filterModalClose');
const filterResetBtn = document.getElementById('filterResetBtn');
const filterApplyBtn = document.getElementById('filterApplyBtn');
const pageHeader = document.getElementById('pageHeader');
const pageTitle = document.getElementById('pageTitle');
const backButton = document.getElementById('backButton');

// Categories Data
const categoriesData = {
    'все': { name: 'Все категории', icon: '🌐', subcategories: [] },
    'новости': { name: 'Новости', icon: 'news', subcategories: ['Политика', 'Экономика', 'Мировые новости'] },
    'спорт': { name: 'Спорт', icon: 'sport', subcategories: ['Футбол', 'Хоккей', 'Теннис', 'Баскетбол'] },
    'технологии': { name: 'Технологии', icon: 'tech', subcategories: ['IT', 'Наука', 'Гаджеты', 'ИИ'] },
    'развлечения': { name: 'Развлечения', icon: 'entertainment', subcategories: ['Кино', 'Музыка', 'Игры'] },
    'образование': { name: 'Образование', icon: 'education', subcategories: ['Языки', 'Курсы', 'Книги'] },
    'бизнес': { name: 'Бизнес', icon: 'business', subcategories: ['Стартапы', 'Инвестиции', 'Криптовалюты'] }
};

// Initialize Telegram Theme
function initializeTelegramTheme() {
    const themeParams = tg.themeParams;
    
    if (themeParams) {
        const root = document.documentElement;
        
        // Set CSS variables based on Telegram theme
        if (themeParams.bg_color) root.style.setProperty('--tg-theme-bg-color', themeParams.bg_color);
        if (themeParams.text_color) root.style.setProperty('--tg-theme-text-color', themeParams.text_color);
        if (themeParams.hint_color) root.style.setProperty('--tg-theme-hint-color', themeParams.hint_color);
        if (themeParams.button_color) root.style.setProperty('--tg-theme-button-color', themeParams.button_color);
        if (themeParams.button_text_color) root.style.setProperty('--tg-theme-button-text-color', themeParams.button_text_color);
        if (themeParams.secondary_bg_color) root.style.setProperty('--tg-theme-secondary-bg-color', themeParams.secondary_bg_color);
        
        // Set header color
        tg.setHeaderColor(themeParams.header_bg_color || themeParams.secondary_bg_color || 'secondary_bg_color');
    }
    
    // Listen for theme changes
    tg.onEvent('themeChanged', function() {
        initializeTelegramTheme();
    });
}

// Initialize User Profile
function initializeUserProfile() {
    const user = tg.initDataUnsafe?.user;
    
    if (user) {
        const userNameElement = document.getElementById('userName');
        const userAvatarElement = document.getElementById('userAvatar');
        const userInitialsElement = document.getElementById('userInitials');
        
        // Set user name
        const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ');
        if (userNameElement) userNameElement.textContent = fullName || 'Пользователь';
        
        // Set avatar or initials
        if (user.photo_url && userAvatarElement) {
            userAvatarElement.src = user.photo_url;
            userAvatarElement.style.display = 'block';
            userInitialsElement.style.display = 'none';
        } else if (userInitialsElement) {
            const firstName = user.first_name || '';
            const lastName = user.last_name || '';
            
            const firstInitial = firstName.charAt(0).toUpperCase();
            const secondInitial = lastName.charAt(0).toUpperCase();
            
            const initials = firstInitial + secondInitial || (user.username?.[0]?.toUpperCase() || 'U');
            userInitialsElement.textContent = initials;
        }
    }
}

// Search Header Collapse/Expand
function toggleSearchHeader() {
    if (isSearchCollapsed) {
        expandSearchHeader();
    } else {
        collapseSearchHeader();
    }
}

function collapseSearchHeader() {
    isSearchCollapsed = true;
    searchContainer.style.display = 'none';
    searchToggle.style.display = 'flex';
    searchHeader.classList.add('collapsed');
}

function expandSearchHeader() {
    isSearchCollapsed = false;
    searchContainer.style.display = 'flex';
    searchToggle.style.display = 'none';
    searchHeader.classList.remove('collapsed');
}

// Scroll handler for search collapse
function handleScroll() {
    const scrollTop = window.pageYOffset;
    
    // Auto-collapse search when scrolling down
    if (scrollTop > 100 && !isSearchCollapsed && !isInCategoryPage) {
        collapseSearchHeader();
    }
    
    // Show/hide "To Top" button
    if (toTopBtn) {
        if (scrollTop > 300) {
            toTopBtn.style.display = 'flex';
        } else {
            toTopBtn.style.display = 'none';
        }
    }
}

// Generate random offset for content variety
function getRandomOffset() {
    return Math.floor(Math.random() * 20);
}

// Load Content Sections with Snap Scrolling
async function loadContentSections() {
    console.log('Loading content sections...');
    
    const types = [
        { type: 'channel', containerId: 'channelsContent' },
        { type: 'bot', containerId: 'botsContent' },
        { type: 'mini_app', containerId: 'appsContent' }
    ];

    for (const { type, containerId } of types) {
        const container = document.getElementById(containerId);
        if (!container) continue;

        try {
            const offset = getRandomOffset();
            const url = `${API_URL}/projects/?type=${type}&limit=10&offset=${offset}`;
            console.log(`Fetching ${type}: ${url}`);
            
            const response = await fetch(url);
            console.log(`Response for ${type}:`, response.status, response.statusText);
            
            if (response.ok) {
                const data = await response.json();
                console.log(`Data for ${type}:`, data);
                
                container.innerHTML = '';
                
                if (Array.isArray(data) && data.length > 0) {
                    data.forEach(project => {
                        const card = createProjectCard(project);
                        container.appendChild(card);
                    });
                    console.log(`Loaded ${data.length} items for ${type}`);
                } else {
                    container.innerHTML = '<div class="no-results">Контент недоступен</div>';
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error(`Error loading ${type}:`, error);
            container.innerHTML = `<div class="no-results">Ошибка загрузки</div>`;
        }
    }
}

// Create Project Card with Modern iOS Design
function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'card';
    
    if (project.is_premium) {
        card.classList.add('premium-card');
    }

    // Icon handling
    let iconHtml = '';
    if (project.icon || project.avatar_url) {
        const iconUrl = project.icon || project.avatar_url;
        iconHtml = `<img src="${iconUrl}" alt="${project.name || project.title}" class="channel-icon">`;
    } else {
        const firstLetter = (project.name || project.title || '').charAt(0).toUpperCase() || 'T';
        iconHtml = `<div class="channel-letter-badge">${firstLetter}</div>`;
    }

    const projectName = project.name || project.title || 'Без названия';
    const projectDescription = project.description || project.theme || 'Описание недоступно';
    const projectUrl = project.url || project.link || '#';
    
    const subscribersCount = project.subscribers || project.subscribers_count || project.likes || 0;
    const projectType = project.type || (project.url && project.url.includes('t.me/') && !project.url.includes('_bot') ? 'channel' : 'bot');
    
    // Show subscribers only for channels
    const showSubscribers = projectType === 'channel' || project.type === 'channel';

    card.innerHTML = `
        ${project.is_premium ? '<div class="premium-badge">Premium</div>' : ''}
        <div class="card-content">
            <a href="${projectUrl}" target="_blank" class="channel-clickable-area" data-url="${projectUrl}">
                <div class="channel-icon-container">
                    ${iconHtml}
                    <div class="channel-info">
                        <h3>${projectName}</h3>
                        <p>${projectDescription}</p>
                    </div>
                </div>
            </a>
            ${showSubscribers ? `
            <div class="subscribers-mini">
                <span class="subscribers-badge">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                    ${formatNumber(subscribersCount)}
                </span>
            </div>
            ` : ''}
        </div>
    `;

    // Add click handler
    const clickableArea = card.querySelector('.channel-clickable-area');
    clickableArea.addEventListener('click', (e) => {
        e.preventDefault();
        
        if (tg.sendData) {
            tg.sendData(JSON.stringify({
                action: 'open_project',
                project_id: project.id,
                project_title: projectName,
                project_url: projectUrl
            }));
        }
        
        window.open(projectUrl, '_blank');
    });

    return card;
}

// Format numbers for display
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Get Category Icon SVG
function getCategoryIcon(iconName) {
    const icons = {
        'news': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8z"/></svg>`,
        'sport': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>`,
        'tech': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
        'entertainment': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10,8 16,12 10,16 10,8"/></svg>`,
        'education': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
        'business': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect x="4" y="20" width="16" height="2" rx="1"/></svg>`
    };
    return icons[iconName] || icons['news'];
}

// Load Categories with Modern Icons
function loadCategories() {
    const categoriesGrid = document.getElementById('categoriesGrid');
    if (!categoriesGrid) return;

    const categories = [
        { icon: 'news', title: 'Новости', value: 'новости' },
        { icon: 'sport', title: 'Спорт', value: 'спорт' },
        { icon: 'tech', title: 'Технологии', value: 'технологии' },
        { icon: 'entertainment', title: 'Развлечения', value: 'развлечения' },
        { icon: 'education', title: 'Образование', value: 'образование' },
        { icon: 'business', title: 'Бизнес', value: 'бизнес' }
    ];

    categoriesGrid.innerHTML = '';
    categories.forEach(category => {
        const categoryItem = document.createElement('div');
        categoryItem.className = 'category-item';
        categoryItem.innerHTML = `
            <div class="category-item-icon">${getCategoryIcon(category.icon)}</div>
            <div class="category-item-title">${category.title}</div>
        `;
        
        categoryItem.addEventListener('click', () => {
            openThemeCategoryPage(category.value, category.title);
        });
        
        categoriesGrid.appendChild(categoryItem);
    });
}

// Open Category Page
async function openCategoryPage(type) {
    const typeNames = {
        'channel': 'Каналы',
        'bot': 'Боты', 
        'mini_app': 'Мини-приложения'
    };

    console.log(`Opening category page for type: ${type}`);
    
    currentCategoryType = type;
    categoryPage = 0;
    categoryHasMore = true;
    categoryLoading = false;
    isInCategoryPage = true;

    // Show page header with back button
    if (pageHeader) pageHeader.style.display = 'flex';
    if (pageTitle) pageTitle.textContent = typeNames[type];

    // Show search header expanded
    expandSearchHeader();

    // Hide main tabs and show category tab
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const categoryTab = document.getElementById('category-tab');
    if (categoryTab) {
        categoryTab.classList.add('active');
        categoryTab.style.display = 'block';
    }

    // Load content
    const categoryContent = document.getElementById('categoryContent');
    if (categoryContent) {
        categoryContent.innerHTML = '<div class="loading">Загрузка...</div>';
        await loadCategoryContent();
        addInfiniteScroll();
    }
}

// Open Theme Category Page
async function openThemeCategoryPage(categoryValue, categoryTitle) {
    currentFilter = categoryValue;
    currentSubcategory = null;
    currentCategoryType = 'theme';
    categoryPage = 0;
    categoryHasMore = true;
    categoryLoading = false;
    isInCategoryPage = true;

    // Show page header with back button
    if (pageHeader) pageHeader.style.display = 'flex';
    if (pageTitle) pageTitle.textContent = categoryTitle;

    // Show search header expanded
    expandSearchHeader();

    // Hide main tabs and show category tab
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const categoryTab = document.getElementById('category-tab');
    if (categoryTab) {
        categoryTab.classList.add('active');
        categoryTab.style.display = 'block';
    }

    // Load content
    const categoryContent = document.getElementById('categoryContent');
    if (categoryContent) {
        categoryContent.innerHTML = '<div class="loading">Загрузка...</div>';
        await loadCategoryContent();
        addInfiniteScroll();
    }
}

// Load Category Content
async function loadCategoryContent(append = false) {
    if (categoryLoading || (!categoryHasMore && append)) return;
    
    categoryLoading = true;
    const categoryContent = document.getElementById('categoryContent');

    if (!append) {
        categoryContent.innerHTML = '<div class="loading">Загрузка...</div>';
    }

    try {
        const query = searchInput?.value?.trim() || '';
        let themeFilter = currentFilter === 'все' ? '' : currentFilter;
        
        if (currentSubcategory) {
            themeFilter = currentSubcategory;
        }

        // Theme categories load mixed content
        if (currentCategoryType === 'theme') {
            const types = ['channel', 'bot', 'mini_app'];
            let allResults = [];

            for (const type of types) {
                try {
                    const searchParam = query ? `&smart_search=${encodeURIComponent(query)}` : '';
                    const themeParam = themeFilter ? `&theme=${encodeURIComponent(themeFilter)}` : '';
                    
                    const apiUrl = `${API_URL}/projects/?type=${type}${themeParam}${searchParam}&limit=4&offset=${Math.floor(categoryPage * 4 / 3)}`;
                    
                    const response = await fetch(apiUrl);
                    
                    if (response.ok) {
                        const data = await response.json();
                        if (Array.isArray(data) && data.length > 0) {
                            allResults.push(...data.slice(0, 3));
                        }
                    }
                } catch (error) {
                    console.error(`Error loading ${type} for theme:`, error);
                }
            }

            // Shuffle results for variety
            allResults.sort(() => Math.random() - 0.5);

            if (!append) {
                categoryContent.innerHTML = '';
            } else {
                const loadingElement = categoryContent.querySelector('.loading');
                if (loadingElement) loadingElement.remove();
            }

            if (allResults.length > 0) {
                const itemsToShow = allResults.slice(0, 10);
                
                itemsToShow.forEach(project => {
                    const card = createProjectCard(project);
                    categoryContent.appendChild(card);
                });

                categoryPage++;
                categoryHasMore = allResults.length >= 10;
                
                if (categoryHasMore) {
                    const loadingElement = document.createElement('div');
                    loadingElement.className = 'loading';
                    loadingElement.textContent = 'Загрузка еще...';
                    categoryContent.appendChild(loadingElement);
                }
            } else {
                if (categoryPage === 0) {
                    categoryContent.innerHTML = '<div class="no-results">Контент по данной тематике недоступен</div>';
                }
                categoryHasMore = false;
            }
        } else {
            // Regular category loading
            const searchParam = query ? `&smart_search=${encodeURIComponent(query)}` : '';
            const themeParam = themeFilter ? `&theme=${encodeURIComponent(themeFilter)}` : '';
            
            const apiUrl = `${API_URL}/projects/?type=${currentCategoryType}${themeParam}${searchParam}&limit=10&offset=${categoryPage * 10}`;
            
            const response = await fetch(apiUrl);
            
            if (response.ok) {
                const data = await response.json();
                
                if (!append) {
                    categoryContent.innerHTML = '';
                } else {
                    const loadingElement = categoryContent.querySelector('.loading');
                    if (loadingElement) loadingElement.remove();
                }

                if (Array.isArray(data) && data.length > 0) {
                    data.forEach(project => {
                        const card = createProjectCard(project);
                        categoryContent.appendChild(card);
                    });

                    categoryPage++;
                    categoryHasMore = data.length === 10;
                    
                    if (categoryHasMore) {
                        const loadingElement = document.createElement('div');
                        loadingElement.className = 'loading';
                        loadingElement.textContent = 'Загрузка еще...';
                        categoryContent.appendChild(loadingElement);
                    }
                } else {
                    if (categoryPage === 0) {
                        categoryContent.innerHTML = '<div class="no-results">Контент недоступен</div>';
                    }
                    categoryHasMore = false;
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        }
    } catch (error) {
        console.error('Error loading category:', error);
        if (categoryPage === 0) {
            categoryContent.innerHTML = '<div class="no-results">Ошибка загрузки данных</div>';
        }
    } finally {
        categoryLoading = false;
    }
}

// Add Infinite Scroll
function addInfiniteScroll() {
    const handleScroll = () => {
        if (categoryLoading || !categoryHasMore) return;

        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        const docHeight = document.documentElement.scrollHeight;

        if (scrollTop + windowHeight >= docHeight - 1000) {
            loadCategoryContent(true);
        }
    };

    window.removeEventListener('scroll', window.categoryScrollHandler);
    window.categoryScrollHandler = handleScroll;
    window.addEventListener('scroll', handleScroll);
}

// Go Back to Search
function goBackToSearch() {
    if (pageHeader) pageHeader.style.display = 'none';
    isInCategoryPage = false;
    
    // Expand search header when going back
    expandSearchHeader();
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('search-tab').classList.add('active');
    const categoryTab = document.getElementById('category-tab');
    if (categoryTab) categoryTab.style.display = 'none';

    window.removeEventListener('scroll', window.categoryScrollHandler);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Load Projects (Search Results)
async function loadProjects(contentType = 'all', append = false) {
    if (loading || (!hasMore && append)) return;
    loading = true;

    const resultsTab = document.getElementById('results-tab');
    let resultsContent = document.getElementById('resultsContent');
    
    if (!resultsContent) {
        resultsContent = document.createElement('div');
        resultsContent.id = 'resultsContent';
        resultsTab.appendChild(resultsContent);
    }

    if (!append) {
        resultsContent.innerHTML = '<div class="loading">Идет поиск...</div>';
        page = 0;
        hasMore = true;
    }

    const query = searchInput?.value?.trim() || '';
    let themeFilter = currentFilter === 'все' ? '' : currentFilter;
    
    if (currentSubcategory) {
        themeFilter = currentSubcategory;
    }

    try {
        let apiCalls = [];
        let types = [];
        
        if (contentType === 'all') {
            types = ['channel', 'bot', 'mini_app'];
        } else {
            types = [contentType];
        }

        for (const type of types) {
            const searchParam = query ? `&smart_search=${encodeURIComponent(query)}` : '';
            const themeParam = themeFilter ? `&theme=${encodeURIComponent(themeFilter)}` : '';
            
            const apiUrl = `${API_URL}/projects/?type=${type}${themeParam}${searchParam}&limit=10&offset=${page*10}`;
            
            apiCalls.push(
                fetch(apiUrl)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    return { type, data: { items: Array.isArray(data) ? data : [] } };
                })
                .catch(error => {
                    console.error(`Error for ${type}:`, error);
                    return { type, data: { items: [] } };
                })
            );
        }

        const results = await Promise.all(apiCalls);
        
        if (!append) {
            resultsContent.innerHTML = '';
        }
        
        let hasResults = false;
        
        for (const { type, data } of results) {
            if (data.items && data.items.length > 0) {
                hasResults = true;
                
                if (contentType === 'all' && types.length > 1) {
                    const typeHeader = document.createElement('div');
                    typeHeader.className = 'results-type-header';
                    typeHeader.innerHTML = getTypeHeaderText(type);
                    resultsContent.appendChild(typeHeader);
                }
                
                data.items.forEach(project => {
                    const card = createProjectCard(project);
                    resultsContent.appendChild(card);
                });
            }
        }
        
        if (!hasResults && page === 0) {
            resultsContent.innerHTML = '<div class="no-results">Ничего не найдено</div>';
            hasMore = false;
        } else {
            hasMore = results.some(result => result.data.items && result.data.items.length === 10);
        }
        
        page++;
        showResultsTab();
        
        if (hasMore && !append) {
            addInfiniteScrollForResults();
        }
        
    } catch (error) {
        console.error('Search error:', error);
        if (page === 0) {
            resultsContent.innerHTML = '<div class="no-results">Ошибка загрузки данных</div>';
        }
    } finally {
        loading = false;
    }
}

// Add Infinite Scroll for Results
function addInfiniteScrollForResults() {
    const handleResultsScroll = () => {
        if (loading || !hasMore) return;

        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        const docHeight = document.documentElement.scrollHeight;

        if (scrollTop + windowHeight >= docHeight - 1000) {
            loadProjects(currentContentType, true);
        }
    };

    window.removeEventListener('scroll', window.resultsScrollHandler);
    window.resultsScrollHandler = handleResultsScroll;
    window.addEventListener('scroll', handleResultsScroll);
}

// Load Recommendations
async function loadRecommendations() {
    const recommendationsContent = document.getElementById('recommendationsContent');
    if (!recommendationsContent) return;

    recommendationsContent.innerHTML = '<div class="loading">Подбираем рекомендации...</div>';

    try {
        const [channelsResp, botsResp, appsResp] = await Promise.all([
            fetch(`${API_URL}/projects/?type=channel&limit=3&offset=0`),
            fetch(`${API_URL}/projects/?type=bot&limit=2&offset=0`),
            fetch(`${API_URL}/projects/?type=mini_app&limit=2&offset=0`)
        ]);

        const [channelsData, botsData, appsData] = await Promise.all([
            channelsResp.ok ? channelsResp.json() : [],
            botsResp.ok ? botsResp.json() : [],
            appsResp.ok ? appsResp.json() : []
        ]);

        recommendationsContent.innerHTML = '';

        if (Array.isArray(channelsData) && channelsData.length) {
            const channelsSection = document.createElement('div');
            channelsSection.innerHTML = '<h4>Популярные каналы</h4>';
            channelsData.forEach(project => {
                const card = createProjectCard(project);
                channelsSection.appendChild(card);
            });
            recommendationsContent.appendChild(channelsSection);
        }

        if (Array.isArray(botsData) && botsData.length) {
            const botsSection = document.createElement('div');
            botsSection.innerHTML = '<h4>Полезные боты</h4>';
            botsData.forEach(project => {
                const card = createProjectCard(project);
                botsSection.appendChild(card);
            });
            recommendationsContent.appendChild(botsSection);
        }

        if (Array.isArray(appsData) && appsData.length) {
            const appsSection = document.createElement('div');
            appsSection.innerHTML = '<h4>Интересные приложения</h4>';
            appsData.forEach(project => {
                const card = createProjectCard(project);
                appsSection.appendChild(card);
            });
            recommendationsContent.appendChild(appsSection);
        }

        if (!channelsData?.length && !botsData?.length && !appsData?.length) {
            recommendationsContent.innerHTML = '<div class="no-results">Рекомендации временно недоступны</div>';
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        recommendationsContent.innerHTML = '<div class="no-results">Ошибка загрузки рекомендаций</div>';
    }
}

// Get Type Header Text
function getTypeHeaderText(type) {
    const headers = {
        'channel': '<h4>Каналы</h4>',
        'bot': '<h4>Боты</h4>',
        'mini_app': '<h4>Мини-приложения</h4>'
    };
    return headers[type] || '';
}

// Show Results Tab
function showResultsTab() {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('results-tab').classList.add('active');
    document.getElementById('results-tab').style.display = 'block';
    
    window.removeEventListener('scroll', window.categoryScrollHandler);
}

// Show Main Tab
function showMainTab() {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('search-tab').classList.add('active');
    document.getElementById('results-tab').style.display = 'none';
    
    window.removeEventListener('scroll', window.resultsScrollHandler);
    loadCategories();
}

// Initialize Tabs
function initializeTabs() {
    const tabs = document.querySelectorAll('.bottom-tab');

    function switchTab(tabName) {
        if (document.getElementById('category-tab').classList.contains('active')) {
            goBackToSearch();
        }

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        tabs.forEach(tab => tab.classList.remove('active'));
        
        const targetTab = document.getElementById(`${tabName}-tab`);
        if (targetTab) {
            targetTab.classList.add('active');
        }
        
        const activeNavTab = document.querySelector(`.bottom-tab[data-tab="${tabName}"]`);
        if (activeNavTab) {
            activeNavTab.classList.add('active');
        }

        if (searchContainer) {
            if (tabName === 'settings') {
                searchHeader.classList.add('hidden');
            } else {
                searchHeader.classList.remove('hidden');
            }
        }

        if (tabName === 'search') {
            showMainTab();
            loadContentSections();
            loadCategories();
            // Expand search header when switching to search tab
            expandSearchHeader();
        } else if (tabName === 'recommendations') {
            loadRecommendations();
        }
    }

    tabs.forEach((tab) => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

// Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// FIX: Search handler - keyboard only closes on Enter
const debouncedSearch = debounce(() => {
    const query = searchInput?.value?.trim() || '';
    
    if (isInCategoryPage) {
        categoryPage = 0;
        categoryHasMore = true;
        loadCategoryContent();
    } else {
        if (query.length > 0 || currentFilter !== 'все' || currentSubcategory) {
            loadProjects(currentContentType);
        } else {
            showMainTab();
        }
    }
}, 500); // Increased debounce time

// Filter Handlers
function handleFilterToggle() {
    if (filterModal) {
        const contentTypeSection = document.querySelector('.filter-section:first-child');
        if (contentTypeSection) {
            if (isInCategoryPage) {
                contentTypeSection.classList.add('hidden');
            } else {
                contentTypeSection.classList.remove('hidden');
            }
        }
        
        filterModal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function handleFilterClose() {
    if (filterModal) {
        filterModal.classList.add('closing');
        
        setTimeout(() => {
            filterModal.classList.remove('show', 'closing');
            document.body.style.overflow = '';
        }, 300);
    }
}

function handleFilterReset() {
    currentFilter = 'все';
    if (!isInCategoryPage) {
        currentContentType = 'all';
    }
    currentSubcategory = null;
    
    page = 0;
    hasMore = true;
    categoryPage = 0;
    categoryHasMore = true;
    
    if (!isInCategoryPage) {
        const contentTypeAll = document.querySelector('input[name="contentType"][value="all"]');
        if (contentTypeAll) contentTypeAll.checked = true;
    }
    
    document.querySelectorAll('.filter-category-item').forEach(item => {
        item.classList.remove('selected');
    });
    const allCategory = document.querySelector('.filter-category-item[data-category="все"]');
    if (allCategory) allCategory.classList.add('selected');
}

function handleFilterApply() {
    const selectedCategory = document.querySelector('.filter-category-item.selected');
    
    if (!isInCategoryPage) {
        const contentTypeInput = document.querySelector('input[name="contentType"]:checked');
        if (contentTypeInput) currentContentType = contentTypeInput.value;
    }
    
    if (selectedCategory) {
        currentFilter = selectedCategory.dataset.category;
        currentSubcategory = null; // Only main categories, no subcategories
    }
    
    page = 0;
    hasMore = true;
    categoryPage = 0;
    categoryHasMore = true;
    
    handleFilterClose();
    
    if (isInCategoryPage) {
        loadCategoryContent();
    } else {
        loadProjects(currentContentType);
    }
}

// Create Filter Categories (without subcategories)
function createFilterCategories() {
    const filterCategories = document.getElementById('filterCategories');
    if (!filterCategories) return;

    filterCategories.innerHTML = '';

    Object.entries(categoriesData).forEach(([key, categoryData]) => {
        const categoryItem = document.createElement('div');
        categoryItem.className = 'filter-category-item';
        categoryItem.dataset.category = key;
        
        if (key === 'все') {
            categoryItem.classList.add('selected');
        }
        
        categoryItem.innerHTML = `<span>${categoryData.name}</span>`;
        
        categoryItem.addEventListener('click', (e) => {
            e.stopPropagation();
            
            document.querySelectorAll('.filter-category-item').forEach(item => {
                item.classList.remove('selected');
            });
            categoryItem.classList.add('selected');
        });
        
        filterCategories.appendChild(categoryItem);
    });
}

// Initialize Filter
function initializeFilter() {
    createFilterCategories();
}

// Settings Click Handler
function handleSettingsClick(settingType) {
    console.log(`Clicked on setting: ${settingType}`);
    
    switch (settingType) {
        case 'add-channel':
            // Open add channel form or redirect to submission page
            if (tg.openTelegramLink) {
                tg.openTelegramLink('https://t.me/tcatalog_bot?start=add_channel');
            }
            break;
        case 'notifications':
            // Handle notifications settings
            break;
        case 'theme':
            // Handle theme settings
            break;
        case 'language':
            // Handle language settings
            break;
        case 'support':
            if (tg.openTelegramLink) {
                tg.openTelegramLink('https://t.me/support_bot');
            }
            break;
        case 'faq':
            // Handle FAQ
            break;
        case 'privacy':
            // Handle privacy policy
            break;
    }
}

// Scroll to Top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
    // Expand search header when scrolling to top
    expandSearchHeader();
}

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    
    initializeTabs();
    initializeFilter();
    
    // Event Handlers
    if (searchInput) {
        // FIX: Only trigger search after typing stops, don't close keyboard on every input
        searchInput.addEventListener('input', debouncedSearch);
        
        // FIX: Close keyboard only on Enter key
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchInput.blur(); // Close keyboard only on Enter
                // Trigger immediate search on Enter
                const query = searchInput.value.trim();
                if (isInCategoryPage) {
                    categoryPage = 0;
                    categoryHasMore = true;
                    loadCategoryContent();
                } else {
                    if (query.length > 0 || currentFilter !== 'все' || currentSubcategory) {
                        loadProjects(currentContentType);
                    } else {
                        showMainTab();
                    }
                }
            }
        });
    }
    
    // Search Toggle Handler
    if (searchToggle) {
        searchToggle.addEventListener('click', expandSearchHeader);
    }
    
    if (filterBtn) {
        filterBtn.addEventListener('click', handleFilterToggle);
    }
    
    if (filterModalClose) {
        filterModalClose.addEventListener('click', handleFilterClose);
    }
    
    if (filterResetBtn) {
        filterResetBtn.addEventListener('click', handleFilterReset);
    }
    
    if (filterApplyBtn) {
        filterApplyBtn.addEventListener('click', handleFilterApply);
    }
    
    if (toTopBtn) {
        toTopBtn.addEventListener('click', scrollToTop);
    }
    
    if (backButton) {
        backButton.addEventListener('click', goBackToSearch);
    }

    // Section Header Handlers
    document.querySelectorAll('.section-header').forEach(header => {
        header.addEventListener('click', () => {
            const type = header.dataset.type;
            if (type) {
                openCategoryPage(type);
            }
        });
    });
    
    // Scroll Handler
    window.addEventListener('scroll', handleScroll);
    
    // Filter Modal Backdrop Click
    if (filterModal) {
        filterModal.addEventListener('click', (e) => {
            if (e.target === filterModal) {
                handleFilterClose();
            }
        });
        
        const modalContent = document.querySelector('.filter-modal-content');
        if (modalContent) {
            modalContent.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    }
    
    // Load initial content
    loadContentSections();
    loadCategories();
    
    // Initialize Telegram WebApp
    tg.ready();
});