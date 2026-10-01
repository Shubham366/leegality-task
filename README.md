# leegality-task

This service stores a directed graph of nodes and edges and finds the lowest-latency path between two nodes.

Nodes and edges live in SQLite. Each edge has a latency greater than 0. A node or edge is `published` while it is in use. `DELETE` does not remove the row; it sets `status` to `archived`. Archived edges are left out of path finding. Archiving a node also archives every edge that uses it.

## Shortest path

`POST /v1/routes/shortest` takes `source` and `destination` and runs Dijkstra on the published edges. The response path is a list of node names, plus the total latency. Each lookup is saved in `routes_audit`.

`GET /v1/routes/history` returns those lookups, newest first. `source`, `destination`, `limit`, `date_from`, and `date_to` are optional. A date-only `date_to` includes the whole day.

## Graph cache

The published graph is cached in Redis so Dijkstra does not read SQLite on every request.

- Key `edges` holds the published edges. It expires after 10 minutes.
- Key `shortest_path_{source_id}_{destination_id}` holds a computed path and its latency, also for 10 minutes.
- Archiving a node or an edge deletes both caches, so the next search rebuilds the graph from the database.

A further step is to keep the adjacency list in Redis and update it when a node or edge is added or archived. Shortest path would then read that list directly. It would not query the database to fetch the graph, and it would not wait for the `edges` key to expire and rebuild and invalidate each time for wrong data.But we kept simple caching for now.

## API

| Method | Path | What it does |
|---|---|---|
| POST | `/v1/node` | Create a node |
| POST | `/v1/edge` | Create an edge (`source`, `destination`, `latency`) |
| GET | `/v1/nodes` | List nodes |
| GET | `/v1/edges` | List edges, with node names on `source` and `destination` |
| DELETE | `/v1/nodes/{id}` | Archive the node and its edges |
| DELETE | `/v1/edges/{id}` | Archive the edge |
| POST | `/v1/routes/shortest` | Shortest path. JSON body: `source`, `destination` |
| GET | `/v1/routes/history` | Past shortest-path lookups |

## Run

Locally, Redis must be on `127.0.0.1:6379`.

```bash
python main.py
```

With Docker, Compose starts Redis first, then builds this image and starts the API on port 8000.

```bash
docker compose up --build
```
