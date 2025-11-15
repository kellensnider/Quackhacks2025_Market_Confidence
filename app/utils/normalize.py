def normalize_to_score(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min/max and scale to 0–100.
    """
    if max_val == min_val:
        return 50.0
    clamped = max(min_val, min(max_val, value))
    norm = (clamped - min_val) / (max_val - min_val)
    return norm * 100.0