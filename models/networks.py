from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Nodes(Base):
    __tablename__ = "nodes"
    __table_args__ = (
        CheckConstraint("status IN ('published', 'archived')", name="nodes_status_valid"),
    )
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, default="published", server_default="published")

    def __repr__(self):
        return f"<Node {self.name}>"

class Edges(Base):
    __tablename__ = "edges"
    __table_args__ = (
        CheckConstraint("latency > 0", name="edges_latency_positive"),
        CheckConstraint("source <> destination", name="edges_no_self_loop"),
        CheckConstraint("status IN ('published', 'archived')", name="edges_status_valid"),
        UniqueConstraint("source", "destination", name="edges_unique_pair"),
    )
    id = Column(Integer, primary_key=True)
    source = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    destination = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    latency = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="published", server_default="published")

    def __repr__(self):
        return f"<Edge {self.source} -> {self.destination}>"

class RoutesAudit(Base):
    __tablename__ = "routes_audit"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    total_latency = Column(Float, nullable=False)
    path = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False)
    __table_args__ = (
        CheckConstraint("total_latency >= 0", name="routes_audit_total_latency_non_negative"),
        CheckConstraint("json_typeof(path) = 'array'", name="routes_audit_path_is_array"),
    )
    def __repr__(self):
        return f"<RouteAudit {self.source} -> {self.destination}>"