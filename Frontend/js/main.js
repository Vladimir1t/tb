const tg = window.Telegram.WebApp;
tg.expand();

const API_URL = 'https://telegram-bot-zgkr.onrender.com';
let searchTimeout;
let currentFilter = 'все';
let page = 0;
let hasMore = true;
let loading = false;

const bottomTabs = document.querySelectorAll('.bottom-tab');
const toTopBtn = document.getElementById('toTopBtn');
const searchInput = document.getElementById('searchInput');
const filterBtn = document.getElementById('filterBtn');
const filterDropdown = document.getElementById('filterDropdown');
const filterOptions = document.querySelectorAll('.filter-option');

// Основная функция загрузки проектов с поиском и фильтром
async function loadProjects(tabName, append = false) {
    if (loading || !hasMore) return;
    loading = true;

    const typeMap = { 'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app' };
    const apiType = typeMap[tabName];
    const tabContent = document.getElementById(`${tabName}-tab`);

    if (!append) {
        tabContent.innerHTML = '<div class="loading">Идёт поиск каналов...</div>';
        page = 0;
        hasMore = true;
    }

    const query = searchInput.value.trim(); // текст поиска
    const themeFilter = currentFilter === 'все' ? '' : currentFilter; // фильтр в нижнем регистре

    console.log("Текущий фильтр (currentFilter):", currentFilter);
    console.log("Тип API (apiType):", apiType);
    console.log("Поисковый запрос (query):", query);
    console.log("Фильтр по теме (themeFilter):", themeFilter);

    try {
        // Если поиск пустой, показываем дефолтные 10 каналов
        const searchParam = query ? `&search=${encodeURIComponent(query)}` : '';

        const response = await fetch(`${API_URL}/projects/?type=${apiType}&theme=${encodeURIComponent(themeFilter)}${searchParam}&limit=10&offset=${page*10}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const projects = await response.json();
        console.log(`Ответ сервера для фильтра "${currentFilter}" (тип: ${apiType}):`, projects); // <-- Добавлено логирование

        // Проверяем, не изменился ли поисковый запрос пока шёл запрос
        const currentQuery = searchInput.value.trim();
        if (currentQuery !== query) {
            loading = false;
            return;
        }

        if (projects.length === 0) {
            hasMore = false;
            if (!append) {
                if (!query && !themeFilter) {
                    const defaultResponse = await fetch(`${API_URL}/projects/?type=${apiType}&limit=10&offset=0`);
                    const defaultProjects = await defaultResponse.json();
                    
                    if (searchInput.value.trim() !== query) {
                        loading = false;
                        return;
                    }
                    
                    let defaultHtml = '';
                    defaultProjects.forEach(project => {
                        const projectId = `${tabName}-${project.name.replace(/\s+/g, '-').toLowerCase()}`;
                        const iconUrl = project.icon || 'https://via.placeholder.com/48';
                        defaultHtml += `
                            <div class="card" data-theme="${project.theme.toLowerCase()}">
                                <div class="card-content">
                                    <a href="${project.link}" class="channel-clickable-area" target="_blank" rel="noopener noreferrer">
                                        ${project.icon ? 
                                            `<img src="${project.icon}" class="channel-icon" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">` : 
                                            ''
                                        }
                                        <div class="channel-letter-badge" ${project.icon ? 'style="display:none;"' : ''}>
                                            ${project.name.charAt(0).toUpperCase()}
                                        </div>
                                        <div class="channel-info">
                                            <h3>${project.name}</h3>
                                            <p>Тематика: ${project.theme}</p>
                                        </div>
                                    </a>
                                    <div class="subscribers-mini">
                                        <span class="subscribers-badge">
                                            ${project.subscribers.toLocaleString()} подписчиков
                                        </span>
                                        <span class="likes-badge">
                                            <svg class="likes-icon-inline" viewBox="0 0 24 24">
                                                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                            </svg>
                                            <span class="likes-count">${project.likes || 0}</span>
                                        </span>
                                    </div>
                                    <div class="actions">
                                        <button class="like-btn" data-project-id="${projectId}" aria-label="Поставить лайк">
                                            <svg class="like-icon" viewBox="0 0 24 24">
                                                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    tabContent.innerHTML = defaultHtml;
                    // Обработчик для кнопки лайка с анимацией
                    tabContent.querySelectorAll('.like-btn').forEach(btn => {
                        btn.onclick = (event) => {
                            event.stopPropagation();
                            
                            // Добавляем класс анимации
                            btn.classList.add('clicked');
                            // Убираем класс через 400 мс (длительность анимации)
                            setTimeout(() => {
                                btn.classList.remove('clicked');
                            }, 400);
                            
                            handleLike(btn.dataset.projectId, btn);
                        };
                    });

                    // Обработчик для плашки с количеством лайков
                    tabContent.querySelectorAll('.likes-badge').forEach(badge => {
                        badge.onclick = (event) => {
                            // Находим соответствующую кнопку лайка в этой карточке
                            const card = event.currentTarget.closest('.card');
                            const likeBtn = card.querySelector('.like-btn');
                            if (likeBtn) {
                                // Добавляем класс clicked для запуска анимации
                                badge.classList.add('clicked');
                                // Убираем класс через 300 мс после завершения анимации
                                setTimeout(() => {
                                    badge.classList.remove('clicked');
                                }, 300);

                                // Вызываем функцию handleLike
                                handleLike(likeBtn.dataset.projectId, likeBtn);
                            }
                        };
                    });
                    page = 1;
                    hasMore = defaultProjects.length === 10;
                } else {
                    // Показываем "Ничего не найдено" только если запрос всё ещё актуален
                    if (searchInput.value.trim() === query) {
                        tabContent.innerHTML = '<div class="no-results">Ничего не найдено</div>';
                    }
                }
            }
            loading = false;
            return;
        }

        let html = '';
        projects.forEach(project => {
            const projectId = `${tabName}-${project.name.replace(/\s+/g, '-').toLowerCase()}`;
            const iconUrl = project.icon || 'https://via.placeholder.com/48';
            html += `
                <div class="card" data-theme="${project.theme.toLowerCase()}">
                    <div class="card-content">
                        <a href="${project.link}" class="channel-clickable-area" target="_blank" rel="noopener noreferrer">
                            ${project.icon ? 
                                `<img src="${project.icon}" class="channel-icon" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">` : 
                                ''
                            }
                            <div class="channel-letter-badge" ${project.icon ? 'style="display:none;"' : ''}>
                                ${project.name.charAt(0).toUpperCase()}
                            </div>
                            <div class="channel-info">
                                <h3>${project.name}</h3>
                                <p>Тематика: ${project.theme}</p>
                            </div>
                        </a>
                        <div class="subscribers-mini">
                            <span class="subscribers-badge">
                                ${project.subscribers.toLocaleString()} подписчиков
                            </span>
                            <span class="likes-badge">
                                <svg class="likes-icon-inline" viewBox="0 0 24 24">
                                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                </svg>
                                <span class="likes-count">${project.likes || 0}</span>
                            </span>
                        </div>
                        <div class="actions">
                            <button class="like-btn" data-project-id="${projectId}" aria-label="Поставить лайк">
                                <svg class="like-icon" viewBox="0 0 24 24">
                                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        if (searchInput.value.trim() !== query) {
            loading = false;
            return;
        }

        // Обработчик для кнопки лайка с анимацией
        tabContent.querySelectorAll('.like-btn').forEach(btn => {
            btn.onclick = (event) => {
                event.stopPropagation();
                
                // Добавляем класс анимации
                btn.classList.add('clicked');
                // Убираем класс через 400 мс (длительность анимации)
                setTimeout(() => {
                    btn.classList.remove('clicked');
                }, 400);
                
                handleLike(btn.dataset.projectId, btn);
            };
        });

        // Обработчик для плашки с количеством лайков
        tabContent.querySelectorAll('.likes-badge').forEach(badge => {
            badge.onclick = (event) => {
                // Находим соответствующую кнопку лайка в этой карточке
                const card = event.currentTarget.closest('.card');
                const likeBtn = card.querySelector('.like-btn');
                if (likeBtn) {
                    // Добавляем класс clicked для запуска анимации
                    badge.classList.add('clicked');
                    // Убираем класс через 300 мс после завершения анимации
                    setTimeout(() => {
                        badge.classList.remove('clicked');
                    }, 300);

                    // Вызываем функцию handleLike
                    handleLike(likeBtn.dataset.projectId, likeBtn);
                }
            };
        });

        if (append) {
            tabContent.insertAdjacentHTML('beforeend', html);
        } else {
            tabContent.innerHTML = html;
        }
        const loadingElements = tabContent.querySelectorAll('.loading');
        loadingElements.forEach(el => el.remove());
        // Обработчик для кнопки лайка с анимацией
        tabContent.querySelectorAll('.like-btn').forEach(btn => {
            btn.onclick = (event) => {
                event.stopPropagation();
                
                // Добавляем класс анимации
                btn.classList.add('clicked');
                // Убираем класс через 400 мс (длительность анимации)
                setTimeout(() => {
                    btn.classList.remove('clicked');
                }, 400);
                
                handleLike(btn.dataset.projectId, btn);
            };
        });

        // Обработчик для плашки с количеством лайков
        tabContent.querySelectorAll('.likes-badge').forEach(badge => {
            badge.onclick = (event) => {
                // Находим соответствующую кнопку лайка в этой карточке
                const card = event.currentTarget.closest('.card');
                const likeBtn = card.querySelector('.like-btn');
                if (likeBtn) {
                    // Добавляем класс clicked для запуска анимации
                    badge.classList.add('clicked');
                    // Убираем класс через 300 мс после завершения анимации
                    setTimeout(() => {
                        badge.classList.remove('clicked');
                    }, 300);  
                    // Вызываем функцию handleLike
                    handleLike(likeBtn.dataset.projectId, likeBtn);
                }
            };
        });

        page++;
        hasMore = projects.length === 10;
    } catch (err) {
        console.error('Ошибка:', err);
        if (!append && searchInput.value.trim() === query) {
            tabContent.innerHTML = '<div class="no-results">Ошибка загрузки данных</div>';
        }
    }

    loading = false;
}

// Функция для обновления позиции и размера индикатора
function updateTabIndicator() {
    const activeTab = document.querySelector('.bottom-tab.active');
    const indicator = document.querySelector('.tab-indicator');
    
    if (activeTab && indicator) {
        // Получаем координаты активной вкладки относительно контейнера
        const tabRect = activeTab.getBoundingClientRect();
        const containerRect = activeTab.parentElement.getBoundingClientRect();
        
        // Вычисляем смещение слева и ширину
        const left = tabRect.left - containerRect.left;
        const width = tabRect.width;
        
        // Применяем стили к индикатору
        indicator.style.left = `${left}px`;
        indicator.style.width = `${width}px`;
    }
}

function resetSearch() {
    searchInput.value = '';
    loadProjects(getActiveTab(), false);
}

function resetFilter() {
    resetFilterToDefault();
    const activeTab = getActiveTab();
    loadProjects(getActiveTab(), false);
}

function getActiveTab() {
    const activeTab = document.querySelector('.tab.active');
    return activeTab ? activeTab.dataset.tab : 'channels';
}

searchInput.addEventListener('blur', () => {
    if (searchInput.value === '') {
        loadProjects(getActiveTab(), false);
    }
});

function handleLike(projectId, likeBtn) {
    likeBtn.classList.toggle('liked');
    // Находим элемент с количеством лайков внутри карточки
    const likesCountElement = likeBtn.closest('.card').querySelector('.likes-count');
    if (likesCountElement) {
        let currentLikes = parseInt(likesCountElement.textContent) || 0;
        likesCountElement.textContent = likeBtn.classList.contains('liked') ? currentLikes + 1 : currentLikes - 1;
    }
    console.log(`Проект ${projectId} ${likeBtn.classList.contains('liked') ? 'лайкнут' : 'дизлайкнут'}`);
}

function switchTab(tabName) {
    document.querySelector('.tab-content.active')?.classList.remove('active');
    bottomTabs.forEach(tab => tab.classList.toggle('active', tab.dataset.tab === tabName));
    const newContent = document.getElementById(`${tabName}-tab`);
    newContent.classList.add('active');
    page = 0;
    hasMore = true;

    // === Добавлено: Сброс фильтра ===
    resetFilterToDefault();
    
    // Добавляем вызов обновления индикатора
    updateTabIndicator();
    
    loadProjects(tabName);
}

// Функция для сброса фильтра на "Все категории"
function resetFilterToDefault() {
    // Сбрасываем переменную currentFilter
    currentFilter = 'все';
    
    // Обновляем текст кнопки фильтра
    if (filterBtn) {
        filterBtn.textContent = 'Фильтр ▼';
    }
    
    // Сбрасываем активный класс у опций фильтра
    if (filterOptions) {
        filterOptions.forEach(option => {
            if (option.dataset.theme === 'все') {
                option.classList.add('active');
            } else {
                option.classList.remove('active');
            }
        });
    }
    
    // Скрываем dropdown, если он открыт
    if (filterDropdown) {
        filterDropdown.classList.remove('show');
    }
}

function applyFiltersAndSearch() {
    page = 0;
    hasMore = true;
    const activeTab = document.querySelector('.bottom-tab.active').dataset.tab;
    loadProjects(activeTab);
}

filterBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    filterDropdown.classList.toggle('show');
    filterBtn.textContent = filterDropdown.classList.contains('show') ? 'Фильтр ▲' : 'Фильтр ▼';
});

filterOptions.forEach(option => {
    option.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        filterOptions.forEach(opt => opt.classList.remove('active'));
        option.classList.add('active');
        currentFilter = option.dataset.theme;
        filterBtn.textContent = currentFilter === 'все' ? 'Фильтр ▼' : currentFilter;
        filterDropdown.classList.remove('show');
        applyFiltersAndSearch();
    });
});

document.addEventListener('click', (e) => {
    if (!filterBtn.contains(e.target) && !filterDropdown.contains(e.target)) {
        filterDropdown.classList.remove('show');
        filterBtn.textContent = currentFilter === 'все' ? 'Фильтр ▼' : currentFilter;
    }
});

bottomTabs.forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));

searchInput.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        applyFiltersAndSearch();
    }, 300);
});

window.onscroll = function() {
    toTopBtn.style.display = (window.scrollY > 300) ? "block" : "none";
};

window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
        const activeTab = document.querySelector('.bottom-tab.active').dataset.tab;
        const tabContent = document.getElementById(`${activeTab}-tab`);
        const loadingElements = tabContent.querySelectorAll('.loading');
        loadingElements.forEach(el => el.remove());
        tabContent.insertAdjacentHTML('beforeend', '<div class="loading">Идёт поиск каналов...</div>');
        loadProjects(activeTab, true);
    }
});

toTopBtn.addEventListener('click', () => window.scrollTo({top: 0, behavior: 'smooth'}));

// В конце файла, где у вас DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    loadProjects('channels');
    tg.platform !== 'unknown' && tg.BackButton.show();
    tg.platform !== 'unknown' && tg.BackButton.onClick(() => tg.close());
    
    // Инициализируем позицию индикатора
    updateTabIndicator();
});

// Добавляем обработчик изменения размера окна
window.addEventListener('resize', updateTabIndicator);

// Обновляем обработчики кликов на вкладках
bottomTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        // Сначала убираем класс active у всех вкладок
        bottomTabs.forEach(t => t.classList.remove('active'));
        // Добавляем класс active только кликнутой вкладке
        tab.classList.add('active');
        // Переключаем контент
        switchTab(tab.dataset.tab);
    });
});

// === Swipe Navigation для переключения вкладок ===
let touchStartX = 0;
let touchEndX = 0;
const swipeThreshold = 50; // Минимальная дистанция свайпа в пикселях

// Обработчик начала касания
document.addEventListener('touchstart', e => {
    touchStartX = e.changedTouches[0].screenX;
}, { passive: true });

// Обработчик окончания касания
document.addEventListener('touchend', e => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipeGesture();
}, { passive: true });

// Функция обработки свайп-жеста
function handleSwipeGesture() {
    const swipeDistance = touchStartX - touchEndX;
    
    // Определяем направление свайпа
    if (Math.abs(swipeDistance) > swipeThreshold) {
        const activeTab = document.querySelector('.bottom-tab.active');
        const allTabs = Array.from(document.querySelectorAll('.bottom-tab'));
        const currentIndex = allTabs.indexOf(activeTab);
        
        let targetIndex;
        
        if (swipeDistance > 0) {
            // Свайп влево -> следующая вкладка
            targetIndex = (currentIndex + 1) % allTabs.length;
        } else {
            // Свайп вправо -> предыдущая вкладка
            targetIndex = (currentIndex - 1 + allTabs.length) % allTabs.length;
        }
        
        // Получаем имя целевой вкладки и переключаемся
        const targetTabName = allTabs[targetIndex].dataset.tab;
        switchTab(targetTabName);
        
        // Обновляем активный класс на вкладках
        allTabs.forEach(tab => tab.classList.remove('active'));
        allTabs[targetIndex].classList.add('active');
    }
}