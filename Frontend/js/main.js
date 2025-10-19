const tg = window.Telegram.WebApp;
tg.expand();

// Инициализация темы и пользователя
// initializeTelegramTheme();
initializeUserProfile();

const API_URL = 
'https://tcatalogbot.ru/api';
// 'http://localhost:8000';
window.API_URL = API_URL; 

const urlParams = new URLSearchParams(window.location.search);
const debugUserParam = urlParams.get('debug_user');
const parsedDebugUser = debugUserParam ? parseInt(debugUserParam, 10) : null;
const DEBUG_USER_ID = Number.isFinite(parsedDebugUser) ? parsedDebugUser : null;

window.DEBUG_USER_ID = DEBUG_USER_ID;

let searchTimeout;
let currentFilter = 'все';
let currentContentType = 'all';
let currentSortBy = 'subscribers';
let currentSubcategory = null;
let page = 0;
let hasMore = true;
let loading = false;
let currentCategoryType = null;
let categoryPage = 0;
let categoryHasMore = true;
let categoryLoading = false;
let isInCategoryPage = false;
let survey = null; // Инициализация опросника

const toTopBtn = document.getElementById('toTopBtn');
const searchInput = document.getElementById('searchInput');
const searchContainer = document.getElementById('searchContainer');
const filterBtn = document.getElementById('filterBtn');
const filterModal = document.getElementById('filterModal');
const filterModalClose = document.getElementById('filterModalClose');
const filterResetBtn = document.getElementById('filterResetBtn');
const filterApplyBtn = document.getElementById('filterApplyBtn');
const pageHeader = document.getElementById('pageHeader');
const pageTitle = document.getElementById('pageTitle');
const backButton = document.getElementById('backButton');

// Данные категорий и подкатегорий
const categoriesData = {
    'все': {
        name: 'Все категории',
        subcategories: []
    },
    'новости': {
        name: 'Новости',
        subcategories: ['Политика', 'Экономика', 'Мировые новости', 'Происшествия']
    },
    'спорт': {
        name: 'Спорт',
        subcategories: ['Футбол', 'Хоккей', 'Теннис', 'Баскетбол', 'Единоборства']
    },
    'технологии': {
        name: 'Технологии',
        subcategories: ['IT и программирование', 'Наука', 'Гаджеты', 'Искусственный интеллект']
    },
    'развлечения': {
        name: 'Развлечения',
        subcategories: ['Кино и сериалы', 'Музыка', 'Игры', 'Юмор']
    },
    'образование': {
        name: 'Образование',
        subcategories: ['Изучение языков', 'Онлайн курсы', 'Книги', 'Наука']
    },
    'бизнес': {
        name: 'Бизнес',
        subcategories: ['Стартапы', 'Инвестиции', 'Маркетинг', 'Криптовалюты']
    }
};

// Инициализация темы Telegram
function initializeTelegramTheme() {
    const themeParams = tg.themeParams;
    
    if (themeParams) {
        const root = document.documentElement;
        
        // Устанавливаем CSS переменные на основе темы Telegram
        if (themeParams.bg_color) root.style.setProperty('--tg-theme-bg-color', themeParams.bg_color);
        if (themeParams.text_color) root.style.setProperty('--tg-theme-text-color', themeParams.text_color);
        if (themeParams.hint_color) root.style.setProperty('--tg-theme-hint-color', themeParams.hint_color);
        if (themeParams.button_color) root.style.setProperty('--tg-theme-button-color', themeParams.button_color);
        if (themeParams.button_text_color) root.style.setProperty('--tg-theme-button-text-color', themeParams.button_text_color);
        if (themeParams.secondary_bg_color) root.style.setProperty('--tg-theme-secondary-bg-color', themeParams.secondary_bg_color);
        if (themeParams.header_bg_color) root.style.setProperty('--tg-theme-header-bg-color', themeParams.header_bg_color);
        if (themeParams.accent_text_color) root.style.setProperty('--tg-theme-accent-text-color', themeParams.accent_text_color);
        if (themeParams.section_bg_color) root.style.setProperty('--tg-theme-section-bg-color', themeParams.section_bg_color);
        if (themeParams.link_color) root.style.setProperty('--tg-theme-link-color', themeParams.link_color);
        if (themeParams.destructive_text_color) root.style.setProperty('--tg-theme-destructive-text-color', themeParams.destructive_text_color);
        
        // Устанавливаем цвет заголовка
        tg.setHeaderColor(themeParams.header_bg_color || themeParams.secondary_bg_color || 'secondary_bg_color');
    }
    
    // Слушаем изменения темы
    tg.onEvent('themeChanged', function() {
        initializeTelegramTheme();
    });
}

// Инициализация профиля пользователя
function initializeUserProfile() {
    const user = tg?.initDataUnsafe?.user;
    
    if (user) {
        const userNameElement = document.getElementById('userName');
        const userAvatarElement = document.getElementById('userAvatar');
        const userInitialsElement = document.getElementById('userInitials');
        
        // Устанавливаем имя пользователя
        const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ');
        if (userNameElement) userNameElement.textContent = fullName || 'Пользователь';
        
        // Устанавливаем аватар или инициалы
        if (user.photo_url && userAvatarElement) {
            userAvatarElement.src = user.photo_url;
        } else if (userInitialsElement) {
            const firstName = user.first_name || '';
            const lastName = user.last_name || '';
            
            // Берем первую букву имени и первую букву фамилии
            const firstInitial = firstName.charAt(0).toUpperCase();
            const secondInitial = lastName.charAt(0).toUpperCase();
            
            const initials = firstInitial + secondInitial || (user.username?.[0]?.toUpperCase() || 'U');
            userInitialsElement.textContent = initials;
        }
    }
}

// Функция генерации случайного офсета для каждого типа контента
function getRandomOffset() {
    return Math.floor(Math.random() * 20); // Случайный офсет от 0 до 19
}

// Загрузка блоков контента по 5 штук каждый
async function loadContentSections() {
    const types = [
        { type: 'channel', containerId: 'channelsContent' },
        { type: 'bot', containerId: 'botsContent' },
        { type: 'mini_app', containerId: 'appsContent' }
    ];

    for (const { type, containerId } of types) {
        try {
            const offset = getRandomOffset();
            const response = await fetch(`${API_URL}/projects/?type=${type}&limit=10&offset=${offset}`);
            
            if (response.ok) {
                const data = await response.json();
                const container = document.getElementById(containerId);
                
                if (container) {
                    container.innerHTML = '';
                    
                    if (Array.isArray(data) && data.length > 0) {
                        data.forEach(project => {
                            const card = createProjectCard(project);
                            container.appendChild(card);
                        });
                    } else {
                        container.innerHTML = '<div class="no-results">Контент недоступен</div>';
                    }
                }
            }
        } catch (error) {
            console.error(`Ошибка загрузки ${type}:`, error);
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = '<div class="no-results">Ошибка загрузки</div>';
            }
        }
    }
}

// Открытие страницы категории
async function openCategoryPage(type) {
    const typeNames = {
        'channel': 'Каналы',
        'bot': 'Боты', 
        'mini_app': 'Мини-приложения'
    };

    currentCategoryType = type;
    categoryPage = 0;
    categoryHasMore = true;
    categoryLoading = false;
    isInCategoryPage = true;

    // Показываем заголовок с кнопкой назад
    pageHeader.style.display = 'flex';
    pageTitle.textContent = typeNames[type];

    // Скрываем основные вкладки и показываем страницу категории
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const categoryTab = document.getElementById('category-tab');
    categoryTab.classList.add('active');
    categoryTab.style.display = 'block';

    // Создаем контейнер для контента
    const categoryContent = document.getElementById('categoryContent');
    categoryContent.innerHTML = '<div class="scroll-loading">Загрузка...</div>';

    // Загружаем первую порцию данных
    await loadCategoryContent();

    // Добавляем обработчик бесконечного скролла
    addInfiniteScroll();
}

// ФИКС: Обновляем существующую функцию loadCategoryContent для поддержки тематических категорий
async function loadCategoryContent(append = false) {
    // Если это тематическая категория, используем специальную функцию
    if (currentCategoryType === 'theme') {
        return await loadThemeCategoryContent(append);
    }

    // Оригинальная логика для типовых категорий (каналы, боты, мини-приложения)
    if (categoryLoading || (!categoryHasMore && append)) return;
    
    categoryLoading = true;
    const categoryContent = document.getElementById('categoryContent');

    if (!append) {
        categoryContent.innerHTML = '<div class="scroll-loading">Загрузка...</div>';
    }

    try {
        const query = searchInput?.value?.trim() || '';
        let themeFilter = currentFilter === 'все' ? '' : currentFilter;
        
        if (currentSubcategory) {
            themeFilter = currentSubcategory;
        }

        const searchParam = query ? `&smart_search=${encodeURIComponent(query)}` : '';
        const themeParam = themeFilter ? `&theme=${encodeURIComponent(themeFilter)}` : '';
        
        const apiUrl = `${API_URL}/projects/?type=${currentCategoryType}${themeParam}${searchParam}&limit=10&offset=${categoryPage * 10}`;
        
        console.log('Category API URL:', apiUrl);
        
        const response = await fetch(apiUrl);
        
        if (response.ok) {
            const data = await response.json();
            
            if (!append) {
                categoryContent.innerHTML = '';
            } else {
                const loadingElement = categoryContent.querySelector('.scroll-loading');
                if (loadingElement) {
                    loadingElement.remove();
                }
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
                    loadingElement.className = 'scroll-loading';
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
    } catch (error) {
        console.error('Ошибка загрузки категории:', error);
        if (categoryPage === 0) {
            categoryContent.innerHTML = '<div class="no-results">Ошибка загрузки данных</div>';
        }
    } finally {
        categoryLoading = false;
    }
}

// Добавление бесконечного скролла
function addInfiniteScroll() {
    const handleScroll = () => {
        if (categoryLoading || !categoryHasMore) return;

        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        const docHeight = document.documentElement.scrollHeight;

        // Загружаем больше контента когда пользователь почти доходит до конца
        if (scrollTop + windowHeight >= docHeight - 1000) {
            loadCategoryContent(true);
        }
    };

    // Удаляем предыдущий обработчик если есть
    window.removeEventListener('scroll', window.categoryScrollHandler);
    
    // Добавляем новый обработчик
    window.categoryScrollHandler = handleScroll;
    window.addEventListener('scroll', handleScroll);
}

// Возврат на главную страницу поиска
function goBackToSearch() {
    // Скрываем заголовок с кнопкой назад
    pageHeader.style.display = 'none';
    isInCategoryPage = false;
    
    // Показываем вкладку поиска
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('search-tab').classList.add('active');
    document.getElementById('category-tab').style.display = 'none';

    // Убираем обработчик бесконечного скролла
    window.removeEventListener('scroll', window.categoryScrollHandler);
    
    // Прокручиваем наверх
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ФИКС: Основная функция загрузки проектов с правильным бесконечным скроллом
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
    
    // Если выбрана подкатегория, используем её вместо основной категории
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
                
                // Добавляем заголовок для типа контента (только если показываем все типы)
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
            // Проверяем есть ли еще данные
            hasMore = results.some(result => result.data.items && result.data.items.length === 10);
        }
        
        page++;
        
        // Показываем вкладку результатов
        showResultsTab();
        
        // ФИКС: Добавляем бесконечный скролл для результатов поиска
        if (hasMore && !append) {
            addInfiniteScrollForResults();
        }
        
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        if (page === 0) {
            resultsContent.innerHTML = '<div class="no-results">Ошибка загрузки данных. Попробуйте позже.</div>';
        }
    } finally {
        loading = false;
    }
}

// ФИКС: Добавляем бесконечный скролл для результатов поиска
function addInfiniteScrollForResults() {
    const handleResultsScroll = () => {
        if (loading || !hasMore) return;

        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        const docHeight = document.documentElement.scrollHeight;

        // Загружаем больше контента когда пользователь почти доходит до конца
        if (scrollTop + windowHeight >= docHeight - 1000) {
            loadProjects(currentContentType, true);
        }
    };

    // Удаляем предыдущий обработчик если есть
    window.removeEventListener('scroll', window.resultsScrollHandler);
    
    // Добавляем новый обработчик
    window.resultsScrollHandler = handleResultsScroll;
    window.addEventListener('scroll', handleResultsScroll);
}

// Загрузка рекомендаций
async function loadRecommendations() {
    const recommendationsContent = document.getElementById('recommendationsContent');
    if (!recommendationsContent) return;

    recommendationsContent.innerHTML = '<div class="loading">Подбираем рекомендации...</div>';

    try {
        // Загружаем смешанные рекомендации из разных категорий
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

        // Создаем секции рекомендаций
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
        console.error('Ошибка загрузки рекомендаций:', error);
        recommendationsContent.innerHTML = '<div class="no-results">Ошибка загрузки рекомендаций</div>';
    }
}

// Загрузка категорий
// ФИКС: Загрузка категорий с переходом на отдельные страницы
function loadCategories() {
    const categoriesGrid = document.getElementById('categoriesGrid');
    if (!categoriesGrid) return;

    const categories = [
        { icon: '📰', title: 'Новости', value: 'новости' },
        { icon: '⚽', title: 'Спорт', value: 'спорт' },
        { icon: '💻', title: 'Технологии', value: 'технологии' },
        { icon: '🎭', title: 'Развлечения', value: 'развлечения' },
        { icon: '📚', title: 'Образование', value: 'образование' },
        { icon: '💼', title: 'Бизнес', value: 'бизнес' }
    ];

    categoriesGrid.innerHTML = '';
    categories.forEach(category => {
        const categoryItem = document.createElement('div');
        categoryItem.className = 'category-item';
        categoryItem.innerHTML = `
            <div class="category-item-icon">${category.icon}</div>
            <div class="category-item-title">${category.title}</div>
        `;
        
        // ФИКС: Добавляем обработчик для открытия страницы категории
        categoryItem.addEventListener('click', () => {
            openThemeCategoryPage(category.value, category.title);
        });
        
        categoriesGrid.appendChild(categoryItem);
    });
}

// ФИКС: Новая функция для открытия страницы тематической категории
async function openThemeCategoryPage(categoryValue, categoryTitle) {
    currentFilter = categoryValue;
    currentSubcategory = null;
    currentCategoryType = 'theme'; // Специальный тип для тематических категорий
    categoryPage = 0;
    categoryHasMore = true;
    categoryLoading = false;
    isInCategoryPage = true;

    // Показываем заголовок с кнопкой назад
    pageHeader.style.display = 'flex';
    pageTitle.textContent = categoryTitle;

    // Скрываем основные вкладки и показываем страницу категории
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const categoryTab = document.getElementById('category-tab');
    categoryTab.classList.add('active');
    categoryTab.style.display = 'block';

    // Создаем контейнер для контента
    const categoryContent = document.getElementById('categoryContent');
    categoryContent.innerHTML = '<div class="scroll-loading">Загрузка...</div>';

    // Загружаем первую порцию данных
    await loadThemeCategoryContent();

    // Добавляем обработчик бесконечного скролла
    addInfiniteScroll();
}

// ФИКС: Загрузка контента тематической категории
async function loadThemeCategoryContent(append = false) {
    if (categoryLoading || (!categoryHasMore && append)) return;
    
    categoryLoading = true;
    const categoryContent = document.getElementById('categoryContent');

    if (!append) {
        categoryContent.innerHTML = '<div class="scroll-loading">Загрузка...</div>';
    }

    try {
        const query = searchInput?.value?.trim() || '';
        let themeFilter = currentFilter === 'все' ? '' : currentFilter;
        
        // Если выбрана подкатегория, используем её вместо основной категории
        if (currentSubcategory) {
            themeFilter = currentSubcategory;
        }

        // Загружаем смешанный контент из всех типов с данной тематикой
        const types = ['channel', 'bot', 'mini_app'];
        let allResults = [];

        // Собираем данные из всех типов контента
        for (const type of types) {
            try {
                const searchParam = query ? `&smart_search=${encodeURIComponent(query)}` : '';
                const themeParam = themeFilter ? `&theme=${encodeURIComponent(themeFilter)}` : '';
                
                const apiUrl = `${API_URL}/projects/?type=${type}${themeParam}${searchParam}&limit=4&offset=${Math.floor(categoryPage * 4 / 3)}`;
                
                const response = await fetch(apiUrl);
                
                if (response.ok) {
                    const data = await response.json();
                    if (Array.isArray(data) && data.length > 0) {
                        allResults.push(...data.slice(0, 3)); // Берем не более 3 элементов каждого типа
                    }
                }
            } catch (error) {
                console.error(`Ошибка загрузки ${type}:`, error);
            }
        }

        // Перемешиваем результаты для разнообразия
        allResults.sort(() => Math.random() - 0.5);

        if (!append) {
            categoryContent.innerHTML = '';
        } else {
            // Убираем индикатор загрузки
            const loadingElement = categoryContent.querySelector('.scroll-loading');
            if (loadingElement) {
                loadingElement.remove();
            }
        }

        if (allResults.length > 0) {
            // Берем только нужное количество элементов для данной страницы
            const itemsToShow = allResults.slice(0, 10);
            
            itemsToShow.forEach(project => {
                const card = createProjectCard(project);
                categoryContent.appendChild(card);
            });

            categoryPage++;
            categoryHasMore = allResults.length >= 10;
            
            if (categoryHasMore) {
                const loadingElement = document.createElement('div');
                loadingElement.className = 'scroll-loading';
                loadingElement.textContent = 'Загрузка еще...';
                categoryContent.appendChild(loadingElement);
            }
        } else {
            if (categoryPage === 0) {
                categoryContent.innerHTML = '<div class="no-results">Контент по данной тематике недоступен</div>';
            }
            categoryHasMore = false;
        }
    } catch (error) {
        console.error('Ошибка загрузки тематической категории:', error);
        if (categoryPage === 0) {
            categoryContent.innerHTML = '<div class="no-results">Ошибка загрузки данных</div>';
        }
    } finally {
        categoryLoading = false;
    }
}

// ФИКС: Создание карточки проекта без подписчиков для ботов
function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'card';
    
    if (project.is_premium) {
        card.classList.add('premium-card');
    }

    // Определение URL для иконки
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
    
    // ФИКС: Поддерживаем разные поля для количества подписчиков и убираем для ботов
    const subscribersCount = project.subscribers || project.subscribers_count || project.likes || 0;
    const projectType = project.type || (project.url && project.url.includes('t.me/') && !project.url.includes('_bot') ? 'channel' : 'bot');
    
    // ФИКС: Показываем подписчиков только для каналов, не для ботов
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
                <span class="subscribers-badge">👥 ${formatNumber(subscribersCount)}</span>
            </div>
            ` : ''}
        </div>
    `;

    // Добавляем обработчик клика для аналитики
    const clickableArea = card.querySelector('.channel-clickable-area');
    clickableArea.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Отправляем данные обратно в Telegram (если нужно)
        if (tg.sendData) {
            tg.sendData(JSON.stringify({
                action: 'open_project',
                project_id: project.id,
                project_title: projectName,
                project_url: projectUrl
            }));
        }
        
        // Открываем ссылку
        window.open(projectUrl, '_blank');
    });

    return card;
}

// Получение заголовка для типа контента
function getTypeHeaderText(type) {
    const headers = {
        'channel': '<h4>📺 Каналы</h4>',
        'bot': '<h4>🤖 Боты</h4>',
        'mini_app': '<h4>📱 Мини-приложения</h4>'
    };
    return headers[type] || '';
}

// Форматирование чисел
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Показать вкладку результатов
function showResultsTab() {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('results-tab').classList.add('active');
    document.getElementById('results-tab').style.display = 'block';
    
    // Убираем обработчик скролла категорий
    window.removeEventListener('scroll', window.categoryScrollHandler);
}

// Показать основную вкладку
function showMainTab() {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('search-tab').classList.add('active');
    document.getElementById('results-tab').style.display = 'none';
    
    // Убираем обработчик скролла результатов
    window.removeEventListener('scroll', window.resultsScrollHandler);
    
    // ФИКС: Перезагружаем категории при возврате на главную
    // закомментил категории и убрал loadCategories();
    // loadCategories();
}

// Инициализация вкладок
function initializeTabs() {
    const tabs = document.querySelectorAll('.bottom-tab');

function switchTab(tabName) {
    if (document.getElementById('category-tab').classList.contains('active')) {
        goBackToSearch();
    }
    
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    tabs.forEach(tab => tab.classList.remove('active'));
    
    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    const activeNavTab = document.querySelector(`.bottom-tab[data-tab="${tabName}"]`);
    if (activeNavTab) {
        activeNavTab.classList.add('active');
    }
    
    // Update active tab indicator position
    const bottomTabs = document.querySelector('.bottom-tabs');
    const tabsArray = ['search', 'recommendations', 'settings'];
    const activeIndex = tabsArray.indexOf(tabName);
    if (bottomTabs && activeIndex !== -1) {
        bottomTabs.setAttribute('data-active-tab', activeIndex);
    }
    
    if (searchContainer) {
        if (tabName === 'settings') {
            searchContainer.classList.add('hidden');
        } else {
            searchContainer.classList.remove('hidden');
        }
    }
    
    if (tabName === 'search') {
        showMainTab();
        loadContentSections();
        // loadCategories(); // Закомментировано - категории убраны
    } else if (tabName === 'recommendations') {
        loadRecommendations();
    }
    // settings tab doesn't need to load anything
}

// Функция для обновления позиции и размера индикатора
function updateTabIndicator() {
    const bottomTabs = document.querySelector('.bottom-tabs');
    const activeTab = document.querySelector('.bottom-tab.active');
    
    if (!bottomTabs || !activeTab) return;
    
    // Получаем размеры и позицию активной вкладки
    const tabsRect = bottomTabs.getBoundingClientRect();
    const activeRect = activeTab.getBoundingClientRect();
    
    // Вычисляем относительную позицию
    const leftOffset = activeRect.left - tabsRect.left;
    
    // Устанавливаем CSS переменные для индикатора
    bottomTabs.style.setProperty('--indicator-left', `${leftOffset}px`);
    bottomTabs.style.setProperty('--indicator-width', `${activeRect.width}px`);
}

    // Инициализация обработчиков вкладок
    tabs.forEach((tab) => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

// Поиск с задержкой
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

// ФИКС: Обработка поиска с закрытием клавиатуры
const debouncedSearch = debounce(() => {
    const query = searchInput?.value?.trim() || '';
    
    // ФИКС: Закрываем клавиатуру после ввода
    if (searchInput) {
        searchInput.blur();
    }
    
    if (isInCategoryPage) {
        // Если мы на странице категории, перезагружаем её с учетом поиска
        categoryPage = 0;
        categoryHasMore = true;
        loadCategoryContent();
    } else {
        // Иначе обрабатываем как обычный поиск
        if (query.length > 0 || currentFilter !== 'все' || currentSubcategory) {
            loadProjects(currentContentType);
        } else {
            showMainTab();
        }
    }
}, 300);

// Обработка фильтра
function handleFilterToggle() {
    if (filterModal) {
        // Скрываем/показываем секцию выбора типа контента в зависимости от того, где мы находимся
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
        }, 400);
    }
}

// ФИКС: Сброс фильтров с полной очисткой кэша
function handleFilterReset() {
    // Сбрасываем все фильтры
    currentFilter = 'все';
    if (!isInCategoryPage) {
        currentContentType = 'all';
    }
    currentSortBy = 'subscribers';
    currentSubcategory = null;
    
    // ФИКС: Полностью сбрасываем пагинацию
    page = 0;
    hasMore = true;
    categoryPage = 0;
    categoryHasMore = true;
    
    // Сбрасываем UI
    if (!isInCategoryPage) {
        const contentTypeAll = document.querySelector('input[name="contentType"][value="all"]');
        if (contentTypeAll) contentTypeAll.checked = true;
    }
    const sortBySubscribers = document.querySelector('input[name="sortBy"][value="subscribers"]');
    if (sortBySubscribers) sortBySubscribers.checked = true;
    
    // Сбрасываем категории
    document.querySelectorAll('.filter-category-item').forEach(item => {
        item.classList.remove('selected', 'expanded');
    });
    document.querySelectorAll('.filter-subcategories').forEach(sub => {
        sub.classList.remove('show');
    });
    const allCategory = document.querySelector('.filter-category-item[data-category="все"]');
    if (allCategory) allCategory.classList.add('selected');
}

function handleFilterApply() {
    // Получаем выбранные значения
    const sortByInput = document.querySelector('input[name="sortBy"]:checked');
    const selectedCategory = document.querySelector('.filter-category-item.selected:not(.subcategory)');
    const selectedSubcategory = document.querySelector('.filter-subcategory-item.selected');
    
    if (!isInCategoryPage) {
        const contentTypeInput = document.querySelector('input[name="contentType"]:checked');
        if (contentTypeInput) currentContentType = contentTypeInput.value;
    }
    
    if (sortByInput) currentSortBy = sortByInput.value;
    
    if (selectedSubcategory) {
        currentSubcategory = selectedSubcategory.dataset.subcategory;
        currentFilter = selectedSubcategory.dataset.parentCategory;
    } else if (selectedCategory) {
        currentFilter = selectedCategory.dataset.category;
        currentSubcategory = null;
    }
    
    // ФИКС: Полностью сбрасываем пагинацию при применении фильтров
    page = 0;
    hasMore = true;
    categoryPage = 0;
    categoryHasMore = true;
    
    // Закрываем модал
    handleFilterClose();
    
    // Применяем фильтры
    if (isInCategoryPage) {
        loadCategoryContent();
    } else {
        loadProjects(currentContentType);
    }
}

// Создание категорий в фильтре
function createFilterCategories() {
    const filterCategories = document.getElementById('filterCategories');
    if (!filterCategories) return;

    filterCategories.innerHTML = '';

    Object.entries(categoriesData).forEach(([key, categoryData]) => {
        // Основная категория
        const categoryItem = document.createElement('div');
        categoryItem.className = 'filter-category-item';
        categoryItem.dataset.category = key;
        
        if (key === 'все') {
            categoryItem.classList.add('selected');
        }
        
        categoryItem.innerHTML = `
            <span>${categoryData.name}</span>
            ${categoryData.subcategories.length > 0 ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>' : ''}
        `;
        
        categoryItem.addEventListener('click', (e) => {
            e.stopPropagation();
            
            // Если у категории есть подкатегории
            if (categoryData.subcategories.length > 0) {
                const isExpanded = categoryItem.classList.contains('expanded');
                
                // Закрываем все другие категории
                document.querySelectorAll('.filter-category-item').forEach(item => {
                    item.classList.remove('expanded');
                });
                document.querySelectorAll('.filter-subcategories').forEach(sub => {
                    sub.classList.remove('show');
                });
                
                if (!isExpanded) {
                    categoryItem.classList.add('expanded');
                    const subcategoriesDiv = categoryItem.nextElementSibling;
                    if (subcategoriesDiv) {
                        subcategoriesDiv.classList.add('show');
                    }
                }
            } else {
                // Выбираем категорию без подкатегорий
                document.querySelectorAll('.filter-category-item, .filter-subcategory-item').forEach(item => {
                    item.classList.remove('selected');
                });
                categoryItem.classList.add('selected');
            }
        });
        
        filterCategories.appendChild(categoryItem);
        
        // Подкатегории
        if (categoryData.subcategories.length > 0) {
            const subcategoriesDiv = document.createElement('div');
            subcategoriesDiv.className = 'filter-subcategories';
            
            categoryData.subcategories.forEach(subcategory => {
                const subcategoryItem = document.createElement('div');
                subcategoryItem.className = 'filter-subcategory-item';
                subcategoryItem.dataset.subcategory = subcategory;
                subcategoryItem.dataset.parentCategory = key;
                subcategoryItem.innerHTML = `<span>${subcategory}</span>`;
                
                subcategoryItem.addEventListener('click', (e) => {
                    e.stopPropagation();
                    
                    // Снимаем выделение со всех элементов
                    document.querySelectorAll('.filter-category-item, .filter-subcategory-item').forEach(item => {
                        item.classList.remove('selected');
                    });
                    
                    // Выделяем выбранную подкатегорию
                    subcategoryItem.classList.add('selected');
                });
                
                subcategoriesDiv.appendChild(subcategoryItem);
            });
            
            filterCategories.appendChild(subcategoriesDiv);
        }
    });
}

// Инициализация фильтра
function initializeFilter() {
    createFilterCategories();
}

// Обработка клика на настройки
function handleSettingsClick(settingType) {
    console.log(`Clicked on setting: ${settingType}`);
    
    switch (settingType) {
        case 'notifications':
            break;
        case 'theme':
            break;
        case 'language':
            break;
        case 'support':
            if (tg.openTelegramLink) {
                tg.openTelegramLink('https://t.me/support_bot');
            }
            break;
        case 'faq':
            break;
        case 'privacy':
            break;
    }
}

// Скролл вверх
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Обработка скролла для кнопки "Наверх"
function handleScroll() {
    if (toTopBtn) {
        if (window.pageYOffset > 300) {
            toTopBtn.style.display = 'block';
        } else {
            toTopBtn.style.display = 'none';
        }
    }
}

// Проверка статуса опроса и показ опросника для новых пользователей
async function checkSurveyStatus() {
    const userId = tg?.initDataUnsafe?.user?.id ?? window.DEBUG_USER_ID;
    
    if (!userId) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/users/${userId}/survey_status`);
        
        if (response.ok) {
            const data = await response.json();
            
            // Показываем опросник если он еще не был пройден
            if (!data.survey_completed && survey) {
                survey.show();
            }
        }
    } catch (error) {
        console.error('Error checking survey status:', error);
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');

      // Initialize active tab indicator on first load
    const bottomTabs = document.querySelector('.bottom-tabs');
    if (bottomTabs) {
        bottomTabs.setAttribute('data-active-tab', '0'); // Start with search tab
    }

    // Инициализируем опросник
    if (window.Survey) {
        try {
            survey = new window.Survey();
        } catch (error) {
            console.error('Error creating Survey object:', error);
        }
    }
    
    initializeTabs();
    initializeFilter();
    
    // Обработчики событий
    if (searchInput) {
    // УДАЛИТЕ ИЛИ ЗАКОММЕНТИРУЙТЕ ЭТИ СТРОКИ:
    // searchInput.addEventListener('input', debouncedSearch);
    
    // ЗАМЕНИТЕ НА:
    // Поиск только при нажатии Enter
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const query = searchInput?.value?.trim();
            
            // Скрываем клавиатуру
            searchInput.blur();
            
            // Выполняем поиск
            if (isInCategoryPage) {
                categoryPage = 0;
                categoryHasMore = true;
                loadCategoryContent();
            } else {
                if (query.length > 0 || currentFilter || currentSubcategory) {
                    loadProjects(currentContentType);
                } else {
                    showMainTab();
                }
            }
        }
    });
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

    // Обработчики кликов по заголовкам секций
    document.querySelectorAll('.section-header').forEach(header => {
        header.addEventListener('click', () => {
            const type = header.dataset.type;
            if (type) {
                openCategoryPage(type);
            }
        });
    });
    
    // Обработка скролла
    window.addEventListener('scroll', handleScroll);
    
    // Плавное закрытие модала при клике на задний фон
    if (filterModal) {
        filterModal.addEventListener('click', (e) => {
            if (e.target === filterModal) {
                handleFilterClose();
            }
        });
        
        // Предотвращаем закрытие при клике на контент модала
        const modalContent = document.querySelector('.filter-modal-content');
        if (modalContent) {
            modalContent.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    }
    
    // Загружаем контент первой вкладки
    loadContentSections();
    // чтобы не отображались категории
    // loadCategories();
    
    // Готовность приложения
    tg.ready();
    
    // Проверяем статус опроса после загрузки приложения
    checkSurveyStatus();
});
