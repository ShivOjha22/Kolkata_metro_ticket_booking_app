import heapq
from app.db.sqlite_client import get_sqlite_conn


def load_graph():
    

    with get_sqlite_conn() as conn:
        cur = conn.cursor()

        # -----------------------
        # Load stations
        # -----------------------
        cur.execute("""
        SELECT id, name, line
        FROM stations""")

        stations = cur.fetchall()

        stations_by_id = {}
        station_name_to_id = {}

        for row in stations:
            stations_by_id[row["id"]] = {
                "id": row["id"],
                "name": row["name"],
                "line": row["line"]
            }

            # first occurrence is enough
            station_name_to_id.setdefault(row["name"], row["id"])

        # -----------------------
        # Graph
        # -----------------------
        graph = {}

        for sid in stations_by_id:
            graph[sid] = []

        # -----------------------
        # Normal Connections
        # -----------------------
        cur.execute("""
        SELECT station_a_id,
        station_b_id,
        travel_time_minutes,
        fare_inr FROM connections""")

        for row in cur.fetchall():

            graph[row["station_a_id"]].append({

                "to": row["station_b_id"],

                "time": row["travel_time_minutes"],

                "fare": row["fare_inr"],

                "interchange": False

            })

        # -----------------------
        # Interchanges
        # -----------------------
        cur.execute("""
        SELECT station_from_id,
        station_to_id,
        transfer_time_minutes
        FROM interchanges""")

        for row in cur.fetchall():

            graph[row["station_from_id"]].append({

                "to": row["station_to_id"],

                "time": row["transfer_time_minutes"],

                "fare": 0,

                "interchange": True

            })

    return stations_by_id, station_name_to_id, graph


def reconstruct_path(parent, destination):

    path = []

    node = destination

    while node is not None:
        path.append(node)
        node = parent[node]

    path.reverse()

    return path


def get_metro_route(source_name: str, destination_name: str):
    
    stations_by_id, station_name_to_id, graph = load_graph()

    if source_name not in station_name_to_id:
        raise ValueError(f"Unknown source station: {source_name}")

    if destination_name not in station_name_to_id:
        raise ValueError(f"Unknown destination station: {destination_name}")

    source = station_name_to_id[source_name]
    destination = station_name_to_id[destination_name]

    distance = {}
    parent = {}

    for node in graph:
        distance[node] = float("inf")
        parent[node] = None

    distance[source] = 0

    pq = []
    heapq.heappush(pq, (0, source))

    while pq:

        current_distance, current = heapq.heappop(pq)

        if current_distance > distance[current]:
            continue

        if current == destination:
            break

        for edge in graph[current]:

            neighbour = edge["to"]

            new_distance = current_distance + edge["time"]

            if new_distance < distance[neighbour]:

                distance[neighbour] = new_distance

                parent[neighbour] = current

                heapq.heappush(
                    pq,
                    (
                        new_distance,
                        neighbour
                    )
                )

    if distance[destination] == float("inf"):
        raise ValueError("No route exists between selected stations.")

    path = reconstruct_path(parent, destination)

    total_time = 0
    total_fare = 0
    itinerary = []
    interchanges = 0
    
    for i in range(len(path)):
        current = path[i]
        station = stations_by_id[current]

        transfer_to = None
        is_interchange = False

        if i < len(path) - 1:
            nxt = path[i + 1]

            for edge in graph[current]:
                if edge["to"] == nxt:

                    total_time += edge["time"]
                    total_fare += edge["fare"]

                    if edge["interchange"]:
                        is_interchange = True
                        interchanges += 1
                        transfer_to = stations_by_id[nxt]["line"]

                    break

        itinerary.append({
            "station_name": station["name"],
            "line": station["line"],
            "is_interchange": is_interchange,
            "transfer_to": transfer_to
        })

    return {
        "route_summary": {
            "source": source_name,
            "destination": destination_name,
            "total_travel_time_minutes": total_time,
            "total_fare_inr": total_fare,
            "interchanges_count": interchanges
        },
        "ordered_itinerary": itinerary
    }