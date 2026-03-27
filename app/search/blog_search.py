from elasticsearch import AsyncElasticsearch
from app.core.config import get_settings
from app.search.blog_queries import BlogSearchFilters, build_blog_query
from app.utils import util


settings = get_settings()

ES_PAGE_SIZE = settings.BLOGS_PER_PAGE
ES_SORT_LATEST = [{"modified_dt": {"order": "desc"}}, {"id": {"order": "desc"}}]
ES_SOURCE_FIELDS = [
    "id",
    "title",
    "content",
    "image_loc",
    "image_ext",
    "modified_dt",
    "author",
]


def _parse_blog_search_items(hits: list[dict]) -> list[dict]:
    """ES 검색 결과(hits 리스트)를 서비스용 리스트로 변환"""
    items = []
    for hit in hits:
        source_data = hit.get("_source")
        if not source_data:
            continue

        raw_image_loc = source_data.get("image_loc")
        image_loc = util.resolve_image_loc(raw_image_loc)

        raw_content = source_data.get("content", "")
        truncated_content = util.truncate_text(raw_content)

        item = {
            "id": source_data.get("id"),
            "title": source_data.get("title"),
            "content": truncated_content,
            "image_loc": image_loc,
            "image_ext": source_data.get("image_ext"),
            "modified_dt": source_data.get("modified_dt"),
            "author": source_data.get("author", {}).get("name"),
        }
        items.append(item)

    return items


async def _search_execute(
    es: AsyncElasticsearch,
    query: dict,
    page: int,
) -> dict[str, int | list[dict]]:
    """ES 검색 실행 및 결과 파싱"""
    from_ = (page - 1) * ES_PAGE_SIZE
    response = await es.search(
        index=settings.elasticsearch_index_blogs,
        query=query,
        sort=ES_SORT_LATEST,
        from_=from_,
        size=ES_PAGE_SIZE,
        track_total_hits=True,
        _source_includes=ES_SOURCE_FIELDS,
    )

    hits = response.get("hits", {}).get("hits", [])
    total = response.get("hits", {}).get("total", {}).get("value", 0)

    items = _parse_blog_search_items(hits)
    return {"total": total, "items": items}


async def search_blogs(
    es: AsyncElasticsearch,
    *,
    q: str,
    search_type: str,
    page: int,
    filters: BlogSearchFilters | None = None,
) -> tuple[list[dict], int, int]:
    query = build_blog_query(q=q, search_type=search_type, filters=filters)
    result = await _search_execute(es, query, page)

    total = result.get("total", 0)
    blogs = result.get("items", [])

    total_pages, current_page = util.calc_pagination(
        total=total, page=page, per_page=ES_PAGE_SIZE
    )
    return blogs, total_pages, current_page
