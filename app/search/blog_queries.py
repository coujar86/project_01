from dataclasses import dataclass
from datetime import datetime
from app.core.config import get_settings

settings = get_settings()


@dataclass(slots=True)
class BlogSearchFilters:
    image_ext: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


def build_blog_query(
    *, q: str, search_type: str, filters: BlogSearchFilters | None = None
) -> dict:
    filters = filters or BlogSearchFilters()
    filter_opt = []

    if filters.image_ext == "none":
        filter_opt.append({"bool": {"must_not": [{"exists": {"field": "image_ext"}}]}})
    elif filters.image_ext in settings.ALLOWED_EXT_ES:
        filter_opt.append({"term": {"image_ext": filters.image_ext}})

    if filters.date_from or filters.date_to:
        date_range = {}
        if filters.date_from:
            date_range["gte"] = filters.date_from.isoformat()
        if filters.date_to:
            date_range["lte"] = filters.date_to.isoformat()

        filter_opt.append({"range": {"modified_dt": date_range}})

    if search_type == "title_content":
        must_query = {
            "bool": {
                "should": [
                    {"match_phrase": {"title": {"query": q, "boost": 5}}},
                    {
                        "multi_match": {
                            "query": q,
                            "fields": ["title^3", "content"],
                            "type": "best_fields",
                            "operator": "or",
                        }
                    },
                    {"match": {"title.ngram": {"query": q, "boost": 1.2}}},
                ],
                "minimum_should_match": 1,
            }
        }
    elif search_type == "author":
        must_query = {
            "term": {
                "author.name": {
                    "value": q,
                    "case_insensitive": True,
                }
            }
        }
    else:
        raise ValueError()

    return {
        "bool": {
            "must": [must_query],
            "filter": filter_opt,
        }
    }
