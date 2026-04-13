"""
Pipe-delimited rows: unit_id|property_id|unit_code|property_name|unit_type|vacancy_days|apps
The parser applies a deterministic adjustment so seeded app volume has a realistic spread.
"""

INVENTORY_DEMO_PIPE = """
4706dd37-7ef3-4ce3-9f72-f9701fae067b|596d3791-eb69-4030-9e1b-2e3f9b2ddd09|A-103|Maple Heights|2 BR|6|2
e4102abc-f216-4cbe-9e60-a2eaa67cf1fa|92e9be2c-05e0-4bcc-a646-895ae83dd515|A-104|Cedar Point Apartments|3 BR|8|1
400eab10-fe22-444d-bf8e-257cb4fcf8cc|ec6e19d8-ccee-47bb-9866-13db48ecb8e5|A-106|Lakeside Commons|2 BR|10|5
f5484984-5bea-458f-9ab1-45370dd78261|f7c028a9-af8c-4f60-9a48-467ca4668cfb|A-107|Pine Grove Villas|3 BR|12|5
8078dbf0-973e-43b6-a279-02c285664298|183f7339-e6c7-4d08-9299-422207e91f29|A-108|Grand Central Living|1 BR|14|4
6218bb17-010d-4275-877e-1e444e01497c|39d2e354-9052-4eec-8bbf-0e39948c21ca|A-109|Sunset Ridge|2 BR|16|5
3b146ab2-0ab1-4f7e-95cd-f86c21b6b73f|e6e0e36b-dd01-49e1-99c3-bafde02b5e0e|A-111|Parkside Estates|1 BR|18|4
702c9737-7e4c-49e4-bd80-5e5d9c961c63|f48c0983-006e-4cfa-b0bd-18896b5c6d00|A-112|Highland Square|2 BR|20|2
48c11da2-46d5-4b60-bd8d-8bbe4aed1878|fc705241-30eb-448d-b3a8-416117044176|A-113|Cityline Residences|3 BR|22|4
6d1cfc11-2234-4bfc-81a0-dc29dbc2bd8c|92edec9c-fa8e-4945-88f4-9c9eeaab71bb|A-114|Brookstone Flats|1 BR|24|1
65959425-c1bd-46de-b6a7-781208ded762|fe7c0806-df39-4aa4-8cb5-5fd44975a66e|A-116|Elmwood Court|3 BR|26|1
37e5b03d-295c-4a24-89ca-76b9d2e080f9|ffe230e2-6caf-464c-9568-4aab4f8fb046|A-117|Beacon Hill Towers|1 BR|28|5
afa13298-9d38-4cac-88eb-9a82d7fa5aec|a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6|A-118|The Meridian|2 BR|30|5
f702d151-11f3-4f06-982c-ca7f07e88b94|0a39dc44-b1d6-4c45-9e11-96c6476104e5|A-119|Aurora Place|3 BR|32|4
01737eb9-335d-4731-a638-9dbeba266a32|e3ff8f2a-9d13-46b6-8673-3d99fa5cf949|A-121|Skyline Towers|2 BR|34|2
1fc00df9-a32f-4e68-b5f7-5e419a4a4b84|c5a7fd3a-71be-4895-995f-3700922467d5|A-122|River Lofts|3 BR|36|1
bc81838d-bcd6-445f-b3ef-a532c0ffad6e|596d3791-eb69-4030-9e1b-2e3f9b2ddd09|A-123|Maple Heights|1 BR|38|4
00c4cd06-276a-4fa1-ade3-52b7f3155354|92e9be2c-05e0-4bcc-a646-895ae83dd515|A-124|Cedar Point Apartments|2 BR|40|2
294846d1-52b0-4533-a44e-a564cec8e1bf|ec6e19d8-ccee-47bb-9866-13db48ecb8e5|A-126|Lakeside Commons|1 BR|2|4
6562502b-d2c0-4a58-b582-03c8425f71a2|f7c028a9-af8c-4f60-9a48-467ca4668cfb|A-127|Pine Grove Villas|2 BR|4|5
1da448f4-567d-4499-9a84-702323879248|183f7339-e6c7-4d08-9299-422207e91f29|A-128|Grand Central Living|3 BR|6|5
a31d170e-057d-4167-9a0c-49d3c8f5d4b4|39d2e354-9052-4eec-8bbf-0e39948c21ca|A-129|Sunset Ridge|1 BR|8|4
92cd28ce-b727-42af-b9b5-8e2bd024c58c|e6e0e36b-dd01-49e1-99c3-bafde02b5e0e|A-131|Parkside Estates|3 BR|10|4
fd84019e-80ac-4b25-821a-fdd03df45bec|f48c0983-006e-4cfa-b0bd-18896b5c6d00|A-132|Highland Square|1 BR|12|5
810cf975-2825-48ea-964a-9ad677e53196|c5a7fd3a-71be-4895-995f-3700922467d5|A-102|River Lofts|1 BR|4|4
8c9dc69c-7849-4254-95d4-d5140b3c8d73|fc705241-30eb-448d-b3a8-416117044176|A-133|Cityline Residences|2 BR|14|2
eac476f5-3ddf-4007-8c02-01fd34077509|92edec9c-fa8e-4945-88f4-9c9eeaab71bb|A-134|Brookstone Flats|3 BR|16|1
93158ffc-ed3f-45e2-9acb-fc96eab91231|fe7c0806-df39-4aa4-8cb5-5fd44975a66e|A-136|Elmwood Court|2 BR|18|2
e2647880-e4f6-49e2-86d9-42a954d047b7|ffe230e2-6caf-464c-9568-4aab4f8fb046|A-137|Beacon Hill Towers|3 BR|20|5
73bbe383-003e-431b-a285-9fc6d6296d11|a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6|A-138|The Meridian|1 BR|22|4
""".strip()


def parse_demo_rows():
    rows = []
    for line in INVENTORY_DEMO_PIPE.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        uid, pid, code, pname, utype, days_s, apps_s = parts
        br = utype.split()[0] if utype else "1"
        base_apps = int(apps_s)
        vacancy_days = int(days_s)
        unit_seed = abs(hash(uid.strip())) % 5
        # Realistic pattern: newer vacancies trend more activity; older ones taper off,
        # with deterministic variance so not every unit in the same bucket looks identical.
        if vacancy_days <= 10:
            adjusted_apps = base_apps + 2 + (unit_seed % 2)
        elif vacancy_days <= 20:
            adjusted_apps = base_apps + 1
        elif vacancy_days <= 30:
            adjusted_apps = max(1, base_apps)
        else:
            adjusted_apps = max(0, base_apps - 1 - (unit_seed % 2))

        rows.append(
            {
                "unit_id": uid.strip(),
                "property_id": pid.strip(),
                "unit_code": code.strip(),
                "property_name": pname.strip(),
                "bedrooms": br,
                "vacancy_days": vacancy_days,
                "apps": adjusted_apps,
                "tours": 5,
            }
        )
    return rows
