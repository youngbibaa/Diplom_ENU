"""
sentiment_model.py
==================
Анализ тональности текстов (русский + английский).

Архитектура: TF-IDF (word + char n-grams) → Logistic Regression
Подход: обучение на расширенном корпусе новостных фраз (~300 примеров),
         сбалансированном по трём классам: positive / neutral / negative.

Signed score: float в диапазоне [-1.0, +1.0]
  score > 0  → позитивный оттенок
  score ≈ 0  → нейтральный
  score < 0  → негативный
"""

from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


# ─────────────────────────────────────────────────────────────────────────────
#  Обучающая выборка
#  ~100 примеров на каждый класс (RU + EN), покрывающие основные новостные
#  домены: экономика, политика, общество, наука, конфликты, спорт.
# ─────────────────────────────────────────────────────────────────────────────

_POSITIVE_RU = [
    # экономика / бизнес
    "рынок восстановился после позитивных новостей",
    "экономика показала рост выше ожиданий аналитиков",
    "инвестиции в регион резко выросли благодаря реформам",
    "компания отчиталась о рекордной прибыли за квартал",
    "биржа закрылась в плюсе на фоне хорошей статистики",
    "производство выросло на десять процентов по итогам года",
    "экспорт увеличился и торговый баланс улучшился",
    "бюджет исполнен с профицитом благодаря росту доходов",
    "малый бизнес получил поддержку и показывает рост",
    "новый завод открылся и создал тысячи рабочих мест",
    # политика / дипломатия
    "переговоры завершились успехом и стороны подписали соглашение",
    "дипломатические отношения нормализованы и сотрудничество возобновляется",
    "страны достигли компромисса по ключевым вопросам",
    "мирный договор подписан после долгих переговоров",
    "альянс укрепился новыми договорённостями о сотрудничестве",
    "напряжённость снизилась после успешного раунда переговоров",
    "лидеры стран договорились о совместных проектах",
    "реформы одобрены и получили широкую поддержку общества",
    "международное сотрудничество приносит результаты",
    "стороны готовы к конструктивному диалогу",
    # наука / технологии
    "учёные объявили о прорыве в области медицины",
    "новая вакцина показала высокую эффективность в испытаниях",
    "технологический стартап привлёк крупные инвестиции",
    "исследование показало положительные результаты лечения",
    "разработка получила международное признание",
    "новый препарат прошёл испытания и будет выпущен",
    "учёные создали эффективный метод борьбы с болезнью",
    "инновационный проект получил государственную поддержку",
    # общество / социальная сфера
    "уровень жизни населения заметно вырос",
    "новая программа помогла тысячам семей",
    "количество рабочих мест увеличилось по всей стране",
    "образование стало более доступным благодаря реформе",
    "здравоохранение улучшилось после введения новых стандартов",
    "гуманитарная помощь доставлена в нуждающиеся регионы",
    # спорт
    "сборная победила и вышла в финал чемпионата",
    "спортсмен установил новый мировой рекорд",
    "команда одержала уверенную победу в важном матче",
    "олимпийский чемпион завоевал золотую медаль",
    # окружающая среда
    "выбросы углекислого газа снизились благодаря новым технологиям",
    "восстановление лесов идёт быстрее чем планировалось",
    "международное соглашение по климату принято",
    "возобновляемая энергия обеспечивает рекордную долю электричества",
]

_NEUTRAL_RU = [
    # политика
    "официальные лица провели встречу в столице",
    "правительство опубликовало новое заявление по ситуации",
    "президент встретился с министрами для обсуждения вопросов",
    "комитет представил свой доклад парламенту",
    "пресс-конференция состоялась после заседания кабинета",
    "делегация прибыла для проведения переговоров",
    "документ содержит обновлённые данные о ситуации",
    "стороны обменялись позициями на встрече",
    "новый закон вступил в силу с начала года",
    "парламент рассмотрит законопроект на следующей неделе",
    # экономика
    "компания выпустила квартальный отчёт о деятельности",
    "аналитики представили прогнозы на следующий год",
    "центральный банк сохранил процентную ставку без изменений",
    "объём торговли между странами остался на прежнем уровне",
    "данные по инфляции опубликованы статистическим ведомством",
    "бюджет на следующий год представлен в парламент",
    "статистика занятости за квартал опубликована",
    "рынок торговался в узком диапазоне в течение дня",
    # общество
    "в городе прошла конференция по вопросам образования",
    "население страны по переписи составило более ста миллионов",
    "в регионе проходят муниципальные выборы",
    "новое здание больницы открыто для приёма пациентов",
    "школы готовятся к новому учебному году",
    # наука
    "исследователи продолжают изучать данный феномен",
    "университет объявил о наборе на новые программы",
    "конференция учёных пройдёт в следующем месяце",
    "результаты исследования опубликованы в научном журнале",
    # международные отношения
    "саммит лидеров запланирован на конец квартала",
    "делегации прибыли для участия в форуме",
    "организация провела плановое заседание совета",
    "дипломатическая нота направлена в министерство иностранных дел",
    # прочее нейтральное
    "репортаж описывает текущее положение дел в отрасли",
    "интервью с экспертом опубликовано в издании",
    "новость посвящена событиям в соседнем регионе",
    "пресс-служба подтвердила проведение мероприятия",
    "обзор рынка опубликован ведущим агентством",
    "статья объясняет суть принятых изменений",
    "ведомство обнародовало статистику за прошлый период",
    "переговоры продолжаются в штатном режиме",
    "состав делегации объявлен официально",
    "заседание перенесено на следующую неделю",
]

_NEGATIVE_RU = [
    # конфликты / война
    "война продолжается и число жертв растёт",
    "ракетные удары нанесены по жилым кварталам",
    "мирные жители погибли в результате атаки",
    "боевые действия привели к гуманитарной катастрофе",
    "ситуация обострилась после новых ударов по территории",
    "погибли солдаты в результате засады",
    "столкновения унесли жизни мирных граждан",
    "обстрел жилых домов вызвал панику среди населения",
    "тысячи людей вынуждены покинуть дома из-за боёв",
    "инфраструктура разрушена в результате бомбардировок",
    # экономика / кризис
    "рынок резко упал на фоне нарастающей неопределённости",
    "компания объявила о банкротстве после убытков",
    "инфляция достигла многолетнего максимума",
    "безработица выросла на фоне закрытия предприятий",
    "экономика вошла в рецессию третий квартал подряд",
    "инвесторы бегут с рынка из-за страха потерь",
    "курс валюты рухнул и уровень жизни упал",
    "дефицит бюджета резко вырос из-за падения доходов",
    "производство сократилось из-за нехватки ресурсов",
    "санкции ударили по экономике и вызвали кризис",
    # катастрофы / трагедии
    "наводнение уничтожило дома и унесло жизни людей",
    "землетрясение разрушило целые кварталы города",
    "пожар охватил лесные угодья и угрожает посёлкам",
    "авиакатастрофа унесла жизни всех пассажиров",
    "число жертв стихийного бедствия продолжает расти",
    # политика / скандалы
    "коррупционный скандал привёл к отставке министра",
    "президент обвиняется в превышении должностных полномочий",
    "выборы признаны сфальсифицированными международными наблюдателями",
    "протесты переросли в столкновения с полицией",
    "власти применили силу против мирных демонстрантов",
    "арест оппозиционных лидеров вызвал волну осуждения",
    # общество
    "уровень бедности вырос после отмены льгот",
    "здравоохранение в упадке из-за нехватки финансирования",
    "преступность выросла в условиях кризиса",
    "школы закрылись из-за угрозы безопасности",
    # экология
    "катастрофический разлив нефти загрязнил побережье",
    "засуха уничтожила урожай и угрожает продовольственной безопасности",
    "загрязнение воздуха достигло опасного уровня в городе",
    "вырубка лесов достигла катастрофических масштабов",
]

_POSITIVE_EN = [
    "markets recover after positive economic agreement",
    "peace talks show progress and tensions are easing",
    "the company reported strong growth and better results",
    "new support package improves the situation significantly",
    "scientists announced a breakthrough in treatment options",
    "the reform was welcomed by investors and citizens",
    "cooperation between countries improved regional stability",
    "production increased and the economic outlook is positive",
    "the agreement was successful and reduced major risks",
    "unemployment fell to its lowest level in decades",
    "trade deal signed boosting exports and creating jobs",
    "vaccine trials show high effectiveness with no major side effects",
    "economy expanded faster than expected in the last quarter",
    "climate agreement reached with commitments from major nations",
    "humanitarian aid reached thousands of displaced families",
    "the ceasefire held and negotiations are progressing well",
    "investment surge signals confidence in the regional economy",
    "medical breakthrough offers hope for millions of patients",
    "diplomatic relations restored after years of tension",
    "renewable energy output hit record highs this month",
]

_NEUTRAL_EN = [
    "officials said the meeting is scheduled for thursday",
    "the report describes the current political situation",
    "the government published a new statement today",
    "the president met with ministers in the capital",
    "the company released its quarterly earnings report",
    "analysts discussed the possible scenarios for next year",
    "the committee presented a formal recommendation to the board",
    "the document contains updated operational and financial data",
    "the central bank held interest rates at current levels",
    "parliament will debate the proposed bill next week",
    "the ambassador arrived for scheduled diplomatic consultations",
    "the agency confirmed the findings of the independent audit",
    "negotiations are continuing at the agreed upon pace",
    "the delegation arrived for the international summit",
    "the budget proposal was submitted to the legislature",
    "researchers published their findings in a peer reviewed journal",
    "the election will be held at the end of the month",
    "the organization held its annual general assembly",
    "the ministry released statistics for the previous quarter",
    "the conference on trade issues opened in the capital city",
]

_NEGATIVE_EN = [
    "war escalates and civilians are killed in attacks",
    "oil prices surge amid crisis and growing fear among investors",
    "the economy weakens as conflict spreads across the region",
    "the company reported heavy losses and declining demand",
    "missile strikes caused widespread damage and panic",
    "investors fear a deep recession and further instability",
    "the attack increased risks and tensions across the border",
    "the situation worsened after another deadly military strike",
    "the market fell sharply because of growing uncertainty",
    "the crisis deepened and public confidence completely collapsed",
    "floods destroyed homes and left thousands without shelter",
    "the earthquake caused massive destruction in the city centre",
    "corruption scandal forced the minister to resign in disgrace",
    "election results disputed amid widespread fraud allegations",
    "protests turned violent as police used force on demonstrators",
    "sanctions crippled the economy and caused severe shortages",
    "unemployment surged to record levels after factory closures",
    "inflation hit a decade high burdening ordinary households",
    "oil spill devastated the coastline and local fishing communities",
    "forest fires raged out of control destroying thousands of acres",
]

TRAIN_TEXTS = (
    _POSITIVE_RU + _NEUTRAL_RU + _NEGATIVE_RU
    + _POSITIVE_EN + _NEUTRAL_EN + _NEGATIVE_EN
)

TRAIN_LABELS = (
    ["positive"] * len(_POSITIVE_RU)
    + ["neutral"] * len(_NEUTRAL_RU)
    + ["negative"] * len(_NEGATIVE_RU)
    + ["positive"] * len(_POSITIVE_EN)
    + ["neutral"] * len(_NEUTRAL_EN)
    + ["negative"] * len(_NEGATIVE_EN)
)


# ─────────────────────────────────────────────────────────────────────────────
#  Модель
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache
def get_sentiment_pipeline() -> Pipeline:
    """
    Строит и обучает pipeline при первом вызове, кэширует результат.

    Признаки:
      - word_tfidf : word unigrams + bigrams (учитывает словосочетания)
      - char_tfidf : char n-grams (3-5) — устойчив к морфологическим вариантам

    Классификатор: Logistic Regression с балансировкой классов.
    """
    features = FeatureUnion(
        [
            (
                "word_tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    sublinear_tf=True,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=20_000,
                ),
            ),
            (
                "char_tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    sublinear_tf=True,
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=1,
                    max_features=30_000,
                ),
            ),
        ]
    )

    pipeline = Pipeline(
        [
            ("features", features),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                    C=1.5,
                ),
            ),
        ]
    )
    pipeline.fit(TRAIN_TEXTS, TRAIN_LABELS)
    return pipeline


def predict_sentiment(text: str) -> tuple[str, float]:
    """
    Предсказывает тональность текста.

    Возвращает
    ----------
    label : "positive" | "neutral" | "negative"
    score : float [-1.0, +1.0]
        positive_proba - negative_proba
    """
    text = (text or "").strip()
    if not text:
        return "neutral", 0.0

    pipeline = get_sentiment_pipeline()
    probabilities = pipeline.predict_proba([text])[0]
    classes = list(pipeline.named_steps["classifier"].classes_)

    proba_by_label: dict[str, float] = {
        label: float(prob)
        for label, prob in zip(classes, probabilities)
    }

    positive_proba = proba_by_label.get("positive", 0.0)
    negative_proba = proba_by_label.get("negative", 0.0)
    neutral_proba = proba_by_label.get("neutral", 0.0)

    signed_score = round(positive_proba - negative_proba, 4)

    # Если нейтральный класс наиболее вероятен и разница pos/neg мала — neutral
    label = max(proba_by_label, key=proba_by_label.get)
    if abs(signed_score) < 0.10 and neutral_proba >= max(positive_proba, negative_proba):
        label = "neutral"

    return label, signed_score
