from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


TRAIN_TEXTS = [
    # positive EN
    "markets recover after positive economic agreement",
    "peace talks show progress and tensions are easing",
    "the company reported strong growth and better results",
    "new support package improves the situation significantly",
    "scientists announced a breakthrough and optimistic outlook",
    "the reform was welcomed by investors and citizens",
    "cooperation between countries improved regional stability",
    "the new policy brings development and opportunity",
    "production increased and the outlook is positive",
    "the agreement was successful and reduced risks",
    # neutral EN
    "officials said the meeting is scheduled for thursday",
    "the report describes the current political situation",
    "the government published a new statement today",
    "the article explains how the new law works",
    "the president met with ministers in the capital",
    "the company released its quarterly report",
    "analysts discussed the possible scenarios for next year",
    "the news covers events in the middle east",
    "the committee presented a formal recommendation",
    "the document contains updated operational data",
    # negative EN
    "war escalates and civilians are killed in attacks",
    "oil prices surge amid crisis and growing fear",
    "the economy weakens as conflict spreads",
    "the company reported losses and declining demand",
    "missile strikes caused damage and panic",
    "investors fear recession and further instability",
    "the attack increased risks across the region",
    "the situation worsened after another deadly strike",
    "the market fell sharply because of uncertainty",
    "the crisis deepened and confidence collapsed",

    # positive RU
    "рынок восстановился после позитивных новостей",
    "переговоры завершились успешно и напряженность снизилась",
    "компания показала сильный рост и хорошие результаты",
    "новая программа поддержки улучшила ситуацию",
    "ученые сообщили о прорыве и хорошем прогнозе",
    "реформа была встречена положительно инвесторами",
    "сотрудничество стран укрепило стабильность в регионе",
    "новая политика создает возможности для развития",
    "производство выросло и прогноз остается положительным",
    "соглашение оказалось успешным и снизило риски",
    # neutral RU
    "официальные лица сообщили о встрече в четверг",
    "в отчете описывается текущая политическая ситуация",
    "правительство опубликовало новое заявление",
    "статья объясняет как работает новый закон",
    "президент встретился с министрами в столице",
    "компания выпустила квартальный отчет",
    "аналитики обсудили возможные сценарии на следующий год",
    "новость посвящена событиям на ближнем востоке",
    "комитет представил формальную рекомендацию",
    "документ содержит обновленные данные",
    # negative RU
    "война усиливается и мирные жители погибают",
    "цены на нефть растут на фоне кризиса и страха",
    "экономика слабеет из за конфликта",
    "компания сообщила об убытках и падении спроса",
    "ракетные удары вызвали разрушения и панику",
    "инвесторы опасаются рецессии и нестабильности",
    "атака усилила риски в регионе",
    "ситуация ухудшилась после нового удара",
    "рынок резко упал из за неопределенности",
    "кризис углубился и доверие снизилось",
]

TRAIN_LABELS = (
    ["positive"] * 10
    + ["neutral"] * 10
    + ["negative"] * 10
    + ["positive"] * 10
    + ["neutral"] * 10
    + ["negative"] * 10
)


@lru_cache
def get_sentiment_pipeline() -> Pipeline:
    features = FeatureUnion(
        [
            (
                "word_tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    sublinear_tf=True,
                    ngram_range=(1, 2),
                    min_df=1,
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
                ),
            ),
        ]
    )

    pipeline.fit(TRAIN_TEXTS, TRAIN_LABELS)
    return pipeline


def predict_sentiment(text: str) -> tuple[str, float]:
    text = (text or "").strip()
    if not text:
        return "neutral", 0.0

    pipeline = get_sentiment_pipeline()

    probabilities = pipeline.predict_proba([text])[0]
    classes = pipeline.named_steps["classifier"].classes_

    proba_by_label = {
        label: float(prob)
        for label, prob in zip(classes, probabilities)
    }

    positive_proba = proba_by_label.get("positive", 0.0)
    negative_proba = proba_by_label.get("negative", 0.0)
    neutral_proba = proba_by_label.get("neutral", 0.0)

    label = max(proba_by_label, key=proba_by_label.get)
    signed_score = round(positive_proba - negative_proba, 4)

    if abs(signed_score) < 0.10 and neutral_proba >= max(positive_proba, negative_proba):
        label = "neutral"

    return label, signed_score