"""Scoring engine to compute similarity between incoming and captured network requests."""

from typing import Any

from app.shadow.normalizer import RequestNormalizer
from app.shadow.schemas import CapturedRequest


class MatchScorer:
    """Calculates a similarity score between two captured requests.

    Higher scores indicate a better match. A score of -1.0 means incompatible.
    """

    def __init__(self, normalizer: RequestNormalizer | None = None):
        self.normalizer = normalizer or RequestNormalizer()

    def calculate_score(self, req1: CapturedRequest, req2: CapturedRequest) -> float:
        """Calculates a similarity score.

        Returns -1.0 if the requests are incompatible (different method or non-matching paths).
        """
        # 1. HTTP Method must match exactly (case-insensitive)
        if req1.method.upper() != req2.method.upper():
            return -1.0

        # Normalize path and query
        path1, query1 = self.normalizer.normalize_url(req1.url)
        path2, query2 = self.normalizer.normalize_url(req2.url)

        # 2. Path Match check
        if path1 != path2:
            return -1.0

        score = 0.0

        # High bonus for exact URL match (including all query parameters)
        if req1.url == req2.url:
            score += 150.0
        else:
            score += 100.0

        # 3. Query Parameters Match (up to 30.0 points)
        if not query1 and not query2:
            score += 30.0
        elif query1 and query2:
            all_keys = set(query1.keys()).union(query2.keys())
            matching_keys = set(query1.keys()).intersection(query2.keys())
            match_count = 0
            for k in matching_keys:
                if sorted(query1[k]) == sorted(query2[k]):
                    match_count += 1
            if all_keys:
                score += (match_count / len(all_keys)) * 30.0

        # 4. Headers Match (up to 20.0 points)
        headers1 = self.normalizer.normalize_headers(req1.headers)
        headers2 = self.normalizer.normalize_headers(req2.headers)

        if not headers1 and not headers2:
            score += 20.0
        elif headers1 and headers2:
            all_keys = set(headers1.keys()).union(headers2.keys())
            matching_keys = set(headers1.keys()).intersection(headers2.keys())
            match_count = 0
            for k in matching_keys:
                if headers1[k] == headers2[k]:
                    match_count += 1
            if all_keys:
                score += (match_count / len(all_keys)) * 20.0

        # 5. Request Body Match (up to 50.0 points)
        body1_norm = self.normalizer.normalize_body(req1.body)
        body2_norm = self.normalizer.normalize_body(req2.body)

        if not body1_norm and not body2_norm:
            score += 50.0
        elif body1_norm and body2_norm:
            if body1_norm == body2_norm:
                score += 50.0
            elif isinstance(body1_norm, dict) and isinstance(body2_norm, dict):
                dict_score = self._compare_normalized_dicts(body1_norm, body2_norm)
                score += dict_score * 50.0

        return score

    def _compare_normalized_dicts(self, d1: dict[str, Any], d2: dict[str, Any]) -> float:
        """Returns a similarity ratio between 0.0 and 1.0 for two normalized dictionaries."""
        all_keys = set(d1.keys()).union(d2.keys())
        if not all_keys:
            return 1.0
        matching_keys = set(d1.keys()).intersection(d2.keys())
        match_count = 0
        for k in matching_keys:
            if d1[k] == d2[k]:
                match_count += 1
        return match_count / len(all_keys)
