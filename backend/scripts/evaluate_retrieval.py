"""Evaluate retrieval ranking with a small manually labeled JSON benchmark.

Run from backend:
  python -m scripts.evaluate_retrieval --dataset experiments/retrieval_benchmark.json
The dataset is intentionally a template: replace relevant_chunk_ids with IDs verified
against your own documents before interpreting metric values.
"""
import argparse
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from app.services.retrieval_service import RetrievalService

def precision_at_k(retrieved, relevant, k):
    return sum(x in relevant for x in retrieved[:k]) / max(k, 1)

def recall_at_k(retrieved, relevant, k):
    return sum(x in relevant for x in retrieved[:k]) / len(relevant) if relevant else 0.0

def reciprocal_rank(retrieved, relevant):
    for rank, item in enumerate(retrieved, 1):
        if item in relevant:
            return 1.0 / rank
    return 0.0

def ndcg_at_k(retrieved, relevant, k):
    dcg = sum((1.0 / math.log2(rank + 1)) for rank, item in enumerate(retrieved[:k], 1) if item in relevant)
    ideal_count = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return dcg / idcg if idcg else 0.0

def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="experiments/retrieval_benchmark.json")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", default="experiments/retrieval_evaluation_results.json")
    args = parser.parse_args()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is missing. Set it in backend/.env.")
    data = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    service = RetrievalService(database_url)
    rows = []
    latencies = []
    for case in data:
        query = case["query"]
        relevant = {int(x) for x in case.get("relevant_chunk_ids", [])}
        if not relevant:
            print(f"SKIP {query!r}: add verified relevant_chunk_ids first.")
            continue
        start = time.perf_counter()
        response = service.search(query, args.top_k)
        elapsed_ms = (time.perf_counter() - start) * 1000
        retrieved = [int(x["chunk_id"]) for x in response["results"]]
        latencies.append(elapsed_ms)
        rows.append({
            "query": query,
            "relevant_chunk_ids": sorted(relevant),
            "retrieved_chunk_ids": retrieved,
            "precision_at_k": precision_at_k(retrieved, relevant, args.top_k),
            "recall_at_k": recall_at_k(retrieved, relevant, args.top_k),
            "mrr": reciprocal_rank(retrieved, relevant),
            "ndcg_at_k": ndcg_at_k(retrieved, relevant, args.top_k),
            "wall_latency_ms": round(elapsed_ms, 2),
            "embedding_time_ms": round(response["embedding_time_ms"], 2),
            "database_retrieval_time_ms": round(response["retrieval_time_ms"], 2),
        })
    summary = {"top_k": args.top_k, "evaluated_queries": len(rows), "results": rows}
    if rows:
        for metric in ("precision_at_k", "recall_at_k", "mrr", "ndcg_at_k"):
            summary[metric + "_mean"] = round(statistics.mean(r[metric] for r in rows), 4)
        summary["latency_median_ms"] = round(statistics.median(latencies), 2)
        summary["latency_p95_ms"] = round(sorted(latencies)[min(len(latencies)-1, math.ceil(.95*len(latencies))-1)], 2)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved report: {args.output}")

if __name__ == "__main__":
    main()
