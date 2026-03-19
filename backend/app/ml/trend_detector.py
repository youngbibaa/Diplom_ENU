"""
trend_detector.py
=================
Расчёт метрик тренда для тем по временным срезам.

Метрики
-------
growth_rate  : относительный прирост упоминаний [-1.0, +2.0]
trend_score  : взвешенная сумма volume + growth + sentiment [0, ∞)

Формула trend_score:
  volume_component    = log(1 + mentions) × 12   — объём (логарифмическая шкала)
  growth_component    = growth_rate × 8           — динамика роста
  sentiment_component = sentiment_avg × 4         — эмоциональный фон

Коэффициенты подобраны так, чтобы объём доминировал, но рост и
тональность заметно влияли на итоговую позицию темы.
"""

import math


def calculate_growth_rate(current_mentions: int, previous_mentions: int) -> float:
    """
    Вычисляет относительный прирост упоминаний.

    Граничные случаи
    ----------------
    current == 0, previous > 0  → тема исчезла      → -1.0
    current > 0,  previous == 0 → новая тема         → +0.5 (умеренно позитивный сигнал)
    оба == 0                    → тема не активна    →  0.0

    Диапазон: [-1.0, +2.0] — клиппинг убирает экстремальные выбросы.
    """
    if current_mentions <= 0:
        return -1.0 if previous_mentions > 0 else 0.0

    if previous_mentions == 0:
        # Тема появилась впервые — даём умеренно-позитивный сигнал
        # вместо нуля (0.0 раньше делало новые темы "мёртвыми")
        return 0.5

    growth_rate = (current_mentions - previous_mentions) / previous_mentions
    return round(max(min(growth_rate, 2.0), -1.0), 4)


def calculate_trend_score(
    mentions_count: int,
    growth_rate: float,
    sentiment_avg: float,
) -> float:
    """
    Вычисляет итоговый trend_score.

    Параметры
    ---------
    mentions_count : число упоминаний темы за период
    growth_rate    : относительный прирост (из calculate_growth_rate)
    sentiment_avg  : средний signed sentiment score [-1.0, +1.0]

    Возвращает
    ----------
    float ≥ 0.0, округлённый до 4 знаков
    """
    volume_component = math.log1p(mentions_count) * 12
    growth_component = growth_rate * 8
    sentiment_component = sentiment_avg * 4

    score = volume_component + growth_component + sentiment_component
    return round(max(score, 0.0), 4)
