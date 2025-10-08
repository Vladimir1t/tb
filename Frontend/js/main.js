const tg = window.Telegram.WebApp;
tg.expand();

// Инициализация темы и пользователя
initializeTelegramTheme();
initializeUserProfile();

const API_URL = 'http://localhost:8000';
let searchTimeout;
let currentFilter = 'все';
let currentContentType = 'all';
let currentSortBy = 'subscribers';
let currentSubcategory = null;
let page = 0;
let hasMore = true;
let loading = false;

const toTopBtn = document.getElementById('toTopBtn');
const searchInput = document.getElementById('searchInput');
const searchContainer = document.getElementById('searchContainer');
const filterBtn = document.getElementById('filterBtn');
const filterModal = document.getElementById('filterModal');
const filterModalClose = document.getElementById('filterModalClose');
const filterResetBtn = document.getElementById('filterResetBtn');
const filterApplyBtn = document.getElementById('filterApplyBtn');

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
    const user = tg.initDataUnsafe?.user;
    
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

// Основная функция загрузки проектов с поиском и фильтром
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

    const query = searchInput.value.trim();
    let themeFilter = currentFilter === 'все' ? '' : currentFilter;
    
    // Если выбрана подкатегория, используем её вместо основной категории
    if (currentSubcategory) {
        themeFilter = currentSubcategory;
    }

    console.log("Текущий фильтр (currentFilter):", currentFilter);
    console.log("Подкатегория (currentSubcategory):", currentSubcategory);
    console.log("Тип контента (contentType):", contentType);
    console.log("Поисковый запрос (query):", query);
    console.log("Фильтр по теме (themeFilter):", themeFilter);

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
            const sortParam = `&sort_by=${currentSortBy}`;
            
            apiCalls.push(
                fetch(`${API_URL}/projects/?type=${type}&theme=${encodeURIComponent(themeFilter)}${searchParam}${sortParam}&limit=10&offset=${page*10}`)
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    return response.json();
                })
                .then(data => ({ type, data }))
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
        
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        if (page === 0) {
            resultsContent.innerHTML = '<div class="no-results">Ошибка загрузки данных</div>';
        }
    } finally {
        loading = false;
    }
}

// Загрузка популярного контента для главной страницы
async function loadFeaturedContent() {
    const featuredContent = document.getElementById('featuredContent');
    if (!featuredContent) return;

    featuredContent.innerHTML = '<div class="loading">Загрузка популярного контента...</div>';

    try {
        // Загружаем по несколько элементов каждого типа
        const [channelsResp, botsResp, appsResp] = await Promise.all([
            fetch(`${API_URL}/projects/?type=channel&sort_by=subscribers&limit=3&offset=0`),
            fetch(`${API_URL}/projects/?type=bot&sort_by=subscribers&limit=2&offset=0`),
            fetch(`${API_URL}/projects/?type=mini_app&sort_by=subscribers&limit=2&offset=0`)
        ]);

        const [channelsData, botsData, appsData] = await Promise.all([
            channelsResp.json(),
            botsResp.json(),
            appsResp.json()
        ]);

        featuredContent.innerHTML = '';

        // Объединяем все результаты
        const allItems = [
            ...(channelsData.items || []),
            ...(botsData.items || []),
            ...(appsData.items || [])
        ];

        if (allItems.length) {
            allItems.forEach(project => {
                const card = createProjectCard(project);
                featuredContent.appendChild(card);
            });
        } else {
            featuredContent.innerHTML = '<div class="no-results">Контент временно недоступен</div>';
        }
    } catch (error) {
        console.error('Ошибка загрузки популярного контента:', error);
        featuredContent.innerHTML = '<div class="no-results">Ошибка загрузки данных</div>';
    }
}

// Загрузка категорий
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
        
        categoryItem.addEventListener('click', () => {
            currentFilter = category.value;
            currentSubcategory = null; // Сбрасываем подкатегорию при выборе основной категории
            loadProjects(currentContentType);
        });
        
        categoriesGrid.appendChild(categoryItem);
    });
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
            channelsResp.json(),
            botsResp.json(),
            appsResp.json()
        ]);

        recommendationsContent.innerHTML = '';

        // Создаем секции рекомендаций
        if (channelsData.items?.length) {
            const channelsSection = document.createElement('div');
            channelsSection.innerHTML = '<h4>Популярные каналы</h4>';
            channelsData.items.forEach(project => {
                const card = createProjectCard(project);
                channelsSection.appendChild(card);
            });
            recommendationsContent.appendChild(channelsSection);
        }

        if (botsData.items?.length) {
            const botsSection = document.createElement('div');
            botsSection.innerHTML = '<h4>Полезные боты</h4>';
            botsData.items.forEach(project => {
                const card = createProjectCard(project);
                botsSection.appendChild(card);
            });
            recommendationsContent.appendChild(botsSection);
        }

        if (appsData.items?.length) {
            const appsSection = document.createElement('div');
            appsSection.innerHTML = '<h4>Интересные приложения</h4>';
            appsData.items.forEach(project => {
                const card = createProjectCard(project);
                appsSection.appendChild(card);
            });
            recommendationsContent.appendChild(appsSection);
        }

        if (!channelsData.items?.length && !botsData.items?.length && !appsData.items?.length) {
            recommendationsContent.innerHTML = '<div class="no-results">Рекомендации временно недоступны</div>';
        }
    } catch (error) {
        console.error('Ошибка загрузки рекомендаций:', error);
        recommendationsContent.innerHTML = '<div class="no-results">Ошибка загрузки рекомендаций</div>';
    }
}

// Создание карточки проекта (без лайков)
function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'card';
    
    if (project.is_premium) {
        card.classList.add('premium-card');
    }

    // Определение URL для иконки
    let iconHtml = '';
    if (project.avatar_url) {
        iconHtml = `<img src="${project.avatar_url}" alt="${project.title}" class="channel-icon">`;
    } else {
        const firstLetter = project.title.charAt(0).toUpperCase();
        iconHtml = `<div class="channel-letter-badge">${firstLetter}</div>`;
    }

    card.innerHTML = `
        ${project.is_premium ? '<div class="premium-badge">Premium</div>' : ''}
        <div class="card-content">
            <a href="${project.url}" target="_blank" class="channel-clickable-area" data-url="${project.url}">
                <div class="channel-icon-container">
                    ${iconHtml}
                    <div class="channel-info">
                        <h3>${project.title}</h3>
                        <p>${project.description}</p>
                    </div>
                </div>
            </a>
            <div class="subscribers-mini">
                <span class="subscribers-badge">
                    👥 ${formatNumber(project.subscribers_count || 0)}
                </span>
            </div>
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
                project_title: project.title,
                project_url: project.url
            }));
        }
        
        // Открываем ссылку
        window.open(project.url, '_blank');
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
}

// Показать основную вкладку
function showMainTab() {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('search-tab').classList.add('active');
    document.getElementById('results-tab').style.display = 'none';
}

// Инициализация вкладок
function initializeTabs() {
    const tabs = document.querySelectorAll('.bottom-tab');

    function switchTab(tabName) {
        // Скрываем все вкладки
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // Убираем активный класс у всех вкладок
        tabs.forEach(tab => tab.classList.remove('active'));
        
        // Активируем нужную вкладку
        const targetTab = document.getElementById(`${tabName}-tab`);
        if (targetTab) {
            targetTab.classList.add('active');
        }
        
        // Активируем соответствующую кнопку в навигации
        const activeNavTab = document.querySelector(`.bottom-tab[data-tab="${tabName}"]`);
        if (activeNavTab) {
            activeNavTab.classList.add('active');
        }

        // Показываем/скрываем строку поиска в зависимости от вкладки
        if (tabName === 'settings') {
            searchContainer.classList.add('hidden');
        } else {
            searchContainer.classList.remove('hidden');
        }

        // Загружаем контент для вкладки
        if (tabName === 'search') {
            showMainTab();
            loadFeaturedContent();
            loadCategories();
        } else if (tabName === 'recommendations') {
            loadRecommendations();
        }
        // Для settings ничего дополнительно не загружаем
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

// Обработка поиска
const debouncedSearch = debounce(() => {
    const query = searchInput.value.trim();
    if (query.length > 0 || currentFilter !== 'все' || currentSubcategory) {
        loadProjects(currentContentType);
    } else {
        showMainTab();
    }
}, 300);

// Обработка фильтра
function handleFilterToggle() {
    filterModal.classList.add('show');
    document.body.style.overflow = 'hidden'; // Предотвращаем прокрутку фона
}

function handleFilterClose() {
    filterModal.classList.add('closing');
    
    // Дожидаемся завершения анимации перед скрытием
    setTimeout(() => {
        filterModal.classList.remove('show', 'closing');
        document.body.style.overflow = ''; // Возвращаем прокрутку
    }, 400); // Время соответствует продолжительности анимации
}

function handleFilterReset() {
    // Сбрасываем все фильтры
    currentFilter = 'все';
    currentContentType = 'all';
    currentSortBy = 'subscribers';
    currentSubcategory = null;
    
    // Сбрасываем UI
    document.querySelector('input[name="contentType"][value="all"]').checked = true;
    document.querySelector('input[name="sortBy"][value="subscribers"]').checked = true;
    
    // Сбрасываем категории
    document.querySelectorAll('.filter-category-item').forEach(item => {
        item.classList.remove('selected', 'expanded');
    });
    document.querySelectorAll('.filter-subcategories').forEach(sub => {
        sub.classList.remove('show');
    });
    document.querySelector('.filter-category-item[data-category="все"]').classList.add('selected');
}

function handleFilterApply() {
    // Получаем выбранные значения
    const contentTypeInput = document.querySelector('input[name="contentType"]:checked');
    const sortByInput = document.querySelector('input[name="sortBy"]:checked');
    const selectedCategory = document.querySelector('.filter-category-item.selected:not(.subcategory)');
    const selectedSubcategory = document.querySelector('.filter-subcategory-item.selected');
    
    if (contentTypeInput) currentContentType = contentTypeInput.value;
    if (sortByInput) currentSortBy = sortByInput.value;
    
    if (selectedSubcategory) {
        currentSubcategory = selectedSubcategory.dataset.subcategory;
        currentFilter = selectedSubcategory.dataset.parentCategory;
    } else if (selectedCategory) {
        currentFilter = selectedCategory.dataset.category;
        currentSubcategory = null;
    }
    
    // Закрываем модал
    handleFilterClose();
    
    // Применяем фильтры
    loadProjects(currentContentType);
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
    
    // Здесь можно добавить логику для каждого типа настроек
    switch (settingType) {
        case 'notifications':
            // Логика для уведомлений
            break;
        case 'theme':
            // Логика для темы
            break;
        case 'language':
            // Логика для языка
            break;
        case 'support':
            // Открыть бота поддержки
            if (tg.openTelegramLink) {
                tg.openTelegramLink('https://t.me/support_bot');
            }
            break;
        case 'faq':
            // Открыть FAQ
            break;
        case 'privacy':
            // Открыть политику конфиденциальности
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
    if (window.pageYOffset > 300) {
        toTopBtn.style.display = 'block';
    } else {
        toTopBtn.style.display = 'none';
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializeFilter();
    
    // Обработчики событий
    if (searchInput) {
        searchInput.addEventListener('input', debouncedSearch);
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
    
    // Обработка скролла
    window.addEventListener('scroll', handleScroll);
    
    // Плавное закрытие модала при клике на задний фон
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
    
    // Загружаем контент первой вкладки
    loadFeaturedContent();
    loadCategories();
    
    // Готовность приложения
    tg.ready();
});