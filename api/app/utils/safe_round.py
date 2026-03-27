def safe_round(val, precision=1):
    return round(float(val), precision) if val is not None else None