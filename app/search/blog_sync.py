from elasticsearch import AsyncElasticsearch
from app.core.config import get_settings
from app.db.models import Blog
from app.utils.util import extract_image_ext

settings = get_settings()


def convert_blog_to_document(blog: Blog) -> dict:
    es_document = {
        "id": blog.id,
        "title": blog.title,
        "content": blog.content,
        "image_loc": blog.image_loc,
        "image_ext": extract_image_ext(blog.image_loc),
        "modified_dt": blog.modified_dt.isoformat(),
        "author": {
            "id": blog.author.id,
            "name": blog.author.name,
            "email": blog.author.email,
        },
    }
    return es_document


async def upsert_es_document(es: AsyncElasticsearch, document: dict) -> None:
    await es.index(
        index=settings.elasticsearch_index_blogs,
        id=str(document.get("id")),
        document=document,
    )


async def delete_es_document(es: AsyncElasticsearch, blog_id: int) -> None:
    await es.delete(
        index=settings.elasticsearch_index_blogs,
        id=str(blog_id),
    )
