import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.all import EmergencyPlan

def _tokenize(text):
    if not text:
        return []
    import jieba
    return [w.strip() for w in jieba.lcut(text) if len(w.strip()) >= 2]

_bm25_index = {}
_bm25_ready = False


async def _build_index(db: AsyncSession):
    global _bm25_index, _bm25_ready
    result = await db.execute(select(EmergencyPlan))
    plans = result.scalars().all()
    _bm25_index.clear()
    for plan in plans:
        tokens = _tokenize((plan.content or "") + " " + (plan.title or ""))
        _bm25_index[plan.id] = tokens
    _bm25_ready = True


async def refresh_index(db: AsyncSession):
    global _bm25_ready
    _bm25_ready = False
    await _build_index(db)


def _bm25_score(query_tokens, doc_tokens, avgdl, total_docs, doc_term_freq):
    k1, b = 1.5, 0.75
    dl = max(len(doc_tokens), 1)
    score = 0.0
    for term in query_tokens:
        tf = doc_tokens.count(term)
        if tf == 0:
            continue
        df = doc_term_freq.get(term, 1)
        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * dl / avgdl)
        score += idf * numerator / denominator
    return score


async def search_plans(db: AsyncSession, query_text: str, limit: int = 10):
    global _bm25_index, _bm25_ready

    if not _bm25_ready:
        await _build_index(db)

    query_tokens = _tokenize(query_text or "")

    if not _bm25_index or not query_tokens:
        return await _search_ilike(db, query_text, limit)

    docs = list(_bm25_index.items())
    total_docs = len(docs)
    all_tokens = [t for _, tokens in docs for t in tokens]
    avgdl = len(all_tokens) / max(total_docs, 1)

    doc_term_freq = {}
    for term in set(query_tokens):
        doc_term_freq[term] = sum(1 for _, tokens in docs if term in tokens)

    scored = []
    for plan_id, tokens in docs:
        s = _bm25_score(query_tokens, tokens, avgdl, total_docs, doc_term_freq)
        if s > 0:
            scored.append((plan_id, s))

    if not scored:
        return await _search_ilike(db, query_text, limit)

    scored.sort(key=lambda x: x[1], reverse=True)
    top_ids = [pid for pid, _ in scored[:limit]]

    result = await db.execute(
        select(EmergencyPlan).where(EmergencyPlan.id.in_(top_ids))
    )
    plans = {p.id: p for p in result.scalars().all()}
    return [plans[pid] for pid in top_ids if pid in plans]


async def _search_ilike(db: AsyncSession, query_text: str, limit: int = 10):
    keywords = (query_text or "").split()
    conditions = []
    for kw in keywords[:5]:
        if kw.strip():
            conditions.append(EmergencyPlan.content.ilike(f"%{kw}%"))
            conditions.append(EmergencyPlan.title.ilike(f"%{kw}%"))

    if not conditions:
        result = await db.execute(select(EmergencyPlan).order_by(EmergencyPlan.id).limit(limit))
        return result.scalars().all()

    from sqlalchemy import or_
    result = await db.execute(
        select(EmergencyPlan).where(or_(*conditions)).limit(limit)
    )
    return result.scalars().all()


async def match_plans(db: AsyncSession, keywords, limit: int = 3):
    query = " ".join(keywords) if isinstance(keywords, list) else str(keywords or "")
    return await search_plans(db, query, limit)
