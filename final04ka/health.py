import time, secrets, datetime
from django.http import JsonResponse

START_TS = time.time()
INSTANCE_ID = secrets.token_hex(4)
STARTED_AT = datetime.datetime.now(datetime.timezone.utc)

def health(request):
    data = {
        "status": "I am up!",
        "instance_id": INSTANCE_ID,
        "started_at": STARTED_AT,
        "uptime_s": int(time.time() - START_TS),
    }
    resp = JsonResponse(data)
    resp["X-Instance"] = INSTANCE_ID
    resp["X-Started-At"] = STARTED_AT
    return resp