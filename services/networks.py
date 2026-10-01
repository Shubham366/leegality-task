from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from v1.request.networks import Edge, Node
from v1.response import BadRequest, NotFound
from models.networks import Nodes, Edges
from connection_utils.db import session
from connection_utils.db.transactional import Transactional
from connection_utils.redis.connection import redis_client as redis
from serializers.serializers import EdgeSerializer, NodeSerializer

class NetworkService:
    def __init__(self):
        pass

    @Transactional()
    async def create_node(self, node: Node):
        node = Nodes(name=node.name)
        session.add(node)
        try:
            await session.flush()
        except IntegrityError as error:
            if "UNIQUE constraint failed" in str(error.orig):
                raise BadRequest("duplicate name") from error
            raise
        return NodeSerializer().dump(node)
    
    @Transactional()
    async def create_edge(self, edge: Edge.PostConverter):
        source_name = edge.source.name
        destination_name = edge.destination.name
        nodes_map = await self.validate_nodes([edge.source, edge.destination])
        saved = Edges(
            source=nodes_map[source_name].id,
            destination=nodes_map[destination_name].id,
            latency=edge.latency,
        )
        session.add(saved)
        try:
            await session.flush()
        except IntegrityError as error:
            if "UNIQUE constraint failed" in str(error.orig):
                raise BadRequest("path already exists") from error
            raise
        data = EdgeSerializer().dump(saved)
        data["source"] = source_name
        data["destination"] = destination_name
        return data

    async def validate_nodes(self, nodes: list[Node]):
        names = {node.name for node in nodes}
        result = await session.execute(
            select(Nodes).where(Nodes.name.in_(names), Nodes.status == "published")
        )
        found = result.scalars().all()
        found_names = {node.name for node in found}
        if found_names != names:
            raise BadRequest("nodes not found")
        return {node.name: node for node in found}
    
    async def get_edges(self):
        result = await session.execute(select(Edges).where(Edges.status == "published"))
        return result.scalars().all()

    async def list_nodes(self):
        result = await session.execute(select(Nodes).order_by(Nodes.id))
        return [NodeSerializer().dump(node) for node in result.scalars().all()]

    async def list_edges(self):
        result = await session.execute(select(Edges).order_by(Edges.id))
        edges = result.scalars().all()
        node_ids = {edge.source for edge in edges} | {edge.destination for edge in edges}
        if node_ids:
            nodes_result = await session.execute(select(Nodes).where(Nodes.id.in_(node_ids)))
            nodes = {node.id: node for node in nodes_result.scalars().all()}
        else:
            nodes = {}
        data = []
        for edge in edges:
            dumped = EdgeSerializer().dump(edge)
            source = nodes.get(edge.source)
            destination = nodes.get(edge.destination)
            dumped["source"] = source.name if source else edge.source
            dumped["destination"] = destination.name if destination else edge.destination
            data.append(dumped)
        return data

    def _clear_graph_cache(self):
        keys = list(redis.scan_iter("shortest_path_*"))
        keys.append("edges")
        redis.delete(*keys)

    @Transactional()
    async def delete_node(self, node_id: int):
        result = await session.execute(select(Nodes).where(Nodes.id == node_id))
        node = result.scalar_one_or_none()
        if node is None:
            raise NotFound("node not found")
        node.status = "archived"
        await session.execute(
            update(Edges)
            .where((Edges.source == node_id) | (Edges.destination == node_id))
            .values(status="archived")
        )
        await session.flush()
        self._clear_graph_cache()
        return {"id": node_id, "status": "archived"}

    @Transactional()
    async def delete_edge(self, edge_id: int):
        result = await session.execute(select(Edges).where(Edges.id == edge_id))
        edge = result.scalar_one_or_none()
        if edge is None:
            raise NotFound("edge not found")
        edge.status = "archived"
        await session.flush()
        self._clear_graph_cache()
        return {"id": edge_id, "status": "archived"}
    
    async def get_nodes_by_ids(self, node_ids: list[int]):
        result = await session.execute(select(Nodes).where(Nodes.id.in_(node_ids), Nodes.status == "published"))
        return {node.id: node for node in result.scalars().all()}