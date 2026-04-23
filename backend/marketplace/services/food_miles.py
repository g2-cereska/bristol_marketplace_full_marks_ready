POSTCODE_COORDS = {
    'BS1 4DJ': (51.4538, -2.5915),
    'BS1 5JG': (51.4549, -2.5962),
    'BS5 8AA': (51.4601, -2.5480),
    'BS16 1QY': (51.4860, -2.5150),
    'BS40 5DU': (51.3310, -2.7360),
}


def postcode_distance_miles(start: str, end: str) -> float:
    start = (start or '').strip().upper()
    end = (end or '').strip().upper()
    if start not in POSTCODE_COORDS or end not in POSTCODE_COORDS:
        return 10.0
    lat1, lon1 = POSTCODE_COORDS[start]
    lat2, lon2 = POSTCODE_COORDS[end]
    distance = (((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5) * 55
    return round(distance, 2)
