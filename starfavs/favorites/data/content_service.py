import requests
import logging
from typing import Dict
from django.core.cache import cache
from .db_repository import FavoriteRepository
from starfavs.favorites.presentation.types import ResourceConfig, RecordType ,ContentItem ,ContentListResponse

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
    ) -> ContentListResponse:
        """
        Args:
            user_id: The requesting user ID.
            record_type: "movie" or "planet".
            page: 1-based page index for the response slice.
            search: If empty/blank, returns decorated API page. If provided,
                searches across API pages (title/name) and user's favorites,
                merges results, and returns a paginated slice.

        Returns:
            Dict with keys: count, next, previous, results, total_favorites.
        Raises:
            ValueError: If record_type is not supported.
        
        TODO: Limit is always 10. This functionality needs to be dynamic.
        """
        
        record_type_key = RecordType(record_type)
        resource_config = self.resource_config_map[record_type_key]

        if not resource_config:
            raise ValueError("Unsupported record_type")

        # Get the resource config for the record type
        display_field: str = resource_config.display_field
        fetch_page = resource_config.fetch_page
        fetch_detail = resource_config.fetch_detail
        include_release_date: bool = resource_config.include_release_date
        resource_path: str = resource_config.resource_path

        # Get the user favorites for the record type
        user_favorites = self.favorite_repository.get_user_favorites(
            user_id=user_id, record_type=record_type
        )

        # Get the external ID to custom title mapping
        favorite_lookup = {
            str(f.external_record_id).strip(): (
                f.custom_title.strip() if f.custom_title else ""
            )
            for f in user_favorites
        }

        """Helper functions for the content service """

        # Function to get the display value for the item
        def _get_display_label_value(
            source_data: dict, external_id: str, custom_title: str = None
        ) -> str:
            """Get display value, Add's custom title over original name."""
            if custom_title is None:
                custom_title = favorite_lookup.get(external_id, "")

            if custom_title and custom_title.strip():
                return custom_title.strip()

            return source_data.get(display_field, "")

        def _get_item_display_value(item: ContentItem) -> str:
            """Get the display value from a ContentItem based on record type."""
            if display_field == "title":
                return item.title or ""
            else:  # display_field == "name"
                return item.name or ""

        # Function to build the item for the response
        def _build_item(
            source_data: dict,
            external_id: str,
            custom_title: str = None,
            url: str = None,
        ) -> ContentItem:
            """Build a standardized result item for planet or movie."""

            # Get display value for the item
            display_value = _get_display_label_value(
                source_data, external_id, custom_title
            )

            item = {
                "created": source_data.get("created", ""),
                "edited": source_data.get("edited", ""),
                "url": url or source_data.get("url", ""),
                "is_favourite": bool(
                    external_id and external_id in favorite_lookup
                ),
            }

            if display_field == "title":
                item["title"] = display_value
                if include_release_date:
                    item["release_date"] = source_data.get("release_date", "")
            else:
                item["name"] = display_value

            return ContentItem(**item)

        # Function to check if the item matches the search criteria
        def _should_include_in_search(display_value: str, search_query: str) -> bool:
            """Check if item matches search criteria."""
            return search_query in (display_value or "").lower()

        # Function to add the item to the results if it matches the search criteria
        def _add_to_results_if_query_matches(
            item: dict,
            display_value: str,
            external_id: str,
            search_query: str,
            matched_items: list,
            seen_ids: set,
        ):
            """Add item to results if it matches search and hasn't been seen."""
            if _should_include_in_search(display_value, search_query):
                matched_items.append(item)
                seen_ids.add(external_id)

        if not (search and search.strip()):
            api_page = fetch_page(page)
            results = []
            for obj in api_page.get("results", []):
                external_id = self._normalized_id(obj.get("url", ""))
                results.append(_build_item(obj, external_id))

            return ContentListResponse(
                count=api_page.get("count", len(results)),
                next=api_page.get("next"),
                previous=api_page.get("previous"),
                results=results[: max(1, int(limit))],
                total_favorites=len(favorite_lookup),
            )

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
                item = _build_item(obj, external_id)
                display_value = _get_item_display_value(item)
                _add_to_results_if_query_matches(
                    item,
                    display_value,
                    external_id,
                    search_query,
                    matched_items,
                    seen_external_ids,
                )

            if len(matched_items) >= end_index:
                break
            if not api_page.get("next"):
                break
            current_page += 1

        # Skip processing favorites if we've already got enough to satisfy pagination
        if len(matched_items) < end_index:
            for fav in user_favorites:
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
                item = _build_item(detail, external_id, fav.custom_title, url)
                display_value = _get_item_display_value(item)
                _add_to_results_if_query_matches(
                    item,
                    display_value,
                    external_id,
                    search_query,
                    matched_items,
                    seen_external_ids,
                )

        total = len(matched_items)
        paginated_results = matched_items[start_index:end_index]
        return ContentListResponse(
            count=total,
            next=None,
            previous=None,
            results=paginated_results,
            total_favorites=len(favorite_lookup),
        )
