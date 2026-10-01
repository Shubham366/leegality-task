import json
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from v1.request.networks import Edge, Node, ShortestRoute
from v1.response import BadRequest, NotFound
from models.networks import Nodes, Edges, RoutesAudit
from connection_utils.db import session
from connection_utils.redis.connection import redis_client as redis
from connection_utils.db.transactional import Transactional
from serializers.serializers import EdgeSerializer, NodeSerializer, RoutesAuditSerializer
from services.networks import NetworkService
import heapq

class RouteService:
    def __init__(self):
        self.heap=[]
        self.visited=set()
        self.distances=defaultdict(lambda: float('inf'))
        self.redis=redis

    @Transactional()
    async def get_and_save_shortest_route(self, route: ShortestRoute.PostConverter):
        source_name = route.source.name
        destination_name = route.destination.name
        nodes_map = await NetworkService().validate_nodes([route.source, route.destination])
        source_id = nodes_map[source_name].id
        destination_id = nodes_map[destination_name].id
        shortest_path, total_latency =await self.find_shortest_path(source_id, destination_id)
        nodes_map_reverse = await NetworkService().get_nodes_by_ids(shortest_path)
        shortest_path = [nodes_map_reverse.get(node).name for node in shortest_path]
        route_audit = RoutesAudit(
            source=source_id,
            destination=destination_id,
            total_latency=total_latency,
            path=shortest_path,
            created_at=datetime.now()
        )
        session.add(route_audit)
        await session.flush()
        return {"shortest_path": shortest_path,"total_latency": total_latency}

    async def find_shortest_path(self, source_id, destination_id):
        if self.redis.get(f"shortest_path_{source_id}_{destination_id}"):
            res = json.loads(self.redis.get(f"shortest_path_{source_id}_{destination_id}"))
            return res.get("path"), res.get("latency")
        edges = self.redis.get("edges")
        if not edges:
            edges = await NetworkService().get_edges()
            edges = [EdgeSerializer().dump(edge) for edge in edges]
            self.redis.set("edges", json.dumps(edges), timedelta(minutes=10))
        else:
            edges = json.loads(edges)
        graph = defaultdict(list)
        for edge in edges:
            source = edge.get("source")
            destination = edge.get("destination")
            latency = edge.get("latency")
            graph[source].append((destination, latency))
        
        latency,path = self.dijkstra(graph, source_id, destination_id)
        if not latency:
            raise NotFound("No path exists between servers")
        self.redis.set(f"shortest_path_{source_id}_{destination_id}", json.dumps({"path": path, "latency": latency}), timedelta(minutes=10))
        return path,latency
    

    def dijkstra(self, graph, source_id, destination_id):
        previous = {} 
        best = {source_id: 0.0}   
        heapq.heappush(self.heap, (0.0, source_id))
        while self.heap:
            latency, node = heapq.heappop(self.heap)
            if node == destination_id:
                path = [node]
                while node in previous:
                    node = previous[node]
                    path.append(node)
                return latency, path[::-1]
            if latency > best.get(node, float("inf")):
                continue
            for neighbour, edge_latency in graph.get(node, []):
                candidate = latency + edge_latency
                if candidate < best.get(neighbour, float("inf")):
                    best[neighbour] = candidate
                    previous[neighbour] = node
                    heapq.heappush(self.heap, (candidate, neighbour))
        return None,[]
    

    async def _stored_node_keys(self, value: str) -> list[str]:
        keys = [value]
        result = await session.execute(
            select(Nodes).where(Nodes.name == value, Nodes.status == "published")
        )
        node = result.scalar_one_or_none()
        if node is not None:
            keys.append(str(node.id))
        return keys

    async def get_routes_history(self, source: str | None = None, destination: str | None = None, limit: int = 10, date_from: str | None = None, date_to: str | None = None):
        query = select(RoutesAudit)
        if source is not None:
            query = query.where(RoutesAudit.source.in_(await self._stored_node_keys(source)))
        if destination is not None:
            query = query.where(RoutesAudit.destination.in_(await self._stored_node_keys(destination)))
        if date_from is not None:
            query = query.where(RoutesAudit.created_at >= date_from)
        if date_to is not None:
            if len(date_to) == 10:
                date_to = f"{date_to} 23:59:59.999999"
            query = query.where(RoutesAudit.created_at <= date_to)
        query = query.order_by(RoutesAudit.created_at.desc()).limit(limit)
        result = await session.execute(query)
        routes = [RoutesAuditSerializer().dump(route) for route in result.scalars().all()]
        ids = [
            int(value)
            for route in routes
            for value in (route.get("source"), route.get("destination"))
            if isinstance(value, str) and value.isdigit()
        ]
        if ids:
            nodes = await NetworkService().get_nodes_by_ids(ids)
            for route in routes:
                for key in ("source", "destination"):
                    value = route.get(key)
                    if isinstance(value, str) and value.isdigit():
                        node = nodes.get(int(value))
                        if node is not None:
                            route[key] = node.name
        return routes