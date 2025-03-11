from typing import Any
from django.core.handlers.asgi import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.views.generic import TemplateView
from django.urls import get_resolver, URLPattern


class APIView(TemplateView):
    template_name = "api/api.html"

    def get_api_endpoints(self, request: HttpRequest) -> list[dict[str, str]] | None:
        """Fetch all routes under /api/ and their corresponding views"""

        _, api_resolver = get_resolver().namespace_dict.get("api", (None, None))
        if api_resolver is None:
            return

        def should_add_endpoint(pattern: URLPattern) -> bool:
            url_name = pattern.name or ""
            callback_name = pattern.callback.__name__
            return (
                "-list" in url_name
                and "search" not in url_name
                and "PublicAPIViewSet" in callback_name
            )

        def map_pattern_to_endpoint_dict(pattern: URLPattern) -> dict[str, str]:
            url_name = pattern.name
            callback_name = pattern.callback.__name__
            return {
                "name": callback_name.replace("PublicAPIViewSet", ""),
                "url": api_resolver.reverse(url_name),
            }

        return sorted(
            [
                map_pattern_to_endpoint_dict(pattern)
                for pattern in api_resolver.url_patterns
                if should_add_endpoint(pattern)
            ],
            key=lambda x: x["name"],
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["endpoints"] = self.get_api_endpoints(self.request)

        _, api_resolver = get_resolver().namespace_dict.get("api", (None, None))
        context["resolver"] = api_resolver

        return context
