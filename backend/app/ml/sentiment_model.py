from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.preprocessing.cleaner import RussianTextPreprocessor


@dataclass
class SentimentPrediction:
    label: str
    score: float


SEED_SAMPLES: list[tuple[str, str]] = [
    ("positive", "экономика показывает устойчивый рост и развитие рынка"),
    ("positive", "компания сообщила об улучшении показателей и высоком спросе"),
    ("positive", "граждане поддержали инициативу и отметили успех проекта"),
    ("positive", "инвестиции выросли а производство продемонстрировало прогресс"),
    ("positive", "пользователи положительно оценили сервис и качество работы"),
    ("positive", "правительство объявило о запуске новых мер поддержки бизнеса"),
    ("positive", "рынок труда стабилизировался и доходы населения увеличились"),
    ("positive", "исследование показало улучшение экологической ситуации в регионе"),
    ("positive", "команда добилась победы и получила высокую оценку экспертов"),
    ("positive", "в отрасли наблюдается рост экспорта и расширение производства"),
    ("neutral", "ведомство опубликовало отчет о состоянии рынка за квартал"),
    ("neutral", "сегодня в городе состоялось заседание комиссии по транспорту"),
    ("neutral", "новый документ описывает порядок работы информационной системы"),
    ("neutral", "участники форума обсудили вопросы образования и цифровизации"),
    ("neutral", "в публикации приведены статистические данные за прошлый месяц"),
    ("neutral", "на сайте размещена информация о расписании и маршрутах"),
    ("neutral", "аналитики представили обзор текущей ситуации без резких оценок"),
    ("neutral", "министерство рассмотрело несколько сценариев дальнейшего развития"),
    ("neutral", "компания обновила регламент и представила план мероприятий"),
    ("neutral", "в отчете перечислены показатели производства и поставок"),
    ("negative", "на рынке усилился кризис и выросли риски для инвесторов"),
    ("negative", "предприятие столкнулось со спадом спроса и убытками"),
    ("negative", "жители жалуются на проблемы и ухудшение качества услуг"),
    ("negative", "в регионе произошел конфликт который вызвал негативную реакцию"),
    ("negative", "аналитики предупредили об инфляции и снижении доходов"),
    ("negative", "компания сообщила об аварии задержках и финансовых потерях"),
    ("negative", "эксперты отмечают дефицит ресурсов и рост социальной напряженности"),
    ("negative", "скандал вокруг проекта привел к падению доверия пользователей"),
    ("negative", "на фоне санкций усилилось давление на отрасль и экспорт сократился"),
    ("negative", "в отчете говорится о сокращении производства и росте безработицы"),
]


class TfidfLogRegSentimentAnalyzer:
    def __init__(self):
        self.preprocessor = RussianTextPreprocessor(keep_stopwords=False)
        self.pipeline = Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        min_df=1,
                        max_features=12000,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        C=4.0,
                        class_weight="balanced",
                        solver="lbfgs",
                    ),
                ),
            ]
        )
        self.is_fitted = False
        self.train_from_seed()

    def _normalize_for_model(self, text: str) -> str:
        return self.preprocessor.preprocess_text(text)

    def train_from_seed(self) -> None:
        texts = [self._normalize_for_model(text) for _, text in SEED_SAMPLES]
        labels = [label for label, _ in SEED_SAMPLES]
        self.pipeline.fit(texts, labels)
        self.is_fitted = True

    def fit(self, texts: list[str], labels: list[str]) -> None:
        processed = [self._normalize_for_model(text) for text in texts]
        pairs = [(t, y) for t, y in zip(processed, labels) if t.strip()]
        if len(pairs) < 9 or len(set(labels)) < 3:
            return
        x_train = [t for t, _ in pairs]
        y_train = [y for _, y in pairs]
        self.pipeline.fit(x_train, y_train)
        self.is_fitted = True

    def predict(self, text: str) -> SentimentPrediction:
        if not self.is_fitted:
            self.train_from_seed()
        processed = self._normalize_for_model(text)
        if not processed:
            return SentimentPrediction(label="neutral", score=0.0)

        label = str(self.pipeline.predict([processed])[0])
        probabilities = self.pipeline.predict_proba([processed])[0]
        classes = list(self.pipeline.named_steps["clf"].classes_)
        label_index = classes.index(label)
        score = float(probabilities[label_index])
        return SentimentPrediction(label=label, score=score)
