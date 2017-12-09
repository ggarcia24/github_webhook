import datetime
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import WebhookTransaction


@csrf_exempt
@require_POST
def webhook(request):
    jsondata = request.body.decode('utf-8')
    data = json.loads(jsondata)
    # Obtain all the metadata that are string
    meta = {k: v for k, v in request.META.items() if isinstance(v, str)}

    WebhookTransaction.objects.create(
        date_generated=data['pull_request']['created_at'],
        body=json.dumps(data),
        request_meta=json.dumps(meta)
    )

    return HttpResponse(status=200)
