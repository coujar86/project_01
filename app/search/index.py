from elasticsearch import AsyncElasticsearch


BLOG_INDEX_CONFIG = {
    "settings": {
        "analysis": {
            "filter": {"ngram_filter": {"type": "ngram", "min_gram": 2, "max_gram": 3}},
            "tokenizer": {
                "nori_tokenizer": {"type": "nori_tokenizer", "decompound_mode": "mixed"}
            },
            "analyzer": {
                "korean_analyzer": {"type": "custom", "tokenizer": "nori_tokenizer"},
                "korean_ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "ngram_filter"],
                },
            },
        },
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "title": {
                "type": "text",
                "analyzer": "korean_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "ngram": {"type": "text", "analyzer": "korean_ngram_analyzer"},
                },
            },
            "content": {"type": "text", "analyzer": "korean_analyzer"},
            "image_loc": {"type": "keyword", "index": False},
            "image_ext": {"type": "keyword"},
            "modified_dt": {"type": "date"},
            "author": {
                "properties": {
                    "id": {"type": "integer"},
                    "name": {
                        "type": "text",
                        "analyzer": "korean_analyzer",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "email": {"type": "keyword"},
                }
            },
        }
    },
}
BLOG_INDEX = "blogs_01"
BLOG_ALIAS = "blogs"


async def ensure_blog_index(es: AsyncElasticsearch) -> None:
    if not await es.indices.exists(index=BLOG_INDEX):
        await es.indices.create(index=BLOG_INDEX, **BLOG_INDEX_CONFIG)
        await es.indices.put_alias(
            index=BLOG_INDEX, name=BLOG_ALIAS, body={"is_write_index": True}
        )
    else:
        if not await es.indices.exists_alias(name=BLOG_ALIAS):
            await es.indices.put_alias(
                index=BLOG_INDEX, name=BLOG_ALIAS, body={"is_write_index": True}
            )
