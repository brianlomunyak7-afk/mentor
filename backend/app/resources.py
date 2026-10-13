import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.config import Settings, get_settings
from app.models import LearnerProfile, Lesson

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class ResourceSearchError(RuntimeError):
    """Raised when an external resource provider cannot be queried."""


@dataclass(frozen=True)
class ResourceCandidate:
    title: str
    url: str
    source: str
    duration_seconds: int | None
    reason: str
    credibility_score: float
    relevance_score: float


def _safe_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


async def _request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: dict[str, str],
    json: dict[str, object] | None = None,
) -> dict[str, object]:
    for attempt in range(3):
        try:
            response = await client.request(method, url, params=params, json=json)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                await asyncio.sleep(0.2 * (attempt + 1))
                continue
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ResourceSearchError("Resource provider returned invalid JSON")
            return payload
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            if attempt == 2:
                raise ResourceSearchError("Resource provider timed out") from error
    raise ResourceSearchError("Resource provider request failed")


async def search_youtube(
    query: str,
    *,
    profile: LearnerProfile,
    settings: Settings,
    client: httpx.AsyncClient,
) -> list[ResourceCandidate]:
    if not settings.youtube_api_key:
        return []
    payload = await _request_json(
        client,
        "GET",
        YOUTUBE_SEARCH_URL,
        params={
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": "5",
            "key": settings.youtube_api_key,
            "relevanceLanguage": profile.language[:2].lower(),
        },
    )
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ResourceSearchError("YouTube returned an invalid item list")
    candidates: list[ResourceCandidate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        identifier = item.get("id")
        snippet = item.get("snippet")
        if not isinstance(identifier, dict) or not isinstance(snippet, dict):
            continue
        video_id = identifier.get("videoId")
        title = snippet.get("title")
        channel = snippet.get("channelTitle")
        if not isinstance(video_id, str) or not isinstance(title, str):
            continue
        candidates.append(
            ResourceCandidate(
                title=title,
                url=f"https://www.youtube.com/watch?v={video_id}",
                source="youtube",
                duration_seconds=None,
                reason=f"YouTube result from {channel or 'the YouTube API'}",
                credibility_score=0.75,
                relevance_score=0.8,
            )
        )
    return candidates


async def search_web(
    query: str,
    *,
    settings: Settings,
    client: httpx.AsyncClient,
) -> list[ResourceCandidate]:
    if not settings.web_search_api_key:
        return []
    if (settings.web_search_provider or "").lower() != "tavily":
        raise ResourceSearchError("WEB_SEARCH_PROVIDER must be tavily")
    payload = await _request_json(
        client,
        "POST",
        TAVILY_SEARCH_URL,
        params={},
        json={
            "api_key": settings.web_search_api_key,
            "query": query,
            "max_results": 5,
            "include_answer": False,
        },
    )
    results = payload.get("results", [])
    if not isinstance(results, list):
        raise ResourceSearchError("Web search returned an invalid result list")
    candidates: list[ResourceCandidate] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        title, url = result.get("title"), result.get("url")
        if isinstance(title, str) and isinstance(url, str) and _safe_url(url):
            candidates.append(
                ResourceCandidate(
                    title=title,
                    url=url,
                    source="tavily",
                    duration_seconds=None,
                    reason="Web result returned by Tavily search",
                    credibility_score=0.6,
                    relevance_score=float(result.get("score", 0.5)),
                )
            )
    return candidates


async def link_is_live(
    candidate: ResourceCandidate,
    *,
    client: httpx.AsyncClient,
) -> bool:
    if not _safe_url(candidate.url):
        return False
    try:
        response = await client.head(candidate.url, follow_redirects=True)
        if response.status_code == 405:
            response = await client.get(candidate.url, follow_redirects=True)
        return response.is_success
    except (httpx.TimeoutException, httpx.NetworkError):
        return False


async def find_resources(
    lesson: Lesson,
    profile: LearnerProfile,
    *,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[ResourceCandidate]:
    config = settings or get_settings()
    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=8.0)
    query = f"{profile.learning_topic or ''} {lesson.title} {profile.current_level or ''}".strip()
    try:
        candidates = await search_youtube(
            query, profile=profile, settings=config, client=http_client
        )
        candidates.extend(await search_web(query, settings=config, client=http_client))
        checked = [
            candidate
            for candidate in candidates
            if await link_is_live(candidate, client=http_client)
        ]
        checked.sort(
            key=lambda item: (
                item.relevance_score + item.credibility_score,
                item.source == "youtube",
            ),
            reverse=True,
        )
        return checked[:3]
    finally:
        if owns_client:
            await http_client.aclose()
