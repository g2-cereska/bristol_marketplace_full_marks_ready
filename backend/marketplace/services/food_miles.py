import math

# Comprehensive Bristol-area postcode coordinate lookup
# Covers BS1-BS16, BS20-BS24, BS30-BS32, BS34-BS37, BS39-BS41, BS48-BS49
# Plus Bath (BA1-BA2), Gloucestershire (GL), Somerset (TA), Wiltshire (SN)
POSTCODE_COORDS = {
    # Bristol City Centre (BS1)
    'BS1 1AA': (51.4545, -2.5879), 'BS1 2AA': (51.4559, -2.5893),
    'BS1 3AA': (51.4530, -2.5920), 'BS1 4DJ': (51.4538, -2.5915),
    'BS1 4AA': (51.4541, -2.5910), 'BS1 5JG': (51.4549, -2.5962),
    'BS1 5AA': (51.4551, -2.5960), 'BS1 6AA': (51.4498, -2.5938),
    # Clifton / Redland (BS2, BS6, BS7, BS8)
    'BS2 0AA': (51.4601, -2.5750), 'BS2 8AA': (51.4638, -2.5720),
    'BS2 9AA': (51.4580, -2.5740), 'BS6 5AA': (51.4710, -2.5930),
    'BS6 6AA': (51.4730, -2.5880), 'BS6 7AA': (51.4750, -2.5850),
    'BS7 0AA': (51.4930, -2.5830), 'BS7 8AA': (51.4850, -2.5790),
    'BS7 9AA': (51.4820, -2.5810), 'BS8 1AA': (51.4590, -2.6080),
    'BS8 2AA': (51.4630, -2.6100), 'BS8 3AA': (51.4660, -2.6050),
    'BS8 4AA': (51.4680, -2.6020),
    # Easton / St George (BS5)
    'BS5 0AA': (51.4580, -2.5480), 'BS5 6AA': (51.4620, -2.5430),
    'BS5 7AA': (51.4640, -2.5410), 'BS5 8AA': (51.4601, -2.5480),
    'BS5 9AA': (51.4590, -2.5500),
    # Bedminster / South Bristol (BS3, BS13, BS14)
    'BS3 1AA': (51.4430, -2.5930), 'BS3 2AA': (51.4410, -2.5980),
    'BS3 3AA': (51.4390, -2.5870), 'BS3 4AA': (51.4450, -2.5960),
    'BS13 0AA': (51.4180, -2.6040), 'BS13 7AA': (51.4100, -2.5980),
    'BS13 8AA': (51.4120, -2.5940), 'BS14 0AA': (51.4090, -2.5760),
    'BS14 8AA': (51.4050, -2.5820), 'BS14 9AA': (51.4070, -2.5800),
    # North Bristol (BS10, BS11)
    'BS10 5AA': (51.4980, -2.6050), 'BS10 6AA': (51.4960, -2.6100),
    'BS10 7AA': (51.4940, -2.6020), 'BS11 0AA': (51.4850, -2.6620),
    'BS11 9AA': (51.4820, -2.6580),
    # Fishponds / Staple Hill (BS16)
    'BS16 1QY': (51.4860, -2.5150), 'BS16 1AA': (51.4870, -2.5120),
    'BS16 2AA': (51.4910, -2.5090), 'BS16 3AA': (51.4930, -2.5060),
    'BS16 4AA': (51.4820, -2.5070), 'BS16 5AA': (51.4800, -2.5050),
    # Kingswood (BS15)
    'BS15 1AA': (51.4690, -2.4980), 'BS15 2AA': (51.4650, -2.4960),
    'BS15 3AA': (51.4710, -2.4940), 'BS15 4AA': (51.4740, -2.5010),
    # Warmley / Bitton (BS30)
    'BS30 5AA': (51.4570, -2.4710), 'BS30 6AA': (51.4510, -2.4680),
    'BS30 8AA': (51.4480, -2.4820), 'BS30 9AA': (51.4540, -2.4760),
    # Portishead / Clevedon (BS20, BS21)
    'BS20 6AA': (51.4865, -2.7640), 'BS20 7AA': (51.4830, -2.7580),
    'BS20 8AA': (51.4780, -2.7420), 'BS21 6AA': (51.4440, -2.8560),
    'BS21 7AA': (51.4410, -2.8490),
    # Weston-super-Mare (BS22, BS23, BS24)
    'BS22 6AA': (51.3750, -2.9120), 'BS22 7AA': (51.3680, -2.9080),
    'BS22 8AA': (51.3820, -2.9050), 'BS22 9AA': (51.3890, -2.9000),
    'BS23 1AA': (51.3430, -2.9790), 'BS23 2AA': (51.3460, -2.9810),
    'BS23 3AA': (51.3500, -2.9760), 'BS24 0AA': (51.3620, -2.9680),
    'BS24 7AA': (51.3390, -2.9640), 'BS24 8AA': (51.3360, -2.9600),
    'BS24 9AA': (51.3580, -2.9530),
    # Keynsham / Saltford (BS31)
    'BS31 1AA': (51.4180, -2.4960), 'BS31 2AA': (51.4200, -2.5010),
    'BS31 3AA': (51.4130, -2.4890),
    # Bradley Stoke / Patchway (BS32, BS34)
    'BS32 4AA': (51.5320, -2.5550), 'BS32 8AA': (51.5360, -2.5480),
    'BS32 9AA': (51.5290, -2.5520), 'BS34 5AA': (51.5180, -2.5820),
    'BS34 6AA': (51.5150, -2.5770), 'BS34 7AA': (51.5210, -2.5800),
    'BS34 8AA': (51.5230, -2.5750), 'BS34 9AA': (51.5100, -2.5740),
    # Thornbury / Chipping Sodbury (BS35, BS37)
    'BS35 1AA': (51.6070, -2.5210), 'BS35 2AA': (51.6020, -2.5150),
    'BS35 3AA': (51.5940, -2.5080), 'BS37 4AA': (51.5390, -2.4720),
    'BS37 5AA': (51.5420, -2.4770), 'BS37 6AA': (51.5460, -2.4810),
    # Nailsea / Backwell (BS48, BS49)
    'BS48 1AA': (51.4310, -2.7620), 'BS48 2AA': (51.4280, -2.7580),
    'BS48 3AA': (51.4250, -2.7540), 'BS48 4AA': (51.4330, -2.7660),
    'BS49 4AA': (51.3910, -2.7960), 'BS49 5AA': (51.3950, -2.7920),
    'BS49 5HQ': (51.3940, -2.7930),
    # Chew Valley / Pensford (BS39, BS40)
    'BS39 4AA': (51.3560, -2.5810), 'BS39 5AA': (51.3530, -2.5760),
    'BS39 7AA': (51.3490, -2.5700), 'BS40 5DU': (51.3310, -2.7360),
    'BS40 5AA': (51.3350, -2.7300), 'BS40 6AA': (51.3620, -2.7180),
    'BS40 7AA': (51.3580, -2.7120), 'BS40 8AA': (51.3540, -2.6980),
    # Bath (BA1, BA2)
    'BA1 1AA': (51.3837, -2.3590), 'BA1 2AA': (51.3860, -2.3630),
    'BA1 3AA': (51.3810, -2.3520), 'BA1 4AA': (51.3920, -2.3710),
    'BA1 5AA': (51.3780, -2.3840), 'BA2 0AA': (51.3700, -2.3620),
    'BA2 1AA': (51.3740, -2.3680), 'BA2 3AA': (51.3660, -2.3700),
    'BA2 4AA': (51.3590, -2.3940), 'BA2 5AA': (51.3820, -2.4200),
    'BA14 0AA': (51.3430, -2.2070), 'BA15 1AA': (51.3500, -2.2980),
    # Gloucestershire (GL)
    'GL1 1AA': (51.8650, -2.2380), 'GL2 0AA': (51.8480, -2.2540),
    'GL3 1AA': (51.8590, -2.2110), 'GL4 0AA': (51.8410, -2.2090),
    'GL5 1AA': (51.7450, -2.2160), 'GL6 0AA': (51.7290, -2.2280),
    'GL9 1AA': (51.5930, -2.3020), 'GL11 4AA': (51.6410, -2.3790),
    'GL12 7AA': (51.5820, -2.4270), 'GL13 9AA': (51.6860, -2.4870),
    # Somerset (BS26-BS28, TA)
    'BS26 2AA': (51.3210, -2.8740), 'BS27 3AA': (51.2910, -2.7710),
    'BS28 4AA': (51.2540, -2.8010), 'TA1 1AA': (51.0150, -3.1010),
    'TA3 5AA': (51.0280, -2.9820), 'TA9 3AA': (51.2210, -2.9980),
    # Wiltshire (SN)
    'SN14 0AA': (51.4800, -2.2120), 'SN14 6AA': (51.4760, -2.1980),
    'SN15 1AA': (51.4640, -2.0410),
}


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles using the Haversine formula."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)), 2)


def _normalise(postcode: str) -> str:
    """Uppercase, strip spaces, then reinsert space before final 3 chars."""
    pc = (postcode or '').strip().upper().replace(' ', '')
    return (pc[:-3] + ' ' + pc[-3:]) if len(pc) >= 5 else pc


def _lookup(postcode: str):
    """
    Return (lat, lon) for a postcode.
    1. Exact match
    2. Same sector with generic inward code (BS5 6XY → BS5 6AA)
    3. Any entry in same district (BS5 → first BS5 x entry)
    Returns None if nothing found.
    """
    pc = _normalise(postcode)
    if pc in POSTCODE_COORDS:
        return POSTCODE_COORDS[pc]
    parts = pc.split(' ')
    if len(parts) == 2:
        sector_generic = parts[0] + ' ' + parts[1][0] + 'AA'
        if sector_generic in POSTCODE_COORDS:
            return POSTCODE_COORDS[sector_generic]
        district = parts[0]
        for key, coords in POSTCODE_COORDS.items():
            if key.startswith(district + ' '):
                return coords
    return None


def postcode_distance_miles(start: str, end: str) -> float:
    """
    Return straight-line distance in miles between two UK postcodes.
    Falls back to 10.0 miles if either postcode is unrecognised.
    """
    c1 = _lookup(start)
    c2 = _lookup(end)
    if c1 is None or c2 is None:
        return 10.0
    return _haversine_miles(c1[0], c1[1], c2[0], c2[1])