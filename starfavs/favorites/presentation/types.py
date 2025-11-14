from dataclasses import dataclass
from typing import Callable, Optional, List
from enum import Enum


@dataclass
class ResourceConfig:
    resource_path: str
    display_field: str
    include_release_date: bool
    fetch_page: Callable
    fetch_detail: Callable


class RecordType(str, Enum):
    MOVIE = "movie"
    PLANET = "planet"


@dataclass
class CreateFavoriteInput:
    user_id: int
    custom_title: Optional[str]
    original_name: str
    external_record_id: str
    record_type: str


@dataclass
class UpdateFavoriteInput:
    favorite_id: int
    custom_title: Optional[str]


@dataclass
class DeleteFavoriteByIdInput:
    favorite_id: int


@dataclass
class DeleteUserFavoritesByTypeInput:
    user_id: int
    record_type: str
    external_record_id: Optional[str] = None


@dataclass
class GetUserFavoritesInput:
    user_id: int
    record_type: Optional[str] = None


@dataclass
class ListContentInput:
    user_id: int
    record_type: str
    page: int = 1
    limit: int = 10
    search: Optional[str] = None


@dataclass
class ContentItem:
    title: Optional[str] = None
    name: Optional[str] = None
    created: str = ""
    edited: str = ""
    url: str = ""
    is_favourite: bool = False
    release_date: Optional[str] = None


@dataclass
class ContentListResponse:
    next: Optional[str]
    previous: Optional[str]
    results: List[ContentItem]
    total_favorites: int
    count: Optional[int] = None  
