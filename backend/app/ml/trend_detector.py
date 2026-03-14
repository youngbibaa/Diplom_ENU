class TrendCalculator:
    @staticmethod
    def growth_rate(current_mentions: int, previous_mentions: int) -> float:
        if previous_mentions == 0:
            return float(current_mentions)
        return (current_mentions - previous_mentions) / previous_mentions

    @staticmethod
    def trend_score(mentions_count: int, growth_rate: float, sentiment_avg: float) -> float:
        return float(mentions_count * (1 + growth_rate) + sentiment_avg)
