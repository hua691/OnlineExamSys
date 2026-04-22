"""主观题自动评分工具：jieba 分词 + TF-IDF 相似度 + 关键词命中加权。"""
import json
import re

import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 预热 jieba，避免第一次请求慢
jieba.initialize()


def _clean(text: str) -> str:
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text.strip())


def tfidf_similarity(standard: str, student: str) -> float:
    """TF-IDF + 余弦相似度。返回 0-1。"""
    if not standard or not student:
        return 0.0
    s1 = ' '.join(jieba.cut(_clean(standard)))
    s2 = ' '.join(jieba.cut(_clean(student)))
    try:
        vec = TfidfVectorizer()
        m = vec.fit_transform([s1, s2])
        sim = cosine_similarity(m[0:1], m[1:2])[0][0]
        return max(0.0, min(1.0, float(sim)))
    except Exception:
        # 极简兜底：字符重合率
        a, b = set(standard), set(student)
        if not a or not b:
            return 0.0
        return len(a & b) / max(len(a), len(b))


def keyword_hit_ratio(student_text: str, keyword_points) -> float:
    """关键词命中加权。

    keyword_points: list[{"keyword": str, "weight": float}]
    返回 [0, 1]：sum(weight × 命中?) / sum(weight)
    """
    if not keyword_points:
        return 0.0
    total_weight = 0.0
    hit_weight = 0.0
    txt = student_text or ''
    for item in keyword_points:
        try:
            kw = item.get('keyword', '').strip()
            w = float(item.get('weight', 1))
        except Exception:
            continue
        if not kw:
            continue
        total_weight += w
        if kw in txt:
            hit_weight += w
    if total_weight <= 0:
        return 0.0
    return hit_weight / total_weight


def parse_keyword_points(raw: str):
    """把题目的 keyword_points 文本解析成 list。"""
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except Exception:
        pass
    # 兼容逗号分隔写法："循环,栈,递归"
    items = []
    for w in re.split(r'[,，\s]+', raw):
        w = w.strip()
        if w:
            items.append({'keyword': w, 'weight': 1})
    return items


def subjective_auto_score(question, student_answer: str):
    """综合相似度 + 关键词给出建议分数。

    返回 (similarity, auto_score)
    * similarity   : TF-IDF 余弦相似度 (0-1)
    * auto_score   : 建议得分（0 - question.score）

    评分规则：
      final_ratio = 0.5 * similarity_ratio + 0.5 * keyword_ratio
        其中 similarity_ratio：
            sim >= threshold → 1.0
            sim <= 0.3       → 0
            中间线性折算
        keyword_ratio = keyword_hit_ratio()
    """
    if not student_answer:
        return 0.0, 0.0

    similarity = tfidf_similarity(question.answer or '', student_answer)

    threshold = max(0.05, float(question.similarity_threshold or 0.6))
    low = 0.3
    if similarity >= threshold:
        sim_ratio = 1.0
    elif similarity <= low:
        sim_ratio = 0.0
    else:
        sim_ratio = (similarity - low) / (threshold - low)

    kw_points = parse_keyword_points(question.keyword_points)
    if kw_points:
        kw_ratio = keyword_hit_ratio(student_answer, kw_points)
        final_ratio = 0.5 * sim_ratio + 0.5 * kw_ratio
    else:
        final_ratio = sim_ratio  # 没设置关键词时只看相似度

    auto_score = round(final_ratio * float(question.score), 2)
    auto_score = max(0.0, min(auto_score, float(question.score)))
    return round(similarity, 3), auto_score
