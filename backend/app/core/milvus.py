from app.core.config import settings

MILVUS_AVAILABLE = False
try:
    from pymilvus import MilvusClient, DataType
    MILVUS_AVAILABLE = True
except ImportError:
    pass

COLLECTION_NAME = "plan_chunks"
DIM = 1536

_milvus_client = None


def get_milvus_client():
    if not MILVUS_AVAILABLE:
        return None
    global _milvus_client
    if _milvus_client is None:
        _milvus_client = MilvusClient(host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)
    return _milvus_client


async def connect_milvus():
    if not MILVUS_AVAILABLE:
        return
    try:
        client = get_milvus_client()
        client.load_collection(COLLECTION_NAME)
    except Exception:
        pass


async def disconnect_milvus():
    global _milvus_client
    if _milvus_client:
        try:
            _milvus_client.close()
        except Exception:
            pass
        _milvus_client = None


def create_plan_chunks_collection():
    if not MILVUS_AVAILABLE:
        return
    client = get_milvus_client()
    if client is None or client.has_collection(COLLECTION_NAME):
        return

    schema = client.create_schema(
        auto_id=False,
        enable_dynamic_field=False,
    )
    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
    schema.add_field(field_name="plan_id", datatype=DataType.INT64)
    schema.add_field(field_name="chunk_text", datatype=DataType.VARCHAR, max_length=65535)
    schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=DIM)
    schema.add_field(field_name="metadata", datatype=DataType.JSON)

    index_params = client.prepare_index_params()
    index_params.add_index(field_name="embedding", index_type="IVF_FLAT", metric_type="COSINE", params={"nlist": 128})

    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params,
    )


def insert_chunks(chunks: list, embeddings: list) -> list:
    if not MILVUS_AVAILABLE:
        return []
    client = get_milvus_client()
    data = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        data.append({
            "id": chunk["id"],
            "plan_id": chunk["plan_id"],
            "chunk_text": chunk["text"],
            "embedding": emb,
            "metadata": chunk.get("metadata", {}),
        })
    result = client.insert(collection_name=COLLECTION_NAME, data=data)
    client.flush(COLLECTION_NAME)
    return result["ids"]


def search_similar(query_embedding: list, top_k: int = 5) -> list:
    if not MILVUS_AVAILABLE:
        return []
    client = get_milvus_client()
    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_embedding],
        limit=top_k,
        output_fields=["plan_id", "chunk_text", "metadata"],
    )
    hits = []
    for hit in results[0]:
        hits.append({
            "plan_id": hit["entity"]["plan_id"],
            "chunk_text": hit["entity"]["chunk_text"],
            "score": hit["distance"],
            "metadata": hit["entity"].get("metadata", {}),
        })
    return hits
