"""Single source of truth for locations used in SnowPredict.

Any change here must be logged in docs/DECISIONS.md. Coordinates/elevations of SNOTEL stations are
NOT typed in by hand — they are read from the SNOTEL station metadata (see notebook 01, §3).
"""

# Ski-area reference points (approx. base-area coordinates, used only for distances / labels).
SKI_AREAS = {
    "Aspen Mountain":   (39.1861, -106.8182),
    "Aspen Highlands":  (39.1817, -106.8556),
    "Buttermilk":       (39.2052, -106.8608),
    "Snowmass":         (39.2084, -106.9490),
    "St. Anton (AT)":   (47.1300,   10.2700),   # original proposal; used for Open-Meteo-only probes
}

# Candidate SNOTEL stations examined in notebook 01 (triplet -> group label).
# Aspen-area = all active stations within ~40 km of Aspen town; others = stations on/next to resorts.
CANDIDATE_STATIONS = {
    # Aspen area (D-003)
    "542:CO:SNTL": "Aspen area",   # Independence Pass
    "556:CO:SNTL": "Aspen area",   # Kiln
    "369:CO:SNTL": "Aspen area",   # Brumley
    "547:CO:SNTL": "Aspen area",   # Ivanhoe
    "658:CO:SNTL": "Aspen area",   # Nast Lake
    "737:CO:SNTL": "Aspen area",   # Schofield Pass
    "669:CO:SNTL": "Aspen area",   # North Lost Trail
    "380:CO:SNTL": "Aspen area",   # Butte (Crested Butte)
    "1101:CO:SNTL": "Aspen area",  # Chapman Tunnel
    "1141:CO:SNTL": "Aspen area",  # Upper Taylor
    # Other resorts (contrast snow climates)
    "842:CO:SNTL": "Vail",
    "415:CO:SNTL": "Copper Mountain",
    "766:UT:SNTL": "Snowbird",
    "366:UT:SNTL": "Brighton",
    "814:UT:SNTL": "Park City (Thaynes Canyon)",
    "784:CA:SNTL": "Palisades Tahoe",
    "518:CA:SNTL": "Heavenly",
    "590:MT:SNTL": "Big Sky (Lone Mountain)",
    "791:WA:SNTL": "Stevens Pass",
    "1082:WY:SNTL": "Grand Targhee",
}

SNOTEL_ELEMENTS = ["SNWD", "WTEQ", "TAVG", "TMAX", "TMIN", "PREC", "PRCP"]
SNOTEL_PERIOD = ("1978-10-01", "2026-07-31")

# ---- FINAL modelling resorts (D-007, D-008; decided 2026-11-10) ------------------------------------
# One model per resort. Target = measured SNOTEL snow depth (D-005); evaluation on measured, non-imputed days only.
# Aspen is a FIXED-membership composite (mean of members on days ALL members are present, else NaN) so the
# composition never changes over time; Kiln + Brumley are the only Aspen-area stations with every winter 2004–2026.
RESORTS = {
    "Aspen":    {"stations": ["556:CO:SNTL", "369:CO:SNTL"], "first_winter": 2004, "climate": "continental (CO)"},
    "Brighton": {"stations": ["366:UT:SNTL"],                "first_winter": 1998, "climate": "intermountain (UT)"},
    "Heavenly": {"stations": ["518:CA:SNTL"],                "first_winter": 2000, "climate": "Sierra, lee side of Tahoe (CA)"},
}
LAST_WINTER = 2026
