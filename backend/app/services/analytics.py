"""
Analytics service using Neo4j Graph Data Science (GDS).
"""

import json
import logging
import uuid
from typing import List, Dict, Any

from app.config import settings
from app.db.neo4j import neo4j_session
from app.db.redis import get_redis_client

logger = logging.getLogger(__name__)


def calculate_centrality(network_id: str) -> List[Dict[str, Any]]:
    """
    Calculates PageRank centrality for nodes in a specific network using Neo4j GDS.
    Uses cypher projection to isolate the network, runs PageRank, and cleans up.
    Returns a sorted list of dictionaries with node_id, score, and rank.
    """
    cache_key = f"centrality:{network_id}"
    if settings.centrality_cache_ttl_seconds:
        try:
            cached = get_redis_client().get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            logger.warning("centrality cache read failed", exc_info=True)

    # A unique projection eliminates concurrent-request races. Cleanup in a
    # finally block prevents GDS memory leaks when PageRank fails.
    graph_name = f"network_{network_id.replace('-', '_')}_{uuid.uuid4().hex}"
    graph_created = False
    results: List[Dict[str, Any]] = []

    with neo4j_session(write=True) as session:
        try:

            # Project the specific network into memory. Parameters keep the
            # network identifier out of executable Cypher text.
            node_query = "MATCH (n:Asset {network_id: $network_id}) RETURN id(n) AS id"
            rel_query = """
            MATCH (s:Asset {network_id: $network_id})-[r]->(t:Asset {network_id: $network_id})
            RETURN id(s) AS source, id(t) AS target
            """

            session.run(
                """
                CALL gds.graph.project.cypher(
                    $graph_name,
                    $node_query,
                    $rel_query,
                    {parameters: {network_id: $network_id}}
                ) YIELD graphName, nodeCount, relationshipCount
                """,
                graph_name=graph_name,
                node_query=node_query,
                rel_query=rel_query,
                network_id=network_id,
            )
            graph_created = True

            # Run PageRank on the isolated projection.
            results = session.run(
                """
                CALL gds.pageRank.stream($graph_name)
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).id AS node_id, score
                ORDER BY score DESC
                """,
                graph_name=graph_name,
            ).data()
        finally:
            if graph_created:
                try:
                    session.run("CALL gds.graph.drop($graph_name)", graph_name=graph_name)
                except Exception:
                    logger.exception("failed to drop GDS projection %s", graph_name)

    # 5. Format results with rank
    ranked_results = []
    for idx, row in enumerate(results):
        ranked_results.append({
            "node_id": row["node_id"],
            "score": row["score"],
            "rank": idx + 1,
        })

    if settings.centrality_cache_ttl_seconds:
        try:
            get_redis_client().setex(
                cache_key,
                settings.centrality_cache_ttl_seconds,
                json.dumps(ranked_results),
            )
        except Exception:
            logger.warning("centrality cache write failed", exc_info=True)

    return ranked_results
