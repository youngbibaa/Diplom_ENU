import math


def calculate_growth_rate(current_mentions: int, previous_mentions: int) -> float:
    if current_mentions <= 0:
        return -1.0 if previous_mentions > 0 else 0.0

    if previous_mentions == 0:
        return 0.0

    growth_rate = (current_mentions - previous_mentions) / previous_mentions

    return max(min(growth_rate, 2.0), -1.0)


def calculate_trend_score(
    mentions_count: int,
    growth_rate: float,
    sentiment_avg: float,
) -> float:
    volume_component = math.log1p(mentions_count) * 12

    growth_component = growth_rate * 8

    sentiment_component = sentiment_avg * 4

    score = volume_component + growth_component + sentiment_component

    return round(max(score, 0.0), 4)