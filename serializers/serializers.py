from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from models.networks import Edges, Nodes, RoutesAudit


class NodeSerializer(SQLAlchemyAutoSchema):
    class Meta:
        model = Nodes
        load_instance = True


class EdgeSerializer(SQLAlchemyAutoSchema):
    class Meta:
        model = Edges
        load_instance = True
        include_fk = True

class RoutesAuditSerializer(SQLAlchemyAutoSchema):
    class Meta:
        model = RoutesAudit
        load_instance = True    