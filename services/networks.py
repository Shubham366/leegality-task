from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from v1.request.networks import Edge, Node, ShortestRoute
from v1.response import BadRequest
from models.networks import Nodes, Edges, RoutesAudit
from connection_utils.db import session
from connection_utils.db.transactional import Transactional
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
    
    async def get_nodes_by_ids(self, node_ids: list[int]):
        result = await session.execute(select(Nodes).where(Nodes.id.in_(node_ids), Nodes.status == "published"))
        return {node.id: node for node in result.scalars().all()}