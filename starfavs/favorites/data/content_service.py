import requests
import logging
from typing import Dict
from django.core.cache import cache
from .db_repository import FavoriteRepository
from starfavs.favorites.presentation.types import ResourceConfig, RecordType

logger = logging.getLogger(__name__)


class StarWarsAPIService:
    """Thin client for the external Star Wars API with response caching."""

    BASE_URL = "https://sw-api-rwjfuiltyq-el.a.run.app/api"
    CACHE_TIMEOUT = 3600

    def get_resources(self, resource: str, page: int = 1, search: str = "") -> Dict:
        """Fetch a paginated list for a given resource with caching.

        Args:
            resource: API resource path, e.g. "films", "planets".
            page: Page number to fetch.
            search: Optional search query passed through to the API.

        Returns:
            JSON-like dict with keys: count, next, previous, results.
        """
        cache_key = f"sw_api_{resource}_page_{page}_search_{search or ''}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Cache hit for %s page %s", resource, page)
            return cached_result

        try:
            url = f"{self.BASE_URL}/{resource}/"
            params = {"page": page, "search": search}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data, self.CACHE_TIMEOUT)
            logger.info("Cached %s page %s", resource, page)
            return data
        except requests.RequestException as e:
            logger.error("Error fetching %s from external API: %s", resource, e)
            return {"results": [], "count": 0, "next": None, "previous": None}

    def get_movies(self, page: int = 1, search: str = "") -> Dict:
        return self.get_resources("films", page=page, search=search)

    def get_planets(self, page: int = 1, search: str = "") -> Dict:
        return self.get_resources("planets", page=page, search=search)

    def extract_id_from_url(self, url: str) -> str:
        try:
            return url.rstrip("/").split("/")[-1]
        except Exception:
            return ""

    def get_resource_detail(self, resource: str, external_id: str) -> dict:
        """Fetch a single resource detail by external ID with caching.

        Args:
            resource: API resource path, e.g. "films", "planets".
            external_id: External record ID extracted from API URLs.

        Returns:
            Parsed JSON dict for the resource, or {} if not found/error.
        """
        singular = resource[:-1] if resource.endswith("s") else resource
        cache_key = f"sw_api_{singular}_{external_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        url = f"{self.BASE_URL}/{resource}/{external_id}/"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            cache.set(cache_key, data, self.CACHE_TIMEOUT)
            return data
        except requests.RequestException:
            return {}

    def get_movie_detail(self, external_id: str) -> dict:
        return self.get_resource_detail("films", external_id)

    def get_planet_detail(self, external_id: str) -> dict:
        return self.get_resource_detail("planets", external_id)


class ContentService:
    """
    Combines external API results with the user's favorite records to:
    - override display names (custom titles),
    - mark favorites,
    - support optional search across API pages and user favorites,
    - return a consistent, paginated shape.
    """

    def __init__(self):
        self.api_service = StarWarsAPIService()
        self.favorite_repository = FavoriteRepository()

        self.resource_config_map: dict[str, ResourceConfig] = {
            RecordType.MOVIE: ResourceConfig(
                resource_path="films",
                display_field="title",
                include_release_date=True,
                fetch_page=self.api_service.get_movies,
                fetch_detail=self.api_service.get_movie_detail,
            ),
            RecordType.PLANET: ResourceConfig(
                resource_path="planets",
                display_field="name",
                include_release_date=False,
                fetch_page=self.api_service.get_planets,
                fetch_detail=self.api_service.get_planet_detail,
            ),
        }

    def _normalized_id(self, url: str) -> str:
        external_id = self.api_service.extract_id_from_url(url or "")
        return str(external_id).strip()

    def get_content_with_custom_names(
        self,
        user_id: int,
        record_type: str,
        page: int = 1,
        limit: int = 10,
        search: str | None = None,
    ) -> dict:
        """
        Args:
            user_id: The requesting user ID.
            record_type: "movie" or "planet".
            page: 1-based page index for the response slice.
            limit: Max results to return.
            search: If empty/blank, returns decorated API page. If provided,
                searches across API pages (title/name) and user's favorites,
                merges results, and returns a paginated slice.

        Returns:
            Dict with keys: count, next, previous, results, total_favorites.
        Raises:
            ValueError: If record_type is not supported.
        """
        record_type = (record_type or "").strip().lower()
        if record_type not in {"movie", "planet"}:
            raise ValueError("Unsupported record_type. Expected 'movie' or 'planet'.")

        record_type_key = RecordType(record_type)
        resource_config = self.resource_config_map[record_type_key]

        if not resource_config:
            raise ValueError("Unsupported record_type")

        display_field: str = resource_config.display_field
        fetch_page = resource_config.fetch_page
        fetch_detail = resource_config.fetch_detail
        include_release_date: bool = resource_config.include_release_date
        resource_path: str = resource_config.resource_path

        custom_name_by_id = self.favorite_repository.get_user_custom_names_mapping(
            user_id, record_type
        )
        favorite_ids = self.favorite_repository.get_user_favorited_external_ids(
            user_id, record_type
        )

        def _build_result_item(
            source: dict, external_id: str, display_value: str
        ) -> dict:
            item = {
                display_field: display_value,
                "created": source.get("created", ""),
                "edited": source.get("edited", ""),
                "url": source.get("url", ""),
                "is_favourite": bool(external_id and external_id in favorite_ids),
            }
            if include_release_date:
                item["release_date"] = source.get("release_date", "")
            return item

        if not (search and search.strip()):
            api_page = fetch_page(page)
            results = []
            for obj in api_page.get("results", []):
                external_id = self._normalized_id(obj.get("url", ""))
                display_value = custom_name_by_id.get(
                    external_id, obj.get(display_field, "")
                )
                results.append(_build_result_item(obj, external_id, display_value))
            return {
                "count": api_page.get("count", len(results)),
                "next": api_page.get("next"),
                "previous": api_page.get("previous"),
                "results": results[: max(1, int(limit))],
                "total_favorites": len(favorite_ids),
            }

        search_query = search.strip().lower()
        page = max(1, int(page))
        start_index = (page - 1) * limit
        end_index = start_index + limit

        matched_items: list[dict] = []
        seen_external_ids: set[str] = set()

        current_page = 1
        while True:
            api_page = fetch_page(current_page)
            api_results = api_page.get("results", [])
            if not api_results:
                break

            for obj in api_results:
                external_id = self._normalized_id(obj.get("url", ""))
                if not external_id or external_id in seen_external_ids:
                    continue
                display_value = custom_name_by_id.get(
                    external_id, obj.get(display_field, "")
                )
                if search_query in (display_value or "").lower():
                    matched_items.append(
                        _build_result_item(obj, external_id, display_value)
                    )
                    seen_external_ids.add(external_id)

            if len(matched_items) >= end_index:
                break
            if not api_page.get("next"):
                break
            current_page += 1

        favorite_matches = self.favorite_repository.search_user_favorites(
            user_id, record_type, search_query
        )
        for fav in favorite_matches:
            external_id = str(fav.external_record_id).strip()
            if not external_id or external_id in seen_external_ids:
                continue
            detail = fetch_detail(external_id)
            if not detail:
                continue
            url = (
                detail.get("url")
                or f"{self.api_service.BASE_URL}/{resource_path}/{external_id}/"
            )
            display_value = (fav.custom_title or "").strip() or detail.get(
                display_field, ""
            )
            item = {
                display_field: display_value,
                "created": detail.get("created", ""),
                "edited": detail.get("edited", ""),
                "url": url,
                "is_favourite": True,
            }
            if include_release_date:
                item["release_date"] = detail.get("release_date", "")
            matched_items.append(item)
            seen_external_ids.add(external_id)

        total = len(matched_items)
        paginated_results = matched_items[start_index:end_index]
        return {
            "count": total,
            "next": None,
            "previous": None,
            "results": paginated_results,
            "total_favorites": len(favorite_ids),
        }

    def get_movies_with_custom_names(
        self, user_id: int, page: int = 1, limit: int = 10, search: str | None = None
    ) -> dict:
        return self.get_content_with_custom_names(
            user_id=user_id,
            record_type="movie",
            page=page,
            limit=limit,
            search=search,
        )

    def get_planets_with_custom_names(
        self, user_id: int, page: int = 1, limit: int = 10, search: str | None = None
    ) -> dict:
        return self.get_content_with_custom_names(
            user_id=user_id,
            record_type="planet",
            page=page,
            limit=limit,
            search=search,
        )
