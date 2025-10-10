// survey.js - Логика опросника для новых пользователей

// Структура тем и подтем на основе предоставленного дерева
const SURVEY_TOPICS = {
    'IT и технологии': {
        icon: '💻',
        value: 'IT',
        subTopics: ['Программирование', 'Нейросети и ИИ', 'DevOps/SRE', 'Кибербезопасность']
    },
    'Медиа и развлечения': {
        icon: '🎬',
        value: 'Медиа и развлечения',
        subTopics: ['Фильмы и сериалы', 'Музыка', 'Игры', 'Аниме']
    },
    'Бизнес и финансы': {
        icon: '💼',
        value: 'Бизнес и финансы',
        subTopics: ['Бизнес', 'Криптовалюты', 'Маркетинг', 'Инвестиции']
    },
    'Образование': {
        icon: '📚',
        value: 'Образование',
        subTopics: ['Книги и литература', 'Наука', 'Познавательные']
    },
    'Лайфстайл': {
        icon: '✨',
        value: 'Лайфстайл',
        subTopics: ['Психология', 'Красота и мода', 'Здоровье', 'Отношения']
    },
    'Путешествия': {
        icon: '✈️',
        value: 'Путешествия',
        subTopics: []
    },
    'Спорт': {
        icon: '⚽',
        value: 'Спорт',
        subTopics: []
    },
    'Авто/мото': {
        icon: '🚗',
        value: 'Авто и мото',
        subTopics: []
    },
    'Наука/тех': {
        icon: '🔬',
        value: 'Наука и технологии',
        subTopics: []
    },
    'Хобби/дом': {
        icon: '🏡',
        value: 'Хобби и дом',
        subTopics: ['Искусство', 'Дизайн', 'Кулинария', 'Животные']
    },
    'Новости/политика': {
        icon: '📰',
        value: 'Новости',
        subTopics: ['Политика', 'Региональные']
    },
    'Региональное': {
        icon: '🌍',
        value: 'Региональные',
        subTopics: []
    }
};

class Survey {
    constructor() {
        this.selectedMainTopics = [];
        this.selectedSubTopics = [];
        this.maxMainTopics = 7;
        
        // DOM элементы
        this.overlay = document.getElementById('surveyOverlay');
        this.screen1 = document.getElementById('surveyScreen1');
        this.screen2 = document.getElementById('surveyScreen2');
        this.mainTopicsChips = document.getElementById('mainTopicsChips');
        this.surveySubTopics = document.getElementById('surveySubTopics');
        this.selectedCount = document.getElementById('selectedCount');
        this.nextBtn = document.getElementById('surveyNextBtn');
        this.skipBtn = document.getElementById('surveySkipBtn');
        this.backBtn = document.getElementById('surveyBackBtn');
        this.completeBtn = document.getElementById('surveyCompleteBtn');
        
        this.init();
    }
    
    init() {
        this.renderMainTopics();
        this.attachEventListeners();
    }
    
    renderMainTopics() {
        this.mainTopicsChips.innerHTML = '';
        
        Object.entries(SURVEY_TOPICS).forEach(([name, data]) => {
            const chip = document.createElement('div');
            chip.className = 'survey-chip';
            chip.dataset.topic = data.value;
            chip.innerHTML = `
                <span class="survey-chip-icon">${data.icon}</span>
                <span>${name}</span>
            `;
            
            chip.addEventListener('click', () => this.toggleMainTopic(chip, data.value));
            this.mainTopicsChips.appendChild(chip);
        });
    }
    
    toggleMainTopic(chip, topic) {
        if (chip.classList.contains('selected')) {
            // Убираем выбор
            chip.classList.remove('selected');
            const index = this.selectedMainTopics.indexOf(topic);
            if (index > -1) {
                this.selectedMainTopics.splice(index, 1);
            }
        } else {
            // Добавляем выбор если не достигнут лимит
            if (this.selectedMainTopics.length < this.maxMainTopics) {
                chip.classList.add('selected');
                this.selectedMainTopics.push(topic);
            } else {
                // Показываем уведомление о лимите
                this.showLimitNotification();
            }
        }
        
        this.updateCounter();
        this.updateNextButton();
    }
    
    updateCounter() {
        this.selectedCount.textContent = this.selectedMainTopics.length;
    }
    
    updateNextButton() {
        // Кнопка активна если выбрана хотя бы одна тема (можно и 0)
        this.nextBtn.disabled = false;
    }
    
    showLimitNotification() {
        // Простое визуальное уведомление
        this.selectedCount.style.animation = 'none';
        setTimeout(() => {
            this.selectedCount.style.animation = 'shake 0.5s';
        }, 10);
    }
    
    goToScreen2() {
        // Проверяем нужно ли показывать экран 2
        const topicsWithSubTopics = this.selectedMainTopics.filter(topic => {
            const topicData = Object.values(SURVEY_TOPICS).find(t => t.value === topic);
            return topicData && topicData.subTopics && topicData.subTopics.length > 0;
        });
        
        // Показываем экран 2 только если есть темы с подтемами
        // И ограничиваем максимум 3 темами для уточнения (самые широкие)
        if (topicsWithSubTopics.length > 0) {
            // Берем только первые 3 темы с подтемами для уточнения
            const topicsToRefine = topicsWithSubTopics.slice(0, 3);
            
            // Показываем экран 2
            this.renderSubTopics(topicsToRefine);
            this.screen1.classList.remove('active');
            this.screen2.classList.add('active');
            this.screen2.style.display = 'block';
        } else {
            // Пропускаем экран 2 и завершаем
            this.completeSurvey();
        }
    }
    
    renderSubTopics(topicsToShow = null) {
        this.surveySubTopics.innerHTML = '';
        
        // Используем переданный список тем или все выбранные
        const topicsToRender = topicsToShow || this.selectedMainTopics;
        
        // Отображаем только те темы, которые были выбраны и имеют подтемы
        topicsToRender.forEach(topic => {
            const topicEntry = Object.entries(SURVEY_TOPICS).find(([name, data]) => data.value === topic);
            
            if (topicEntry) {
                const [name, data] = topicEntry;
                
                if (data.subTopics && data.subTopics.length > 0) {
                    const section = document.createElement('div');
                    section.className = 'survey-section';
                    
                    const sectionHeader = document.createElement('h3');
                    sectionHeader.innerHTML = `<span>${data.icon}</span> ${name}`;
                    section.appendChild(sectionHeader);
                    
                    const chipsContainer = document.createElement('div');
                    chipsContainer.className = 'survey-section-chips';
                    
                    data.subTopics.forEach(subTopic => {
                        const chip = document.createElement('div');
                        chip.className = 'survey-chip';
                        chip.dataset.subtopic = subTopic;
                        chip.textContent = subTopic;
                        
                        chip.addEventListener('click', () => this.toggleSubTopic(chip, subTopic));
                        chipsContainer.appendChild(chip);
                    });
                    
                    section.appendChild(chipsContainer);
                    this.surveySubTopics.appendChild(section);
                }
            }
        });
    }
    
    toggleSubTopic(chip, subTopic) {
        if (chip.classList.contains('selected')) {
            chip.classList.remove('selected');
            const index = this.selectedSubTopics.indexOf(subTopic);
            if (index > -1) {
                this.selectedSubTopics.splice(index, 1);
            }
        } else {
            chip.classList.add('selected');
            this.selectedSubTopics.push(subTopic);
        }
    }
    
    goBack() {
        this.screen2.classList.remove('active');
        this.screen2.style.display = 'none';
        this.screen1.classList.add('active');
    }
    
    async completeSurvey() {
        // Получаем ID пользователя из Telegram WebApp
        const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id ?? window.DEBUG_USER_ID;
        
        if (!userId) {
            this.hide();
            return;
        }
        
        try {
            // Отправляем данные на сервер
            const response = await fetch(`${window.API_URL}/users/${userId}/survey`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    main_topics: this.selectedMainTopics,
                    sub_topics: this.selectedSubTopics
                })
            });
            
            if (response.ok) {
                this.hide();
                
                // Опционально: загружаем рекомендации на основе предпочтений
                if (typeof window.loadRecommendationsBasedOnPreferences === 'function') {
                    window.loadRecommendationsBasedOnPreferences();
                }
            } else {
                this.hide();
            }
        } catch (error) {
            this.hide();
        }
    }
    
    skip() {
        // Пропускаем опрос, сохраняем пустые предпочтения
        this.selectedMainTopics = [];
        this.selectedSubTopics = [];
        this.completeSurvey();
    }
    
    show() {
        this.overlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    hide() {
        this.overlay.style.display = 'none';
        document.body.style.overflow = '';
    }
    
    attachEventListeners() {
        this.nextBtn.addEventListener('click', () => this.goToScreen2());
        this.skipBtn.addEventListener('click', () => this.skip());
        this.backBtn.addEventListener('click', () => this.goBack());
        this.completeBtn.addEventListener('click', () => this.completeSurvey());
    }
}

// Добавляем анимацию shake для уведомления о лимите
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
`;
document.head.appendChild(style);

// Экспортируем класс Survey для использования в main.js
window.Survey = Survey;
