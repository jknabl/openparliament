import re

from django.conf import settings
from django.core.serializers.json import simplejson as json
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View

class JSONView(View):
    """Base view that serializes responses as JSON."""

    # Subclasses: set this to True to allow JSONP (cross-domain) requests
    allow_jsonp = False

    def __init__(self):
        super(JSONView,self).__init__()
        self.content_type = 'application/json'

    def dispatch(self, request, *args, **kwargs):
        result = super(JSONView, self).dispatch(request, *args, **kwargs)
        indent_response = 4 if request.GET.get('indent') else None

        if isinstance(result, HttpResponse):
            return result
        resp = HttpResponse(content_type=self.content_type)
        callback = ''
        if self.allow_jsonp and 'callback' in request.GET:
            callback = re.sub(r'[^a-zA-Z0-9_]', '', request.GET['callback'])
            resp.write(callback + '(')
        json.dump({'status': 'ok', 'content': result}, resp, indent=indent_response)
        if callback:
            resp.write(');')

        if settings.DEBUG and 'html' in request.GET:
            resp = HttpResponse('<html><body>' + resp.content + '</body></html>')
        return resp

    def login_required(self):
        resp = HttpResponse('Login required', content_type='text/plain')
        resp.status_code = 403
        resp['X-OP-Login-Required'] = 'yep'
        return resp

    def redirect(self, url):
        return AjaxRedirectResponse(url)

    def custom_response(self, status, content, content_key='content', status_code=200):
        resp = HttpResponse(content_type=self.content_type)
        resp.status_code = status_code
        json.dump({
            'status': status,
            content_key: content
        }, resp)
        return resp

    def dispatch_error(self, error_messages):
        return self.custom_response(
            status='error',
            content=error_messages,
            content_key='errors'
        )


class AjaxRedirectResponse(HttpResponse):

    def __init__(self, url, status_code=403):
        super(AjaxRedirectResponse, self).__init__(
            '<script>window.location.href = "%s";</script>' % url,
            content_type='text/html'
        )
        self.status_code = status_code
        self['X-OP-Redirect'] = url


def adaptive_redirect(request, url):
    if request.is_ajax():
        return AjaxRedirectResponse(url)
    return HttpResponseRedirect(url)
