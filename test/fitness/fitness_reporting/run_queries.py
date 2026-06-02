import json
from common.fitness.analytics.query import AFCAnalyticsRepository

DB_PATH = "afc_analytics.sqlite"
#MEMBER_ID = "1e0f8c1b-913d-41a1-91bd-71e3e096e989"
MEMBER_ID = "70a14cf9-834d-4a9b-a266-95f1c1a772e6"

repo = AFCAnalyticsRepository(DB_PATH)

result = repo.member_dashboard_summary(MEMBER_ID)

# write the output to a json file
with open('member_dashboard_summary.json', 'w') as f:
    json.dump(result, f, indent=4)

