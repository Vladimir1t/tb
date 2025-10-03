# База синонимов
SYNONYM_DB = {
    # Новости и СМИ
    'новости': ['новостной', 'новостей', 'сми', 'пресса', 'медиа', 'информация', 'события', 'репортаж', 'журналистика', 'анонсы', 'news', 'media', 'information'],
    'news': ['newspaper', 'media', 'information', 'update', 'headlines', 'breaking', 'reporting', 'новости', 'сми'],
    
    # Игры и развлечения
    'игры': ['игра', 'гейминг', 'гейм', 'развлечения', 'игровой', 'геймплей', 'видеоигры', 'game', 'gaming', 'entertainment', 'play'],
    'game': ['games', 'gaming', 'play', 'player', 'gamer', 'entertainment', 'fun', 'video games', 'игры', 'гейминг'],
    'киберспорт': ['esports', 'киберспортивный', 'соревновательные игры', 'competitive gaming', 'pro gaming'],
    
    # Криптовалюты и блокчейн
    'крипта': ['криптовалюта', 'биткоин', 'блокчейн', 'крипто', 'цифровая валюта', 'crypto', 'cryptocurrency', 'bitcoin', 'blockchain'],
    'crypto': ['cryptocurrency', 'bitcoin', 'blockchain', 'digital currency', 'btc', 'eth', 'ethereum', 'крипта', 'биткоин'],
    
    # Спорт и фитнес
    'спорт': ['спортивный', 'атлетика', 'фитнес', 'тренировка', 'соревнования', 'sport', 'sports', 'fitness', 'athletic'],
    'sport': ['sports', 'fitness', 'athletic', 'training', 'competition', 'workout', 'exercise', 'спорт', 'фитнес'],
    'футбол': ['football', 'soccer', 'футбольный', 'премьер лига', 'чемпионат'],
    'хоккей': ['hockey', 'нхл', 'кхл', 'хоккейный', 'ice hockey'],
    'баскетбол': ['basketball', 'нба', 'баскетбольный', 'b-ball'],
    
    # Технологии и IT
    'технологии': ['техно', 'гаджеты', 'инновации', 'it', 'программирование', 'technology', 'tech', 'innovation', 'gadgets'],
    'technology': ['tech', 'gadgets', 'innovation', 'it', 'programming', 'digital', 'ai', 'технологии', 'it'],
    'программирование': ['coding', 'development', 'software', 'разработка', 'кодинг', 'programming'],
    'искусственный интеллект': ['ai', 'artificial intelligence', 'машинное обучение', 'нейросети', 'machine learning'],
    'ai': ['artificial intelligence', 'machine learning', 'neural networks', 'deep learning', 'искусственный интеллект'],
    
    # Бизнес и финансы
    'бизнес': ['предпринимательство', 'коммерция', 'стартап', 'компания', 'финансы', 'business', 'enterprise', 'startup', 'commerce'],
    'business': ['enterprise', 'commerce', 'startup', 'company', 'finance', 'entrepreneurship', 'corporation', 'бизнес', 'стартап'],
    'финансы': ['finance', 'money', 'investment', 'трейдинг', 'инвестиции', 'экономика'],
    'инвестиции': ['investment', 'investing', 'трейдинг', 'тrading', 'фондовый рынок'],
    
    # Образование
    'образование': ['обучение', 'учеба', 'курсы', 'школа', 'университет', 'education', 'learning', 'study', 'courses'],
    'education': ['learning', 'study', 'courses', 'school', 'university', 'teaching', 'training', 'образование', 'обучение'],
    'онлайн курсы': ['online courses', 'e-learning', 'digital learning', 'удаленное обучение'],
    
    # Здоровье и медицина
    'здоровье': ['медицина', 'здоровый', 'фитнес', 'мед', 'врач', 'лечение', 'health', 'medical', 'medicine', 'wellness'],
    'health': ['medical', 'fitness', 'medicine', 'doctor', 'treatment', 'wellness', 'healthcare', 'здоровье', 'медицина'],
    'йога': ['yoga', 'медитация', 'mindfulness', 'практика'],
    'диета': ['diet', 'nutrition', 'питание', 'похудение', 'weight loss'],
    
    # Путешествия
    'путешествия': ['туризм', 'отдых', 'поездки', 'направления', 'отпуск', 'travel', 'tourism', 'vacation', 'trip'],
    'travel': ['tourism', 'vacation', 'trip', 'destination', 'holiday', 'journey', 'adventure', 'путешествия', 'туризм'],
    
    # Еда и кулинария
    'еда': ['кулинария', 'рецепты', 'питание', 'кухня', 'готовка', 'food', 'cooking', 'recipes', 'cuisine'],
    'food': ['cooking', 'recipes', 'nutrition', 'cuisine', 'cook', 'meal', 'dish', 'еда', 'кулинария'],
    'рестораны': ['restaurants', 'cafes', 'бары', 'еда навынос', 'delivery'],
    
    # Музыка
    'музыка': ['аудио', 'треки', 'плейлист', 'исполнители', 'концерты', 'music', 'audio', 'tracks', 'playlist'],
    'music': ['audio', 'tracks', 'playlist', 'artists', 'concerts', 'songs', 'bands', 'музыка', 'треки'],
    'хип хоп': ['hip hop', 'rap', 'рэп', 'рэп музыка'],
    'электронная музыка': ['electronic music', 'edm', 'techno', 'house', 'dance music'],
    
    # Кино и сериалы
    'фильмы': ['кино', 'сериалы', 'фильм', 'кинотеатр', 'режиссер', 'movies', 'cinema', 'films', 'series'],
    'movies': ['cinema', 'films', 'series', 'theater', 'director', 'hollywood', 'blockbuster', 'фильмы', 'кино'],
    'сериалы': ['tv series', 'tv shows', 'netflix', 'streaming', 'телесериалы'],
    
    # Автомобили
    'машины': ['авто', 'автомобили', 'транспорт', 'водитель', 'драйв', 'cars', 'auto', 'automobile', 'vehicle'],
    'cars': ['auto', 'automobile', 'vehicle', 'driver', 'drive', 'motors', 'automotive', 'машины', 'авто'],
    
    # Мода и красота
    'мода': ['стиль', 'одежда', 'тренды', 'бьюти', 'красота', 'fashion', 'style', 'clothing', 'beauty'],
    'fashion': ['style', 'clothing', 'trends', 'beauty', 'look', 'apparel', 'мода', 'стиль'],
    'косметика': ['cosmetics', 'makeup', 'beauty products', 'уход за кожей', 'skincare'],
    
    # Политика
    'политика': ['государство', 'власть', 'правительство', 'выборы', 'партии', 'politics', 'government', 'elections'],
    'politics': ['government', 'power', 'elections', 'parties', 'state', 'democracy', 'политика', 'правительство'],
    
    # Наука и исследования
    'наука': ['science', 'research', 'исследования', 'scientific', 'открытия', 'discoveries'],
    'science': ['research', 'scientific', 'discovery', 'experiment', 'physics', 'biology', 'chemistry', 'наука'],
    'космос': ['space', 'astronomy', 'nasa', 'космонавтика', 'alliance', 'galaxy'],
    'физика': ['physics', 'quantum', 'механика', 'теоретическая физика'],
    'биология': ['biology', 'genetics', 'dna', 'evolution', 'генетика'],
    
    # Искусство и культура
    'искусство': ['art', 'culture', 'художественный', 'creative', 'arts', 'cultural', 'творчество'],
    'art': ['arts', 'culture', 'creative', 'painting', 'sculpture', 'design', 'искусство', 'культура'],
    'живопись': ['painting', 'drawing', 'illustration', 'artwork', 'картины'],
    'фотография': ['photography', 'photo', 'camera', 'съемка', 'photos'],
    
    # Книги и литература
    'книги': ['books', 'literature', 'reading', 'authors', 'novels', 'литература', 'чтение'],
    'books': ['literature', 'reading', 'authors', 'novels', 'publishing', 'library', 'книги', 'литература'],
    
    # Хобби и увлечения
    'хобби': ['hobby', 'hobbies', 'interests', 'pastime', 'leisure', 'увлечения', 'досуг'],
    'hobby': ['hobbies', 'interests', 'pastime', 'leisure', 'recreation', 'хобби', 'увлечения'],
    'рукоделие': ['handmade', 'crafts', 'diy', 'creative', 'своими руками'],
    'садоводство': ['gardening', 'plants', 'flowers', 'garden', 'растения'],
    
    # Блоги и влоги
    'блог': ['blog', 'vlog', 'blogging', 'content', 'creator', 'влог', 'контент'],
    'blog': ['vlog', 'blogging', 'content', 'creator', 'influencer', 'youtube', 'instagram', 'блог'],
    'влог': ['vlog', 'video blog', 'youtube', 'video content', 'video creator'],
    
    # Подкасты и аудио
    'подкасты': ['podcasts', 'audio shows', 'radio shows', 'podcasting', 'аудиошоу'],
    'podcasts': ['audio shows', 'radio shows', 'podcasting', 'episodes', 'подкасты'],
    
    # Социальные сети
    'социальные сети': ['social media', 'social networks', 'smm', 'instagram', 'facebook', 'twitter'],
    'social media': ['social networks', 'smm', 'instagram', 'facebook', 'twitter', 'tiktok', 'соцсети'],
    
    # Психология и саморазвитие
    'психология': ['psychology', 'mental health', 'therapy', 'self-help', 'mind', 'психическое здоровье'],
    'психология': ['psychology', 'mental health', 'therapy', 'self-help', 'mind', 'психическое здоровье'],
    'саморазвитие': ['self-development', 'personal growth', 'self-improvement', 'motivation', 'личностный рост'],
    
    # Электроника и гаджеты
    'гаджеты': ['gadgets', 'devices', 'electronics', 'tech', 'smartphones', 'устройства'],
    'gadgets': ['devices', 'electronics', 'tech', 'smartphones', 'gadget', 'tech products', 'гаджеты'],
    
    # Недвижимость
    'недвижимость': ['real estate', 'property', 'housing', 'apartments', 'houses', 'риелтор'],
    'real estate': ['property', 'housing', 'apartments', 'houses', 'realtor', 'недвижимость'],
    
    # Маркетинг и реклама
    'маркетинг': ['marketing', 'advertising', 'promotion', 'branding', 'smm', 'реклама'],
    'marketing': ['advertising', 'promotion', 'branding', 'smm', 'digital marketing', 'маркетинг'],
    
    # Дизайн и креатив
    'дизайн': ['design', 'graphic design', 'ui/ux', 'creative', 'art direction', 'графический дизайн'],
    'design': ['graphic design', 'ui/ux', 'creative', 'art direction', 'visual', 'дизайн'],
    
    # Фриланс и удаленная работа
    'фриланс': ['freelance', 'remote work', 'freelancing', 'self-employed', 'удаленная работа'],
    'freelance': ['remote work', 'freelancing', 'self-employed', 'contract work', 'фриланс'],
    
    # История и археология
    'история': ['history', 'historical', 'archaeology', 'past', 'heritage', 'археология'],
    'history': ['historical', 'archaeology', 'past', 'heritage', 'ancient', 'история'],
    
    # Природа и экология
    'природа': ['nature', 'environment', 'ecology', 'wildlife', 'animals', 'экология'],
    'nature': ['environment', 'ecology', 'wildlife', 'animals', 'outdoors', 'природа'],
    
    # Астрономия
    'астрономия': ['astronomy', 'space', 'stars', 'planets', 'universe', 'космос'],
    'astronomy': ['space', 'stars', 'planets', 'universe', 'cosmos', 'астрономия'],
    
    # Математика
    'математика': ['mathematics', 'math', 'calculus', 'algebra', 'geometry', 'maths'],
    'mathematics': ['math', 'calculus', 'algebra', 'geometry', 'maths', 'математика'],
    
    # Программирование и языки
    'python': ['питон', 'python programming', 'django', 'flask', 'data science'],
    'javascript': ['js', 'node.js', 'react', 'vue', 'frontend', 'веб разработка'],
    'веб разработка': ['web development', 'frontend', 'backend', 'fullstack', 'web design'],
    
    # Мобильные приложения
    'мобильные приложения': ['mobile apps', 'android', 'ios', 'app development', 'smartphone apps'],
    'mobile apps': ['android', 'ios', 'app development', 'smartphone apps', 'мобильные приложения'],
    
    # Иностранные языки
    'английский': ['english', 'english language', 'learn english', 'english learning', 'language'],
    'english': ['english language', 'learn english', 'english learning', 'language', 'английский'],
    
    # Кулинарные направления
    'азиатская кухня': ['asian cuisine', 'chinese food', 'japanese food', 'sushi', 'thai food'],
    'европейская кухня': ['european cuisine', 'french cuisine', 'italian food', 'mediterranean'],
    
    # Виды спорта
    'теннис': ['tennis', 'big tennis', 'table tennis', 'настольный теннис'],
    'плавание': ['swimming', 'pool', 'swim', 'бассейн', 'water sports'],
    'бег': ['running', 'jogging', 'marathon', 'track', 'легкая атлетика'],
    
    # Творческие хобби
    'рисование': ['drawing', 'painting', 'sketching', 'art', 'illustration'],
    'пение': ['singing', 'vocal', 'music', 'choir', 'вокал'],
    'танцы': ['dancing', 'dance', 'choreography', 'бальные танцы', 'hip hop dance'],
    
    # Эзотерика и духовность
    'астрология': ['astrology', 'horoscope', 'zodiac', 'stars', 'гороскоп'],
    'медитация': ['meditation', 'mindfulness', 'yoga', 'relaxation', 'спокойствие'],
    
    # Технические направления
    'робототехника': ['robotics', 'robots', 'ai robots', 'automation', 'automated systems'],
    'виртуальная реальность': ['virtual reality', 'vr', 'ar', 'augmented reality', 'mixed reality'],
    
    # Медицинские направления
    'стоматология': ['dentistry', 'dental', 'teeth', 'oral health', 'зубы'],
    'педиатрия': ['pediatrics', 'children health', 'kids medicine', 'детское здоровье'],
    
    # Бьюти индустрия
    'парикмахерская': ['hair salon', 'hairstyling', 'haircuts', 'styling', 'салон красоты'],
    'маникюр': ['manicure', 'nails', 'nail art', 'nail design', 'ногти'],
    
    # Домашние животные
    'домашние животные': ['pets', 'pet care', 'dogs', 'cats', 'animals', 'питомцы'],
    'pets': ['pet care', 'dogs', 'cats', 'animals', 'pet ownership', 'домашние животные'],
    
    # Автотематика
    'электромобили': ['electric cars', 'ev', 'tesla', 'electric vehicles', 'зеленый транспорт'],
    'мотоциклы': ['motorcycles', 'bikes', 'motorbikes', 'harley', 'байки'],
    
    # Игровые жанры
    'рпг': ['rpg', 'role playing games', 'roleplay', 'mmorpg', 'ролевые игры'],
    'шутеры': ['shooters', 'fps', 'first person shooter', 'action games', 'экшен'],
    
    # Музыкальные жанры
    'рок': ['rock', 'rock music', 'rock and roll', 'alternative rock', 'classic rock'],
    'джаз': ['jazz', 'jazz music', 'blues', 'improvisation', 'свинг'],
    
    # Киножанры
    'комедии': ['comedy', 'comedies', 'funny movies', 'humor', 'юмор'],
    'драмы': ['drama', 'dramas', 'serious films', 'emotional movies', 'мелодрамы'],
    
    # Литературные жанры
    'фантастика': ['science fiction', 'sci-fi', 'fantasy', 'sf', 'фэнтези'],
    'детективы': ['detective', 'mystery', 'crime', 'thriller', 'триллеры']
}
