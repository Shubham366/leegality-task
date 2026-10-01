from fastapi import APIRouter

from v1.request.networks import Edge, Node, ShortestRoute
from v1.response import ApiResponse, BadRequest, NotFound
from services.networks import NetworkService
from services.routes import RouteService
router = APIRouter(prefix="/v1")

@router.post("/node")
async def create_node(node: Node):

    network_service = NetworkService()
    try:
        node = await network_service.create_node(node)
    except BadRequest as error:
        return ApiResponse.response_bad_request(message=error.message)
    except Exception as e:
        return ApiResponse.response_error(message=str(e))

    return ApiResponse.response_created(data=node)


@router.post("/edge")
async def create_edge(edge: Edge):
    network_service = NetworkService()
    try:
        edge = await network_service.create_edge(edge.to_post())
    except BadRequest as error:
        return ApiResponse.response_bad_request(message=error.message)
    except Exception as e:
        return ApiResponse.response_error(message=str(e))

    return ApiResponse.response_created(data=edge)



@router.get("/routes/shortest")
async def get_shortest_route(route: ShortestRoute):
    router_service = RouteService()
    try:
        route = await router_service.get_and_save_shortest_route(route.to_post())
    except BadRequest as error:
        return ApiResponse.response_bad_request(message=error.message)
    except NotFound as error:
        return ApiResponse.response_not_found(message=error.message)
    except Exception as e:
        return ApiResponse.response_error(message=str(e))

    return ApiResponse.response_ok(data=route)