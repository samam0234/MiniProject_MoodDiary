from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    """모든 응답을 ``{"success": bool, "data": ..., "error": ...}`` 로 감싼다."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        status_code = response.status_code if response is not None else 200

        if status_code == 204:
            return b""
        if status_code >= 400:
            payload = {"success": False, "data": None, "error": data}
        else:
            payload = {"success": True, "data": data, "error": None}
        return super().render(payload, accepted_media_type, renderer_context)
