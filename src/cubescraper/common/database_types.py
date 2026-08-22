from __future__ import annotations

import datetime
import uuid
from typing import (
    Annotated,
    Any,
    Literal,
    NotRequired,
    Optional,
    TypeAlias,
    TypedDict,
)

from pydantic import BaseModel, Field, Json

NetRequestStatus: TypeAlias = Literal["PENDING", "SUCCESS", "ERROR"]

RealtimeEqualityOp: TypeAlias = Literal["eq", "neq", "lt", "lte", "gt", "gte", "in", "like", "ilike", "is", "match", "imatch", "isdistinct"]

RealtimeAction: TypeAlias = Literal["INSERT", "UPDATE", "DELETE", "TRUNCATE", "ERROR"]

StorageBuckettype: TypeAlias = Literal["STANDARD", "ANALYTICS", "VECTOR"]

AuthFactorType: TypeAlias = Literal["totp", "webauthn", "phone"]

AuthFactorStatus: TypeAlias = Literal["unverified", "verified"]

AuthAalLevel: TypeAlias = Literal["aal1", "aal2", "aal3"]

AuthCodeChallengeMethod: TypeAlias = Literal["s256", "plain"]

AuthOneTimeTokenType: TypeAlias = Literal["confirmation_token", "reauthentication_token", "recovery_token", "email_change_token_new", "email_change_token_current", "phone_change_token"]

AuthOauthRegistrationType: TypeAlias = Literal["dynamic", "manual"]

AuthOauthAuthorizationStatus: TypeAlias = Literal["pending", "approved", "denied", "expired"]

AuthOauthResponseType: TypeAlias = Literal["code"]

AuthOauthClientType: TypeAlias = Literal["public", "confidential"]

PgsodiumKeyStatus: TypeAlias = Literal["default", "valid", "invalid", "expired"]

PgsodiumKeyType: TypeAlias = Literal["aead-ietf", "aead-det", "hmacsha512", "hmacsha256", "auth", "shorthash", "generichash", "kdf", "secretbox", "secretstream", "stream_xchacha20"]

PublicAccessoriesCategories: TypeAlias = Literal["Timer", "Mat", "Lube", "Storage", "Keychain", "Charging pod", "Bag", "Stand"]

PublicAchievementsCategories: TypeAlias = Literal["Website", "Quantity"]

PublicBadgeRarity: TypeAlias = Literal["Special", "Legendary", "Mythic", "Epic", "Rare", "Common"]

PublicCubeReviewStatus: TypeAlias = Literal["published", "draft", "hidden"]

PublicCubeScrapRunsStatus: TypeAlias = Literal["queued", "done", "running", "failed"]

PublicCubeSurfaceFinish: TypeAlias = Literal["Matte", "Frosted", "UV Coated", "Glossy", "Sculpted"]

PublicCubeSurfaceFinishes: TypeAlias = Literal["Frosted", "UV Coated", "Glossy", "Sculpted"]

PublicCubeVersionType: TypeAlias = Literal["Base", "Trim", "Limited"]

PublicCubesSubtypes: TypeAlias = Literal["NxNxN", "Square-N", "Minx", "Shape-Shifting", "Cuboid", "Non-Twisty", "Corner-Turning", "Gear", "Other"]

PublicCubesSubtypesOldVersionToBeDropped: TypeAlias = Literal["NxNxN", "Square-N", "Minx", "Shape-Shifting", "Cuboid", "Non-Twisty", "Corner-Turning"]

PublicRatingCategories: TypeAlias = Literal["cube", "accessory"]

PublicReportTypes: TypeAlias = Literal["user", "cube", "cube-rating", "website"]

PublicStaffActions: TypeAlias = Literal["INSERT", "UPDATE", "DELETE"]

PublicSubmissionStatus: TypeAlias = Literal["Approved", "Rejected", "Pending"]

PublicUserCubeCondition: TypeAlias = Literal["New in box", "New", "Good", "Fair", "Worn", "Poor", "Broken"]

PublicUserCubeStatus: TypeAlias = Literal["Owned", "Wishlist", "Loaned", "Borrowed", "Lost"]

PublicUsersRoles: TypeAlias = Literal["Admin", "Moderator", "Lead Developer", "Community Manager", "Database Manager", "User"]

PublicCurrencies: TypeAlias = Literal["USD", "GBP", "EUR", "ETB", "AED", "RON", "INR", "RUB", "TRY", "VES", "XAF", "XOF", "ZAR", "PLN", "MXN", "BRL", "CAD", "CHF", "NOK", "JPY"]

class PublicAchievements(BaseModel):
    category: Optional[PublicAchievementsCategories] = Field(alias="category")
    created_at: datetime.datetime = Field(alias="created_at")
    description: str = Field(alias="description")
    evolutive: bool = Field(alias="evolutive")
    evolves_from: Optional[str] = Field(alias="evolves_from")
    hidden: bool = Field(alias="hidden")
    icon: str = Field(alias="icon")
    id: int = Field(alias="id")
    is_special: bool = Field(alias="is_special")
    name: str = Field(alias="name")
    rarity: PublicBadgeRarity = Field(alias="rarity")
    slug: str = Field(alias="slug")
    submitted_by_id: uuid.UUID = Field(alias="submitted_by_id")
    title: Optional[str] = Field(alias="title")
    unlock_method: str = Field(alias="unlock_method")
    unlockable: bool = Field(alias="unlockable")
    updated_at: datetime.datetime = Field(alias="updated_at")

class PublicAchievementsInsert(TypedDict):
    category: NotRequired[Annotated[Optional[PublicAchievementsCategories], Field(alias="category")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    description: Annotated[str, Field(alias="description")]
    evolutive: NotRequired[Annotated[bool, Field(alias="evolutive")]]
    evolves_from: NotRequired[Annotated[Optional[str], Field(alias="evolves_from")]]
    hidden: NotRequired[Annotated[bool, Field(alias="hidden")]]
    icon: Annotated[str, Field(alias="icon")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    is_special: NotRequired[Annotated[bool, Field(alias="is_special")]]
    name: Annotated[str, Field(alias="name")]
    rarity: NotRequired[Annotated[PublicBadgeRarity, Field(alias="rarity")]]
    slug: NotRequired[Annotated[str, Field(alias="slug")]]
    submitted_by_id: NotRequired[Annotated[uuid.UUID, Field(alias="submitted_by_id")]]
    title: NotRequired[Annotated[Optional[str], Field(alias="title")]]
    unlock_method: NotRequired[Annotated[str, Field(alias="unlock_method")]]
    unlockable: NotRequired[Annotated[bool, Field(alias="unlockable")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]

class PublicAchievementsUpdate(TypedDict):
    category: NotRequired[Annotated[Optional[PublicAchievementsCategories], Field(alias="category")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    description: NotRequired[Annotated[str, Field(alias="description")]]
    evolutive: NotRequired[Annotated[bool, Field(alias="evolutive")]]
    evolves_from: NotRequired[Annotated[Optional[str], Field(alias="evolves_from")]]
    hidden: NotRequired[Annotated[bool, Field(alias="hidden")]]
    icon: NotRequired[Annotated[str, Field(alias="icon")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    is_special: NotRequired[Annotated[bool, Field(alias="is_special")]]
    name: NotRequired[Annotated[str, Field(alias="name")]]
    rarity: NotRequired[Annotated[PublicBadgeRarity, Field(alias="rarity")]]
    slug: NotRequired[Annotated[str, Field(alias="slug")]]
    submitted_by_id: NotRequired[Annotated[uuid.UUID, Field(alias="submitted_by_id")]]
    title: NotRequired[Annotated[Optional[str], Field(alias="title")]]
    unlock_method: NotRequired[Annotated[str, Field(alias="unlock_method")]]
    unlockable: NotRequired[Annotated[bool, Field(alias="unlockable")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]

class PublicAccessories(BaseModel):
    approved: bool = Field(alias="approved")
    brand: Optional[str] = Field(alias="brand")
    category: Optional[PublicAccessoriesCategories] = Field(alias="category")
    compatibility: Optional[str] = Field(alias="compatibility")
    created_at: datetime.datetime = Field(alias="created_at")
    discontinued: bool = Field(alias="discontinued")
    id: int = Field(alias="id")
    image_url: Optional[str] = Field(alias="image_url")
    name: str = Field(alias="name")
    rating: Optional[float] = Field(alias="rating")
    release_date: datetime.date = Field(alias="release_date")
    slug: str = Field(alias="slug")
    updated_at: datetime.datetime = Field(alias="updated_at")

class PublicAccessoriesInsert(TypedDict):
    approved: NotRequired[Annotated[bool, Field(alias="approved")]]
    brand: NotRequired[Annotated[Optional[str], Field(alias="brand")]]
    category: NotRequired[Annotated[Optional[PublicAccessoriesCategories], Field(alias="category")]]
    compatibility: NotRequired[Annotated[Optional[str], Field(alias="compatibility")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    discontinued: NotRequired[Annotated[bool, Field(alias="discontinued")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    image_url: NotRequired[Annotated[Optional[str], Field(alias="image_url")]]
    name: Annotated[str, Field(alias="name")]
    rating: NotRequired[Annotated[Optional[float], Field(alias="rating")]]
    release_date: Annotated[datetime.date, Field(alias="release_date")]
    slug: Annotated[str, Field(alias="slug")]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]

class PublicAccessoriesUpdate(TypedDict):
    approved: NotRequired[Annotated[bool, Field(alias="approved")]]
    brand: NotRequired[Annotated[Optional[str], Field(alias="brand")]]
    category: NotRequired[Annotated[Optional[PublicAccessoriesCategories], Field(alias="category")]]
    compatibility: NotRequired[Annotated[Optional[str], Field(alias="compatibility")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    discontinued: NotRequired[Annotated[bool, Field(alias="discontinued")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    image_url: NotRequired[Annotated[Optional[str], Field(alias="image_url")]]
    name: NotRequired[Annotated[str, Field(alias="name")]]
    rating: NotRequired[Annotated[Optional[float], Field(alias="rating")]]
    release_date: NotRequired[Annotated[datetime.date, Field(alias="release_date")]]
    slug: NotRequired[Annotated[str, Field(alias="slug")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]

class PublicAwardsCategory(BaseModel):
    created_at: datetime.datetime = Field(alias="created_at")
    description: str = Field(alias="description")
    event_id: int = Field(alias="event_id")
    id: int = Field(alias="id")
    name: str = Field(alias="name")
    slug: str = Field(alias="slug")

class PublicAwardsCategoryInsert(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    description: Annotated[str, Field(alias="description")]
    event_id: Annotated[int, Field(alias="event_id")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: Annotated[str, Field(alias="name")]
    slug: NotRequired[Annotated[str, Field(alias="slug")]]

class PublicAwardsCategoryUpdate(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    description: NotRequired[Annotated[str, Field(alias="description")]]
    event_id: NotRequired[Annotated[int, Field(alias="event_id")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: NotRequired[Annotated[str, Field(alias="name")]]
    slug: NotRequired[Annotated[str, Field(alias="slug")]]

class PublicAwardsEvent(BaseModel):
    created_at: datetime.datetime = Field(alias="created_at")
    end_at: datetime.datetime = Field(alias="end_at")
    id: int = Field(alias="id")
    start_at: datetime.datetime = Field(alias="start_at")
    title: str = Field(alias="title")
    year: int = Field(alias="year")

class PublicAwardsEventInsert(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    end_at: Annotated[datetime.datetime, Field(alias="end_at")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    start_at: Annotated[datetime.datetime, Field(alias="start_at")]
    title: Annotated[str, Field(alias="title")]
    year: Annotated[int, Field(alias="year")]

class PublicAwardsEventUpdate(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    end_at: NotRequired[Annotated[datetime.datetime, Field(alias="end_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    start_at: NotRequired[Annotated[datetime.datetime, Field(alias="start_at")]]
    title: NotRequired[Annotated[str, Field(alias="title")]]
    year: NotRequired[Annotated[int, Field(alias="year")]]

class PublicAwardsNominee(BaseModel):
    category_id: int = Field(alias="category_id")
    created_at: datetime.datetime = Field(alias="created_at")
    cube_id: int = Field(alias="cube_id")
    extra_info: Optional[str] = Field(alias="extra_info")
    id: int = Field(alias="id")

class PublicAwardsNomineeInsert(TypedDict):
    category_id: Annotated[int, Field(alias="category_id")]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube_id: Annotated[int, Field(alias="cube_id")]
    extra_info: NotRequired[Annotated[Optional[str], Field(alias="extra_info")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]

class PublicAwardsNomineeUpdate(TypedDict):
    category_id: NotRequired[Annotated[int, Field(alias="category_id")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube_id: NotRequired[Annotated[int, Field(alias="cube_id")]]
    extra_info: NotRequired[Annotated[Optional[str], Field(alias="extra_info")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]

class PublicAwardsUserVote(BaseModel):
    category_id: int = Field(alias="category_id")
    id: int = Field(alias="id")
    nominee_id: int = Field(alias="nominee_id")
    user_id: uuid.UUID = Field(alias="user_id")
    voted_at: datetime.datetime = Field(alias="voted_at")

class PublicAwardsUserVoteInsert(TypedDict):
    category_id: Annotated[int, Field(alias="category_id")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    nominee_id: Annotated[int, Field(alias="nominee_id")]
    user_id: Annotated[uuid.UUID, Field(alias="user_id")]
    voted_at: NotRequired[Annotated[datetime.datetime, Field(alias="voted_at")]]

class PublicAwardsUserVoteUpdate(TypedDict):
    category_id: NotRequired[Annotated[int, Field(alias="category_id")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    nominee_id: NotRequired[Annotated[int, Field(alias="nominee_id")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]
    voted_at: NotRequired[Annotated[datetime.datetime, Field(alias="voted_at")]]

class PublicBrands(BaseModel):
    added_by_id: uuid.UUID = Field(alias="added_by_id")
    created_at: datetime.datetime = Field(alias="created_at")
    id: int = Field(alias="id")
    name: str = Field(alias="name")

class PublicBrandsInsert(TypedDict):
    added_by_id: NotRequired[Annotated[uuid.UUID, Field(alias="added_by_id")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: NotRequired[Annotated[str, Field(alias="name")]]

class PublicBrandsUpdate(TypedDict):
    added_by_id: NotRequired[Annotated[uuid.UUID, Field(alias="added_by_id")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: NotRequired[Annotated[str, Field(alias="name")]]

class PublicCubeFeatures(BaseModel):
    code: str = Field(alias="code")
    created_at: datetime.datetime = Field(alias="created_at")
    id: int = Field(alias="id")
    label: str = Field(alias="label")

class PublicCubeFeaturesInsert(TypedDict):
    code: Annotated[str, Field(alias="code")]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    label: Annotated[str, Field(alias="label")]

class PublicCubeFeaturesUpdate(TypedDict):
    code: NotRequired[Annotated[str, Field(alias="code")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    label: NotRequired[Annotated[str, Field(alias="label")]]

class PublicCubeModels(BaseModel):
    brand: str = Field(alias="brand")
    created_at: datetime.datetime = Field(alias="created_at")
    discontinued: bool = Field(alias="discontinued")
    id: int = Field(alias="id")
    image_url: str = Field(alias="image_url")
    model: str = Field(alias="model")
    name: Optional[str] = Field(alias="name")
    notes: Optional[str] = Field(alias="notes")
    rating: Optional[float] = Field(alias="rating")
    related_to: Optional[str] = Field(alias="related_to")
    release_date: Optional[datetime.date] = Field(alias="release_date")
    series: Optional[str] = Field(alias="series")
    series_id: Optional[int] = Field(alias="series_id")
    size: Optional[str] = Field(alias="size")
    slug: str = Field(alias="slug")
    status: PublicSubmissionStatus = Field(alias="status")
    sub_type: Optional[PublicCubesSubtypes] = Field(alias="sub_type")
    submitted_by_id: uuid.UUID = Field(alias="submitted_by_id")
    surface_finish: Optional[PublicCubeSurfaceFinishes] = Field(alias="surface_finish")
    type: str = Field(alias="type")
    updated_at: datetime.datetime = Field(alias="updated_at")
    verified_at: Optional[datetime.datetime] = Field(alias="verified_at")
    verified_by_id: Optional[uuid.UUID] = Field(alias="verified_by_id")
    version_name: Optional[str] = Field(alias="version_name")
    version_type: PublicCubeVersionType = Field(alias="version_type")
    weight: float = Field(alias="weight")

class PublicCubeModelsInsert(TypedDict):
    brand: NotRequired[Annotated[str, Field(alias="brand")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    discontinued: NotRequired[Annotated[bool, Field(alias="discontinued")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    image_url: Annotated[str, Field(alias="image_url")]
    model: Annotated[str, Field(alias="model")]
    name: NotRequired[Annotated[Optional[str], Field(alias="name")]]
    notes: NotRequired[Annotated[Optional[str], Field(alias="notes")]]
    rating: NotRequired[Annotated[Optional[float], Field(alias="rating")]]
    related_to: NotRequired[Annotated[Optional[str], Field(alias="related_to")]]
    release_date: NotRequired[Annotated[Optional[datetime.date], Field(alias="release_date")]]
    series: NotRequired[Annotated[Optional[str], Field(alias="series")]]
    series_id: NotRequired[Annotated[Optional[int], Field(alias="series_id")]]
    size: NotRequired[Annotated[Optional[str], Field(alias="size")]]
    slug: Annotated[str, Field(alias="slug")]
    status: NotRequired[Annotated[PublicSubmissionStatus, Field(alias="status")]]
    sub_type: NotRequired[Annotated[Optional[PublicCubesSubtypes], Field(alias="sub_type")]]
    submitted_by_id: NotRequired[Annotated[uuid.UUID, Field(alias="submitted_by_id")]]
    surface_finish: NotRequired[Annotated[Optional[PublicCubeSurfaceFinishes], Field(alias="surface_finish")]]
    type: Annotated[str, Field(alias="type")]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    verified_at: NotRequired[Annotated[Optional[datetime.datetime], Field(alias="verified_at")]]
    verified_by_id: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="verified_by_id")]]
    version_name: NotRequired[Annotated[Optional[str], Field(alias="version_name")]]
    version_type: NotRequired[Annotated[PublicCubeVersionType, Field(alias="version_type")]]
    weight: Annotated[float, Field(alias="weight")]

class PublicCubeModelsUpdate(TypedDict):
    brand: NotRequired[Annotated[str, Field(alias="brand")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    discontinued: NotRequired[Annotated[bool, Field(alias="discontinued")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    image_url: NotRequired[Annotated[str, Field(alias="image_url")]]
    model: NotRequired[Annotated[str, Field(alias="model")]]
    name: NotRequired[Annotated[Optional[str], Field(alias="name")]]
    notes: NotRequired[Annotated[Optional[str], Field(alias="notes")]]
    rating: NotRequired[Annotated[Optional[float], Field(alias="rating")]]
    related_to: NotRequired[Annotated[Optional[str], Field(alias="related_to")]]
    release_date: NotRequired[Annotated[Optional[datetime.date], Field(alias="release_date")]]
    series: NotRequired[Annotated[Optional[str], Field(alias="series")]]
    series_id: NotRequired[Annotated[Optional[int], Field(alias="series_id")]]
    size: NotRequired[Annotated[Optional[str], Field(alias="size")]]
    slug: NotRequired[Annotated[str, Field(alias="slug")]]
    status: NotRequired[Annotated[PublicSubmissionStatus, Field(alias="status")]]
    sub_type: NotRequired[Annotated[Optional[PublicCubesSubtypes], Field(alias="sub_type")]]
    submitted_by_id: NotRequired[Annotated[uuid.UUID, Field(alias="submitted_by_id")]]
    surface_finish: NotRequired[Annotated[Optional[PublicCubeSurfaceFinishes], Field(alias="surface_finish")]]
    type: NotRequired[Annotated[str, Field(alias="type")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    verified_at: NotRequired[Annotated[Optional[datetime.datetime], Field(alias="verified_at")]]
    verified_by_id: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="verified_by_id")]]
    version_name: NotRequired[Annotated[Optional[str], Field(alias="version_name")]]
    version_type: NotRequired[Annotated[PublicCubeVersionType, Field(alias="version_type")]]
    weight: NotRequired[Annotated[float, Field(alias="weight")]]

class PublicCubeScrapRuns(BaseModel):
    created_at: datetime.datetime = Field(alias="created_at")
    error_message: Optional[str] = Field(alias="error_message")
    finished_at: Optional[datetime.datetime] = Field(alias="finished_at")
    id: int = Field(alias="id")
    name: Optional[str] = Field(alias="name")
    started_at: Optional[datetime.datetime] = Field(alias="started_at")
    status: PublicCubeScrapRunsStatus = Field(alias="status")
    url: str = Field(alias="url")
    user_id: uuid.UUID = Field(alias="user_id")

class PublicCubeScrapRunsInsert(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    error_message: NotRequired[Annotated[Optional[str], Field(alias="error_message")]]
    finished_at: NotRequired[Annotated[Optional[datetime.datetime], Field(alias="finished_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: NotRequired[Annotated[Optional[str], Field(alias="name")]]
    started_at: NotRequired[Annotated[Optional[datetime.datetime], Field(alias="started_at")]]
    status: NotRequired[Annotated[PublicCubeScrapRunsStatus, Field(alias="status")]]
    url: Annotated[str, Field(alias="url")]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicCubeScrapRunsUpdate(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    error_message: NotRequired[Annotated[Optional[str], Field(alias="error_message")]]
    finished_at: NotRequired[Annotated[Optional[datetime.datetime], Field(alias="finished_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: NotRequired[Annotated[Optional[str], Field(alias="name")]]
    started_at: NotRequired[Annotated[Optional[datetime.datetime], Field(alias="started_at")]]
    status: NotRequired[Annotated[PublicCubeScrapRunsStatus, Field(alias="status")]]
    url: NotRequired[Annotated[str, Field(alias="url")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicCubeTypes(BaseModel):
    added_by_id: Optional[uuid.UUID] = Field(alias="added_by_id")
    created_at: datetime.datetime = Field(alias="created_at")
    id: int = Field(alias="id")
    name: str = Field(alias="name")
    popularity: int = Field(alias="popularity")
    shape_family: str = Field(alias="shape_family")

class PublicCubeTypesInsert(TypedDict):
    added_by_id: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="added_by_id")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: Annotated[str, Field(alias="name")]
    popularity: NotRequired[Annotated[int, Field(alias="popularity")]]
    shape_family: NotRequired[Annotated[str, Field(alias="shape_family")]]

class PublicCubeTypesUpdate(TypedDict):
    added_by_id: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="added_by_id")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: NotRequired[Annotated[str, Field(alias="name")]]
    popularity: NotRequired[Annotated[int, Field(alias="popularity")]]
    shape_family: NotRequired[Annotated[str, Field(alias="shape_family")]]

class PublicCubeVendorLinks(BaseModel):
    available: bool = Field(alias="available")
    created_at: datetime.datetime = Field(alias="created_at")
    cube_id: int = Field(alias="cube_id")
    id: int = Field(alias="id")
    is_dead: bool = Field(alias="is_dead")
    last_modified: datetime.datetime = Field(alias="last_modified")
    price: float = Field(alias="price")
    updated_at: datetime.datetime = Field(alias="updated_at")
    url: str = Field(alias="url")
    vendor_id: int = Field(alias="vendor_id")

class PublicCubeVendorLinksInsert(TypedDict):
    available: NotRequired[Annotated[bool, Field(alias="available")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube_id: Annotated[int, Field(alias="cube_id")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    is_dead: NotRequired[Annotated[bool, Field(alias="is_dead")]]
    last_modified: NotRequired[Annotated[datetime.datetime, Field(alias="last_modified")]]
    price: NotRequired[Annotated[float, Field(alias="price")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    url: Annotated[str, Field(alias="url")]
    vendor_id: Annotated[int, Field(alias="vendor_id")]

class PublicCubeVendorLinksUpdate(TypedDict):
    available: NotRequired[Annotated[bool, Field(alias="available")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube_id: NotRequired[Annotated[int, Field(alias="cube_id")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    is_dead: NotRequired[Annotated[bool, Field(alias="is_dead")]]
    last_modified: NotRequired[Annotated[datetime.datetime, Field(alias="last_modified")]]
    price: NotRequired[Annotated[float, Field(alias="price")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    url: NotRequired[Annotated[str, Field(alias="url")]]
    vendor_id: NotRequired[Annotated[int, Field(alias="vendor_id")]]

class PublicCubeVendorLinksSnapshot(BaseModel):
    available: bool = Field(alias="available")
    created_at: datetime.datetime = Field(alias="created_at")
    cube_id: int = Field(alias="cube_id")
    id: int = Field(alias="id")
    price: float = Field(alias="price")
    url: str = Field(alias="url")
    vendor_id: int = Field(alias="vendor_id")

class PublicCubeVendorLinksSnapshotInsert(TypedDict):
    available: NotRequired[Annotated[bool, Field(alias="available")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube_id: Annotated[int, Field(alias="cube_id")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    price: NotRequired[Annotated[float, Field(alias="price")]]
    url: Annotated[str, Field(alias="url")]
    vendor_id: Annotated[int, Field(alias="vendor_id")]

class PublicCubeVendorLinksSnapshotUpdate(TypedDict):
    available: NotRequired[Annotated[bool, Field(alias="available")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube_id: NotRequired[Annotated[int, Field(alias="cube_id")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    price: NotRequired[Annotated[float, Field(alias="price")]]
    url: NotRequired[Annotated[str, Field(alias="url")]]
    vendor_id: NotRequired[Annotated[int, Field(alias="vendor_id")]]

class PublicCubesModelFeatures(BaseModel):
    created_at: datetime.datetime = Field(alias="created_at")
    cube: str = Field(alias="cube")
    feature: str = Field(alias="feature")
    id: int = Field(alias="id")

class PublicCubesModelFeaturesInsert(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube: NotRequired[Annotated[str, Field(alias="cube")]]
    feature: NotRequired[Annotated[str, Field(alias="feature")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]

class PublicCubesModelFeaturesUpdate(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube: NotRequired[Annotated[str, Field(alias="cube")]]
    feature: NotRequired[Annotated[str, Field(alias="feature")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]

class PublicHelpfulRating(BaseModel):
    created_at: datetime.datetime = Field(alias="created_at")
    id: int = Field(alias="id")
    rating: int = Field(alias="rating")
    rating_category: PublicRatingCategories = Field(alias="rating_category")
    user_id: uuid.UUID = Field(alias="user_id")

class PublicHelpfulRatingInsert(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    rating: Annotated[int, Field(alias="rating")]
    rating_category: Annotated[PublicRatingCategories, Field(alias="rating_category")]
    user_id: Annotated[uuid.UUID, Field(alias="user_id")]

class PublicHelpfulRatingUpdate(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    rating: NotRequired[Annotated[int, Field(alias="rating")]]
    rating_category: NotRequired[Annotated[PublicRatingCategories, Field(alias="rating_category")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicHelpfulReview(BaseModel):
    created_at: datetime.datetime = Field(alias="created_at")
    id: int = Field(alias="id")
    review_id: int = Field(alias="review_id")
    user_id: uuid.UUID = Field(alias="user_id")

class PublicHelpfulReviewInsert(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    review_id: Annotated[int, Field(alias="review_id")]
    user_id: Annotated[uuid.UUID, Field(alias="user_id")]

class PublicHelpfulReviewUpdate(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    review_id: NotRequired[Annotated[int, Field(alias="review_id")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicNotifications(BaseModel):
    created_at: datetime.datetime = Field(alias="created_at")
    icon: Optional[str] = Field(alias="icon")
    id: int = Field(alias="id")
    link: Optional[str] = Field(alias="link")
    link_text: Optional[str] = Field(alias="link_text")
    message: str = Field(alias="message")
    published_by_id: Optional[uuid.UUID] = Field(alias="published_by_id")
    user_id: Optional[uuid.UUID] = Field(alias="user_id")

class PublicNotificationsInsert(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    icon: NotRequired[Annotated[Optional[str], Field(alias="icon")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    link: NotRequired[Annotated[Optional[str], Field(alias="link")]]
    link_text: NotRequired[Annotated[Optional[str], Field(alias="link_text")]]
    message: Annotated[str, Field(alias="message")]
    published_by_id: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="published_by_id")]]
    user_id: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="user_id")]]

class PublicNotificationsUpdate(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    icon: NotRequired[Annotated[Optional[str], Field(alias="icon")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    link: NotRequired[Annotated[Optional[str], Field(alias="link")]]
    link_text: NotRequired[Annotated[Optional[str], Field(alias="link_text")]]
    message: NotRequired[Annotated[str, Field(alias="message")]]
    published_by_id: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="published_by_id")]]
    user_id: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="user_id")]]

class PublicProfiles(BaseModel):
    banner: Optional[str] = Field(alias="banner")
    beta_flags: Json[Any] = Field(alias="beta_flags")
    bio: Optional[str] = Field(alias="bio")
    certified: bool = Field(alias="certified")
    created_at: datetime.datetime = Field(alias="created_at")
    display_name: str = Field(alias="display_name")
    id: int = Field(alias="id")
    onboarded: bool = Field(alias="onboarded")
    private: bool = Field(alias="private")
    profile_picture: Optional[str] = Field(alias="profile_picture")
    role: PublicUsersRoles = Field(alias="role")
    socials: Optional[Json[Any]] = Field(alias="socials")
    user_id: uuid.UUID = Field(alias="user_id")
    username: str = Field(alias="username")
    verified: bool = Field(alias="verified")

class PublicProfilesInsert(TypedDict):
    banner: NotRequired[Annotated[Optional[str], Field(alias="banner")]]
    beta_flags: NotRequired[Annotated[Json[Any], Field(alias="beta_flags")]]
    bio: NotRequired[Annotated[Optional[str], Field(alias="bio")]]
    certified: NotRequired[Annotated[bool, Field(alias="certified")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    display_name: Annotated[str, Field(alias="display_name")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    onboarded: NotRequired[Annotated[bool, Field(alias="onboarded")]]
    private: NotRequired[Annotated[bool, Field(alias="private")]]
    profile_picture: NotRequired[Annotated[Optional[str], Field(alias="profile_picture")]]
    role: NotRequired[Annotated[PublicUsersRoles, Field(alias="role")]]
    socials: NotRequired[Annotated[Optional[Json[Any]], Field(alias="socials")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]
    username: Annotated[str, Field(alias="username")]
    verified: NotRequired[Annotated[bool, Field(alias="verified")]]

class PublicProfilesUpdate(TypedDict):
    banner: NotRequired[Annotated[Optional[str], Field(alias="banner")]]
    beta_flags: NotRequired[Annotated[Json[Any], Field(alias="beta_flags")]]
    bio: NotRequired[Annotated[Optional[str], Field(alias="bio")]]
    certified: NotRequired[Annotated[bool, Field(alias="certified")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    display_name: NotRequired[Annotated[str, Field(alias="display_name")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    onboarded: NotRequired[Annotated[bool, Field(alias="onboarded")]]
    private: NotRequired[Annotated[bool, Field(alias="private")]]
    profile_picture: NotRequired[Annotated[Optional[str], Field(alias="profile_picture")]]
    role: NotRequired[Annotated[PublicUsersRoles, Field(alias="role")]]
    socials: NotRequired[Annotated[Optional[Json[Any]], Field(alias="socials")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]
    username: NotRequired[Annotated[str, Field(alias="username")]]
    verified: NotRequired[Annotated[bool, Field(alias="verified")]]

class PublicReports(BaseModel):
    comment: Optional[str] = Field(alias="comment")
    created_at: datetime.datetime = Field(alias="created_at")
    id: int = Field(alias="id")
    image_url: Optional[str] = Field(alias="image_url")
    report_type: PublicReportTypes = Field(alias="report_type")
    reported: str = Field(alias="reported")
    reporter: uuid.UUID = Field(alias="reporter")
    resolved: bool = Field(alias="resolved")
    resolved_by: Optional[uuid.UUID] = Field(alias="resolved_by")
    title: str = Field(alias="title")

class PublicReportsInsert(TypedDict):
    comment: NotRequired[Annotated[Optional[str], Field(alias="comment")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    image_url: NotRequired[Annotated[Optional[str], Field(alias="image_url")]]
    report_type: Annotated[PublicReportTypes, Field(alias="report_type")]
    reported: Annotated[str, Field(alias="reported")]
    reporter: Annotated[uuid.UUID, Field(alias="reporter")]
    resolved: NotRequired[Annotated[bool, Field(alias="resolved")]]
    resolved_by: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="resolved_by")]]
    title: NotRequired[Annotated[str, Field(alias="title")]]

class PublicReportsUpdate(TypedDict):
    comment: NotRequired[Annotated[Optional[str], Field(alias="comment")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    image_url: NotRequired[Annotated[Optional[str], Field(alias="image_url")]]
    report_type: NotRequired[Annotated[PublicReportTypes, Field(alias="report_type")]]
    reported: NotRequired[Annotated[str, Field(alias="reported")]]
    reporter: NotRequired[Annotated[uuid.UUID, Field(alias="reporter")]]
    resolved: NotRequired[Annotated[bool, Field(alias="resolved")]]
    resolved_by: NotRequired[Annotated[Optional[uuid.UUID], Field(alias="resolved_by")]]
    title: NotRequired[Annotated[str, Field(alias="title")]]

class PublicStaffLogs(BaseModel):
    action: PublicStaffActions = Field(alias="action")
    created_at: datetime.datetime = Field(alias="created_at")
    id: int = Field(alias="id")
    new_data: Optional[Json[Any]] = Field(alias="new_data")
    old_data: Optional[Json[Any]] = Field(alias="old_data")
    staff_id: uuid.UUID = Field(alias="staff_id")
    target_table: str = Field(alias="target_table")

class PublicStaffLogsInsert(TypedDict):
    action: Annotated[PublicStaffActions, Field(alias="action")]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    new_data: NotRequired[Annotated[Optional[Json[Any]], Field(alias="new_data")]]
    old_data: NotRequired[Annotated[Optional[Json[Any]], Field(alias="old_data")]]
    staff_id: NotRequired[Annotated[uuid.UUID, Field(alias="staff_id")]]
    target_table: Annotated[str, Field(alias="target_table")]

class PublicStaffLogsUpdate(TypedDict):
    action: NotRequired[Annotated[PublicStaffActions, Field(alias="action")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    new_data: NotRequired[Annotated[Optional[Json[Any]], Field(alias="new_data")]]
    old_data: NotRequired[Annotated[Optional[Json[Any]], Field(alias="old_data")]]
    staff_id: NotRequired[Annotated[uuid.UUID, Field(alias="staff_id")]]
    target_table: NotRequired[Annotated[str, Field(alias="target_table")]]

class PublicUserAchievements(BaseModel):
    achievement_slug: str = Field(alias="achievement_slug")
    awarded_at: datetime.datetime = Field(alias="awarded_at")
    awarded_by_id: uuid.UUID = Field(alias="awarded_by_id")
    user_id: uuid.UUID = Field(alias="user_id")

class PublicUserAchievementsInsert(TypedDict):
    achievement_slug: Annotated[str, Field(alias="achievement_slug")]
    awarded_at: NotRequired[Annotated[datetime.datetime, Field(alias="awarded_at")]]
    awarded_by_id: NotRequired[Annotated[uuid.UUID, Field(alias="awarded_by_id")]]
    user_id: Annotated[uuid.UUID, Field(alias="user_id")]

class PublicUserAchievementsUpdate(TypedDict):
    achievement_slug: NotRequired[Annotated[str, Field(alias="achievement_slug")]]
    awarded_at: NotRequired[Annotated[datetime.datetime, Field(alias="awarded_at")]]
    awarded_by_id: NotRequired[Annotated[uuid.UUID, Field(alias="awarded_by_id")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicUserCubeRatings(BaseModel):
    comment: Optional[str] = Field(alias="comment")
    created_at: datetime.datetime = Field(alias="created_at")
    cube_slug: str = Field(alias="cube_slug")
    id: int = Field(alias="id")
    rating: float = Field(alias="rating")
    updated_at: datetime.datetime = Field(alias="updated_at")
    user_id: uuid.UUID = Field(alias="user_id")

class PublicUserCubeRatingsInsert(TypedDict):
    comment: NotRequired[Annotated[Optional[str], Field(alias="comment")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube_slug: Annotated[str, Field(alias="cube_slug")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    rating: Annotated[float, Field(alias="rating")]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    user_id: Annotated[uuid.UUID, Field(alias="user_id")]

class PublicUserCubeRatingsUpdate(TypedDict):
    comment: NotRequired[Annotated[Optional[str], Field(alias="comment")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube_slug: NotRequired[Annotated[str, Field(alias="cube_slug")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    rating: NotRequired[Annotated[float, Field(alias="rating")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicUserCubeReviews(BaseModel):
    created_at: datetime.datetime = Field(alias="created_at")
    cube: str = Field(alias="cube")
    id: int = Field(alias="id")
    review: str = Field(alias="review")
    status: PublicCubeReviewStatus = Field(alias="status")
    title: str = Field(alias="title")
    updated_at: datetime.datetime = Field(alias="updated_at")
    user_id: uuid.UUID = Field(alias="user_id")

class PublicUserCubeReviewsInsert(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube: Annotated[str, Field(alias="cube")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    review: Annotated[str, Field(alias="review")]
    status: NotRequired[Annotated[PublicCubeReviewStatus, Field(alias="status")]]
    title: Annotated[str, Field(alias="title")]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    user_id: Annotated[uuid.UUID, Field(alias="user_id")]

class PublicUserCubeReviewsUpdate(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube: NotRequired[Annotated[str, Field(alias="cube")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    review: NotRequired[Annotated[str, Field(alias="review")]]
    status: NotRequired[Annotated[PublicCubeReviewStatus, Field(alias="status")]]
    title: NotRequired[Annotated[str, Field(alias="title")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicUserCubeReviewsCategories(BaseModel):
    active: bool = Field(alias="active")
    created_at: datetime.datetime = Field(alias="created_at")
    id: int = Field(alias="id")
    label: str = Field(alias="label")
    slug: str = Field(alias="slug")

class PublicUserCubeReviewsCategoriesInsert(TypedDict):
    active: NotRequired[Annotated[bool, Field(alias="active")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    label: Annotated[str, Field(alias="label")]
    slug: Annotated[str, Field(alias="slug")]

class PublicUserCubeReviewsCategoriesUpdate(TypedDict):
    active: NotRequired[Annotated[bool, Field(alias="active")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    label: NotRequired[Annotated[str, Field(alias="label")]]
    slug: NotRequired[Annotated[str, Field(alias="slug")]]

class PublicUserCubeReviewsRatings(BaseModel):
    category_id: int = Field(alias="category_id")
    created_at: datetime.datetime = Field(alias="created_at")
    rating: float = Field(alias="rating")
    review_id: int = Field(alias="review_id")

class PublicUserCubeReviewsRatingsInsert(TypedDict):
    category_id: Annotated[int, Field(alias="category_id")]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    rating: Annotated[float, Field(alias="rating")]
    review_id: Annotated[int, Field(alias="review_id")]

class PublicUserCubeReviewsRatingsUpdate(TypedDict):
    category_id: NotRequired[Annotated[int, Field(alias="category_id")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    rating: NotRequired[Annotated[float, Field(alias="rating")]]
    review_id: NotRequired[Annotated[int, Field(alias="review_id")]]

class PublicUserCubes(BaseModel):
    acquired_at: Optional[datetime.date] = Field(alias="acquired_at")
    bought_from: Optional[str] = Field(alias="bought_from")
    condition: PublicUserCubeCondition = Field(alias="condition")
    created_at: datetime.datetime = Field(alias="created_at")
    cube: str = Field(alias="cube")
    id: int = Field(alias="id")
    main: bool = Field(alias="main")
    modified_at: datetime.datetime = Field(alias="modified_at")
    notes: Optional[str] = Field(alias="notes")
    purchase_price: Optional[float] = Field(alias="purchase_price")
    quantity: int = Field(alias="quantity")
    status: PublicUserCubeStatus = Field(alias="status")
    user_id: uuid.UUID = Field(alias="user_id")

class PublicUserCubesInsert(TypedDict):
    acquired_at: NotRequired[Annotated[Optional[datetime.date], Field(alias="acquired_at")]]
    bought_from: NotRequired[Annotated[Optional[str], Field(alias="bought_from")]]
    condition: Annotated[PublicUserCubeCondition, Field(alias="condition")]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube: Annotated[str, Field(alias="cube")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    main: NotRequired[Annotated[bool, Field(alias="main")]]
    modified_at: NotRequired[Annotated[datetime.datetime, Field(alias="modified_at")]]
    notes: NotRequired[Annotated[Optional[str], Field(alias="notes")]]
    purchase_price: NotRequired[Annotated[Optional[float], Field(alias="purchase_price")]]
    quantity: NotRequired[Annotated[int, Field(alias="quantity")]]
    status: Annotated[PublicUserCubeStatus, Field(alias="status")]
    user_id: Annotated[uuid.UUID, Field(alias="user_id")]

class PublicUserCubesUpdate(TypedDict):
    acquired_at: NotRequired[Annotated[Optional[datetime.date], Field(alias="acquired_at")]]
    bought_from: NotRequired[Annotated[Optional[str], Field(alias="bought_from")]]
    condition: NotRequired[Annotated[PublicUserCubeCondition, Field(alias="condition")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    cube: NotRequired[Annotated[str, Field(alias="cube")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    main: NotRequired[Annotated[bool, Field(alias="main")]]
    modified_at: NotRequired[Annotated[datetime.datetime, Field(alias="modified_at")]]
    notes: NotRequired[Annotated[Optional[str], Field(alias="notes")]]
    purchase_price: NotRequired[Annotated[Optional[float], Field(alias="purchase_price")]]
    quantity: NotRequired[Annotated[int, Field(alias="quantity")]]
    status: NotRequired[Annotated[PublicUserCubeStatus, Field(alias="status")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicUserFollows(BaseModel):
    followed_at: datetime.datetime = Field(alias="followed_at")
    follower_id: uuid.UUID = Field(alias="follower_id")
    following_id: uuid.UUID = Field(alias="following_id")
    id: int = Field(alias="id")

class PublicUserFollowsInsert(TypedDict):
    followed_at: NotRequired[Annotated[datetime.datetime, Field(alias="followed_at")]]
    follower_id: NotRequired[Annotated[uuid.UUID, Field(alias="follower_id")]]
    following_id: NotRequired[Annotated[uuid.UUID, Field(alias="following_id")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]

class PublicUserFollowsUpdate(TypedDict):
    followed_at: NotRequired[Annotated[datetime.datetime, Field(alias="followed_at")]]
    follower_id: NotRequired[Annotated[uuid.UUID, Field(alias="follower_id")]]
    following_id: NotRequired[Annotated[uuid.UUID, Field(alias="following_id")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]

class PublicUserNotificationStatus(BaseModel):
    notification_id: int = Field(alias="notification_id")
    read: bool = Field(alias="read")
    user_id: uuid.UUID = Field(alias="user_id")

class PublicUserNotificationStatusInsert(TypedDict):
    notification_id: Annotated[int, Field(alias="notification_id")]
    read: NotRequired[Annotated[bool, Field(alias="read")]]
    user_id: Annotated[uuid.UUID, Field(alias="user_id")]

class PublicUserNotificationStatusUpdate(TypedDict):
    notification_id: NotRequired[Annotated[int, Field(alias="notification_id")]]
    read: NotRequired[Annotated[bool, Field(alias="read")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicUserOnboarding(BaseModel):
    discovered_via: str = Field(alias="discovered_via")
    id: int = Field(alias="id")
    interested_features: Json[Any] = Field(alias="interested_features")
    other_text: Optional[str] = Field(alias="other_text")
    user_id: uuid.UUID = Field(alias="user_id")

class PublicUserOnboardingInsert(TypedDict):
    discovered_via: Annotated[str, Field(alias="discovered_via")]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    interested_features: NotRequired[Annotated[Json[Any], Field(alias="interested_features")]]
    other_text: NotRequired[Annotated[Optional[str], Field(alias="other_text")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicUserOnboardingUpdate(TypedDict):
    discovered_via: NotRequired[Annotated[str, Field(alias="discovered_via")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    interested_features: NotRequired[Annotated[Json[Any], Field(alias="interested_features")]]
    other_text: NotRequired[Annotated[Optional[str], Field(alias="other_text")]]
    user_id: NotRequired[Annotated[uuid.UUID, Field(alias="user_id")]]

class PublicVendors(BaseModel):
    base_url: str = Field(alias="base_url")
    country_iso: str = Field(alias="country_iso")
    created_at: datetime.datetime = Field(alias="created_at")
    currency: PublicCurrencies = Field(alias="currency")
    id: int = Field(alias="id")
    is_active: bool = Field(alias="is_active")
    logo_url: Optional[str] = Field(alias="logo_url")
    name: str = Field(alias="name")
    rating: float = Field(alias="rating")
    slug: str = Field(alias="slug")
    sponsored: bool = Field(alias="sponsored")
    supports_price_scraping: bool = Field(alias="supports_price_scraping")
    supports_product_scraping: bool = Field(alias="supports_product_scraping")
    updated_at: datetime.datetime = Field(alias="updated_at")
    verified: bool = Field(alias="verified")

class PublicVendorsInsert(TypedDict):
    base_url: Annotated[str, Field(alias="base_url")]
    country_iso: Annotated[str, Field(alias="country_iso")]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    currency: NotRequired[Annotated[PublicCurrencies, Field(alias="currency")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    is_active: NotRequired[Annotated[bool, Field(alias="is_active")]]
    logo_url: NotRequired[Annotated[Optional[str], Field(alias="logo_url")]]
    name: Annotated[str, Field(alias="name")]
    rating: NotRequired[Annotated[float, Field(alias="rating")]]
    slug: Annotated[str, Field(alias="slug")]
    sponsored: NotRequired[Annotated[bool, Field(alias="sponsored")]]
    supports_price_scraping: NotRequired[Annotated[bool, Field(alias="supports_price_scraping")]]
    supports_product_scraping: NotRequired[Annotated[bool, Field(alias="supports_product_scraping")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    verified: NotRequired[Annotated[bool, Field(alias="verified")]]

class PublicVendorsUpdate(TypedDict):
    base_url: NotRequired[Annotated[str, Field(alias="base_url")]]
    country_iso: NotRequired[Annotated[str, Field(alias="country_iso")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    currency: NotRequired[Annotated[PublicCurrencies, Field(alias="currency")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    is_active: NotRequired[Annotated[bool, Field(alias="is_active")]]
    logo_url: NotRequired[Annotated[Optional[str], Field(alias="logo_url")]]
    name: NotRequired[Annotated[str, Field(alias="name")]]
    rating: NotRequired[Annotated[float, Field(alias="rating")]]
    slug: NotRequired[Annotated[str, Field(alias="slug")]]
    sponsored: NotRequired[Annotated[bool, Field(alias="sponsored")]]
    supports_price_scraping: NotRequired[Annotated[bool, Field(alias="supports_price_scraping")]]
    supports_product_scraping: NotRequired[Annotated[bool, Field(alias="supports_product_scraping")]]
    updated_at: NotRequired[Annotated[datetime.datetime, Field(alias="updated_at")]]
    verified: NotRequired[Annotated[bool, Field(alias="verified")]]

class PublicCubeSeries(BaseModel):
    created_at: datetime.datetime = Field(alias="created_at")
    id: int = Field(alias="id")
    name: str = Field(alias="name")

class PublicCubeSeriesInsert(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: Annotated[str, Field(alias="name")]

class PublicCubeSeriesUpdate(TypedDict):
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    id: NotRequired[Annotated[int, Field(alias="id")]]
    name: NotRequired[Annotated[str, Field(alias="name")]]

class PublicVDetailedCubeModels(BaseModel):
    avg_price: Optional[float] = Field(alias="avg_price")
    ball_core: Optional[bool] = Field(alias="ball_core")
    brand: Optional[str] = Field(alias="brand")
    created_at: Optional[datetime.datetime] = Field(alias="created_at")
    discontinued: Optional[bool] = Field(alias="discontinued")
    id: Optional[int] = Field(alias="id")
    image_url: Optional[str] = Field(alias="image_url")
    maglev: Optional[bool] = Field(alias="maglev")
    magnetic: Optional[bool] = Field(alias="magnetic")
    modded: Optional[bool] = Field(alias="modded")
    model: Optional[str] = Field(alias="model")
    name: Optional[str] = Field(alias="name")
    notes: Optional[str] = Field(alias="notes")
    popularity: Optional[int] = Field(alias="popularity")
    rating: Optional[float] = Field(alias="rating")
    related_to: Optional[str] = Field(alias="related_to")
    release_date: Optional[datetime.date] = Field(alias="release_date")
    series: Optional[str] = Field(alias="series")
    series_id: Optional[int] = Field(alias="series_id")
    size: Optional[str] = Field(alias="size")
    slug: Optional[str] = Field(alias="slug")
    smart: Optional[bool] = Field(alias="smart")
    status: Optional[PublicSubmissionStatus] = Field(alias="status")
    stickered: Optional[bool] = Field(alias="stickered")
    sub_type: Optional[PublicCubesSubtypes] = Field(alias="sub_type")
    submitted_by_id: Optional[uuid.UUID] = Field(alias="submitted_by_id")
    surface_finish: Optional[PublicCubeSurfaceFinishes] = Field(alias="surface_finish")
    type: Optional[str] = Field(alias="type")
    updated_at: Optional[datetime.datetime] = Field(alias="updated_at")
    verified_at: Optional[datetime.datetime] = Field(alias="verified_at")
    verified_by_id: Optional[uuid.UUID] = Field(alias="verified_by_id")
    version_name: Optional[str] = Field(alias="version_name")
    version_type: Optional[PublicCubeVersionType] = Field(alias="version_type")
    wca_legal: Optional[bool] = Field(alias="wca_legal")
    weight: Optional[float] = Field(alias="weight")
    year: Optional[int] = Field(alias="year")

class PublicVAchievementRarity(BaseModel):
    category: Optional[PublicAchievementsCategories] = Field(alias="category")
    created_at: Optional[datetime.datetime] = Field(alias="created_at")
    description: Optional[str] = Field(alias="description")
    hidden: Optional[bool] = Field(alias="hidden")
    holders_count: Optional[int] = Field(alias="holders_count")
    icon: Optional[str] = Field(alias="icon")
    id: Optional[int] = Field(alias="id")
    name: Optional[str] = Field(alias="name")
    rarity: Optional[str] = Field(alias="rarity")
    rarity_percent: Optional[float] = Field(alias="rarity_percent")
    slug: Optional[str] = Field(alias="slug")
    title: Optional[str] = Field(alias="title")
    unlock_method: Optional[str] = Field(alias="unlock_method")
    unlockable: Optional[bool] = Field(alias="unlockable")

class PublicVAwardsCategoryWinners(BaseModel):
    category_id: Optional[int] = Field(alias="category_id")
    nominee_count: Optional[int] = Field(alias="nominee_count")
    nominee_slug: Optional[str] = Field(alias="nominee_slug")
    vote_count: Optional[int] = Field(alias="vote_count")

class PublicVDetailedProfiles(BaseModel):
    banner: Optional[str] = Field(alias="banner")
    bio: Optional[str] = Field(alias="bio")
    certified: Optional[bool] = Field(alias="certified")
    created_at: Optional[datetime.datetime] = Field(alias="created_at")
    cube_reviews_count: Optional[float] = Field(alias="cube_reviews_count")
    display_name: Optional[str] = Field(alias="display_name")
    id: Optional[int] = Field(alias="id")
    onboarded: Optional[bool] = Field(alias="onboarded")
    private: Optional[bool] = Field(alias="private")
    profile_picture: Optional[str] = Field(alias="profile_picture")
    role: Optional[PublicUsersRoles] = Field(alias="role")
    socials: Optional[Json[Any]] = Field(alias="socials")
    user_achievements_count: Optional[int] = Field(alias="user_achievements_count")
    user_avg_rating_count: Optional[float] = Field(alias="user_avg_rating_count")
    user_cube_ratings_count: Optional[int] = Field(alias="user_cube_ratings_count")
    user_cubes_count: Optional[int] = Field(alias="user_cubes_count")
    user_follower_count: Optional[int] = Field(alias="user_follower_count")
    user_following_count: Optional[int] = Field(alias="user_following_count")
    user_id: Optional[uuid.UUID] = Field(alias="user_id")
    username: Optional[str] = Field(alias="username")
    verified: Optional[bool] = Field(alias="verified")

class PublicVDetailedUserCubeReviews(BaseModel):
    created_at: Optional[datetime.datetime] = Field(alias="created_at")
    cube: Optional[str] = Field(alias="cube")
    helpful_count: Optional[int] = Field(alias="helpful_count")
    id: Optional[int] = Field(alias="id")
    ratings: Optional[Json[Any]] = Field(alias="ratings")
    review: Optional[str] = Field(alias="review")
    status: Optional[PublicCubeReviewStatus] = Field(alias="status")
    title: Optional[str] = Field(alias="title")
    updated_at: Optional[datetime.datetime] = Field(alias="updated_at")
    user_id: Optional[uuid.UUID] = Field(alias="user_id")

class PublicVDetailedVendors(BaseModel):
    base_url: Optional[str] = Field(alias="base_url")
    buyer_count: Optional[int] = Field(alias="buyer_count")
    country_iso: Optional[str] = Field(alias="country_iso")
    created_at: Optional[datetime.datetime] = Field(alias="created_at")
    currency: Optional[PublicCurrencies] = Field(alias="currency")
    id: Optional[int] = Field(alias="id")
    is_active: Optional[bool] = Field(alias="is_active")
    logo_url: Optional[str] = Field(alias="logo_url")
    name: Optional[str] = Field(alias="name")
    rating: Optional[float] = Field(alias="rating")
    slug: Optional[str] = Field(alias="slug")
    sponsored: Optional[bool] = Field(alias="sponsored")
    updated_at: Optional[datetime.datetime] = Field(alias="updated_at")
    verified: Optional[bool] = Field(alias="verified")

class PublicVNotificationsForUser(BaseModel):
    created_at: Optional[datetime.datetime] = Field(alias="created_at")
    icon: Optional[str] = Field(alias="icon")
    id: Optional[int] = Field(alias="id")
    link: Optional[str] = Field(alias="link")
    link_text: Optional[str] = Field(alias="link_text")
    message: Optional[str] = Field(alias="message")
    published_by_id: Optional[uuid.UUID] = Field(alias="published_by_id")
    read: Optional[bool] = Field(alias="read")
    user_id: Optional[uuid.UUID] = Field(alias="user_id")

class PublicVPriceHistory(BaseModel):
    cube_slug: Optional[str] = Field(alias="cube_slug")
    price_history: Optional[Json[Any]] = Field(alias="price_history")
    vendor_name: Optional[str] = Field(alias="vendor_name")

class PublicVUserStats(BaseModel):
    collection_value: Optional[float] = Field(alias="collection_value")
    cube_count: Optional[int] = Field(alias="cube_count")
    cubes_over_time: Optional[Json[Any]] = Field(alias="cubes_over_time")
    cubes_per_brand: Optional[Json[Any]] = Field(alias="cubes_per_brand")
    cubes_per_condition: Optional[Json[Any]] = Field(alias="cubes_per_condition")
    cubes_per_store: Optional[Json[Any]] = Field(alias="cubes_per_store")
    cubes_per_type: Optional[Json[Any]] = Field(alias="cubes_per_type")
    rating_avg: Optional[float] = Field(alias="rating_avg")
    rating_count: Optional[int] = Field(alias="rating_count")
    user_id: Optional[uuid.UUID] = Field(alias="user_id")
