INDEX_WEIGHTS = {
    "marketConfidence": {
        "sp500Momentum": 0.25,
        "nasdaqMomentum": 0.20,
        "bonds": 0.15,
        "gold": 0.10,
        "housing": 0.10,
        "inflation": 0.20,
    },
    "riskAppetite": {
        "nasdaqMomentum": 0.25,
        "techMomentum": 0.25,
        "btcMomentum": 0.30,
        "polymarketEquities": 0.20,
    },
    "macroStability": {
        "inflation": 0.3,
        "housing": 0.2,
        "bondsCurve": 0.2,          # placeholder for yield curve logic
        "polymarketRates": 0.3,
    },
}
