import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.db.postgres import get_db
from app.models.network import Network, Node, Edge
from app.schemas.network import NetworkBase, NodeBase, EdgeBase, CentralityScore
from app.services.analytics import calculate_centrality
from app.security import enforce_rate_limit, require_viewer

router = APIRouter(
    prefix="/networks",
    tags=["Networks"],
    dependencies=[Depends(require_viewer), Depends(enforce_rate_limit)],
)
logger = logging.getLogger(__name__)


@router.get("", response_model=List[NetworkBase])
def list_networks(limit: int = Query(default=100, ge=1, le=1_000), db: Session = Depends(get_db)):
    """List all available infrastructure networks."""
    return db.query(Network).order_by(Network.created_at.desc()).limit(limit).all()


@router.get("/{network_id}/nodes", response_model=List[NodeBase])
def get_nodes(
    network_id: uuid.UUID,
    limit: int = Query(default=5_000, ge=1, le=10_000),
    db: Session = Depends(get_db),
):
    """Get all nodes for a specific network."""
    nodes = db.query(Node).filter(Node.network_id == network_id).limit(limit).all()
    if not nodes:
        # Check if network exists
        net = db.query(Network).filter(Network.id == network_id).first()
        if not net:
            raise HTTPException(status_code=404, detail="Network not found")
    return nodes


@router.get("/{network_id}/edges", response_model=List[EdgeBase])
def get_edges(
    network_id: uuid.UUID,
    limit: int = Query(default=10_000, ge=1, le=20_000),
    db: Session = Depends(get_db),
):
    """Get all edges for a specific network."""
    network = db.query(Network.id).filter(Network.id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    return db.query(Edge).filter(Edge.network_id == network_id).limit(limit).all()


@router.get("/{network_id}/centrality", response_model=List[CentralityScore])
def get_centrality(network_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Calculate and return PageRank centrality scores for all nodes in the network
    using Neo4j Graph Data Science.
    """
    # Verify network exists
    net = db.query(Network).filter(Network.id == network_id).first()
    if not net:
        raise HTTPException(status_code=404, detail="Network not found")
        
    try:
        results = calculate_centrality(str(network_id))
        return results
    except Exception:
        logger.exception("centrality calculation failed for network %s", network_id)
        raise HTTPException(status_code=503, detail="Centrality service unavailable")
