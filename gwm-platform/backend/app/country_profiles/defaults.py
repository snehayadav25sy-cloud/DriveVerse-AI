# Default configuration maps for country profile engines

# Mapping from semantic vehicle classes to lists of CARLA 0.9.16 blueprint IDs
DEFAULT_BLUEPRINT_MAP = {
    "sedan": [
        "vehicle.audi.a2",
        "vehicle.tesla.model3",
        "vehicle.lincoln.mkz_2017",
        "vehicle.lincoln.mkz_2020",
        "vehicle.toyota.prius",
        "vehicle.seat.leon",
        "vehicle.citroen.c3",
        "vehicle.nissan.micra"
    ],
    "suv": [
        "vehicle.nissan.patrol",
        "vehicle.nissan.patrol_2021",
        "vehicle.jeep.wrangler_rubicon"
    ],
    "sports": [
        "vehicle.audi.tt",
        "vehicle.ford.mustang",
        "vehicle.chevrolet.impala",
        "vehicle.dodge.charger_2020",
        "vehicle.mercedes.coupe",
        "vehicle.mercedes.coupe_2020"
    ],
    "van": [
        "vehicle.volkswagen.t2",
        "vehicle.volkswagen.t2_2021",
        "vehicle.mercedes.sprinter"
    ],
    "truck": [
        "vehicle.carlamotors.carlacola"
    ],
    "hgv": [
        "vehicle.carlamotors.european_hgv"
    ],
    "motorcycle": [
        "vehicle.harley-davidson.low_rider",
        "vehicle.yamaha.yzf",
        "vehicle.kawasaki.ninja"
    ],
    "scooter": [
        "vehicle.vespa.zx125"
    ],
    "bicycle": [
        "vehicle.bh.crossbike",
        "vehicle.gazelle.omafiets",
        "vehicle.diamondback.century"
    ],
    "bus": [
        "vehicle.mitsubishi.fusorosa"
    ],
    "micro": [
        "vehicle.micro.microlino"
    ],
    "police": [
        "vehicle.dodge.charger_police",
        "vehicle.dodge.charger_police_2020"
    ],
    "ambulance": [
        "vehicle.ford.ambulance"
    ],
    "firetruck": [
        "vehicle.carlamotors.firetruck"
    ]
}

# Mapping from semantic building classes to static prop categories in CARLA
DEFAULT_ASSET_MAP = {
    "residential": ["Static.Building.Residential", "Static.Building.House"],
    "commercial": ["Static.Building.Office", "Static.Building.Commercial", "Static.Building.Store"],
    "industrial": ["Static.Building.Warehouse", "Static.Building.Industrial"],
    "hospital": ["Static.Building.Hospital", "Static.Building.Public"],
    "school": ["Static.Building.School", "Static.Building.Public"],
    "temple": ["Static.Building.Church", "Static.Building.Historic", "Static.Building.Public"],
    "church": ["Static.Building.Church", "Static.Building.Historic", "Static.Building.Public"],
    "mosque": ["Static.Building.Church", "Static.Building.Historic", "Static.Building.Public"],
    "monument": ["Static.Prop.Monument", "Static.Building.Historic"]
}

# Sign language conventions per country
DEFAULT_SIGN_CONVENTIONS = {
    "india": {"language": "en", "convention": "IRC"},
    "usa": {"language": "en", "convention": "MUTCD"},
    "japan": {"language": "ja", "convention": "Japan Road Signs"},
    "dubai": {"language": "ar/en", "convention": "UAE Road Signs"},
    "germany": {"language": "de", "convention": "StVO"},
    "uk": {"language": "en", "convention": "TSRGD"}
}
