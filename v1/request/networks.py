from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

class Node(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class Edge(BaseModel):
    source: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    destination: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    latency: Annotated[float, Field(gt=0)]

    class PostConverter(BaseModel):
        source: Node
        destination: Node
        latency: Annotated[float, Field(gt=0)]

    def to_post(self):
        return self.PostConverter(
            source=Node(name=self.source),
            destination=Node(name=self.destination),
            latency=self.latency,
        )
    

class ShortestRoute(BaseModel):
    source: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    destination: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

    class PostConverter(BaseModel):
        source: Node
        destination: Node
    
    def to_post(self):
        return self.PostConverter(
            source=Node(name=self.source),
            destination=Node(name=self.destination),
        )