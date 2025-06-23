from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import heapq
import math
from .movement_system import MovementSystem, Tile, TileType, Area
from .web_walking import WebWalking
from .locations import TransportationManager, TransportType, LocationType, TransportNode


@dataclass
class PathSegment:
    """Represents a segment of a path using a specific transportation method."""

    start: Tile
    end: Tile
    transport_type: Optional[TransportType]
    cost: float
    requirements: Dict[str, any]
    interaction_text: str


@dataclass
class Path:
    """Complete path from start to end, possibly using multiple transportation methods."""

    segments: List[PathSegment]
    total_cost: float
    total_distance: float
    requirements: Dict[str, any]


class PathFinder:
    def __init__(
        self,
        movement_system: MovementSystem,
        web_walking: WebWalking,
        transport_manager: TransportationManager,
    ):
        self.movement = movement_system
        self.web_walking = web_walking
        self.transport = transport_manager
        self.cached_paths: Dict[Tuple[Tuple[int, int, int], Tuple[int, int, int]], Path] = {}

    def find_path(self, start: Tile, end: Tile, include_transport: bool = True) -> Optional[Path]:
        """Find the optimal path between two points, using transportation if available."""
        # Check cache first
        cache_key = ((start.x, start.y, start.z), (end.x, end.y, end.z))
        if cache_key in self.cached_paths:
            return self.cached_paths[cache_key]

        # Try direct walking path first
        walking_path = self.web_walking.find_path(start, end)
        if walking_path:
            path = self._create_walking_path(walking_path)
            if path.total_distance <= 30:  # If destination is close, just walk
                self.cached_paths[cache_key] = path
                return path

        if not include_transport:
            return self._create_walking_path(walking_path) if walking_path else None

        # Try using transportation methods
        return self._find_transport_path(start, end)

    def _create_walking_path(self, tiles: List[Tile]) -> Path:
        """Create a path from a list of tiles using walking."""
        if not tiles:
            return None

        segments = []
        total_distance = 0

        for i in range(len(tiles) - 1):
            distance = self.web_walking.calculate_distance(tiles[i], tiles[i + 1])
            total_distance += distance

            segments.append(
                PathSegment(
                    start=tiles[i],
                    end=tiles[i + 1],
                    transport_type=None,
                    cost=distance,
                    requirements={},
                    interaction_text="Walk to",
                )
            )

        return Path(
            segments=segments,
            total_cost=total_distance,
            total_distance=total_distance,
            requirements={},
        )

    def _find_transport_path(self, start: Tile, end: Tile) -> Optional[Path]:
        """Find a path using transportation methods."""

        def heuristic(tile: Tile) -> float:
            return self.web_walking.calculate_distance(tile, end)

        # Priority queue of (cost + heuristic, cost, current_tile, path)
        frontier = []
        heapq.heappush(frontier, (heuristic(start), 0, start, []))
        visited = {(start.x, start.y, start.z): 0}

        while frontier:
            _, current_cost, current_tile, current_path = heapq.heappop(frontier)

            if self.web_walking.calculate_distance(current_tile, end) < 10:
                # Close enough to walk to destination
                final_walking = self.web_walking.find_path(current_tile, end)
                if final_walking:
                    walking_segment = self._create_walking_path(final_walking)
                    complete_path = Path(
                        segments=current_path + walking_segment.segments,
                        total_cost=current_cost + walking_segment.total_cost,
                        total_distance=sum(seg.cost for seg in current_path)
                        + walking_segment.total_distance,
                        requirements=self._merge_requirements(
                            [seg.requirements for seg in current_path]
                        ),
                    )
                    return complete_path

            # Try each transportation method
            for transport_type in TransportType:
                nearest_transport = self.transport.get_nearest_transport(
                    current_tile, transport_type
                )
                if not nearest_transport:
                    continue

                # Check if we can walk to the transport node
                transport_walking = self.web_walking.find_path(
                    current_tile, nearest_transport.source
                )
                if not transport_walking:
                    continue

                # Try each destination from this transport
                for dest_tile, dest_reqs in nearest_transport.destinations:
                    dest_key = (dest_tile.x, dest_tile.y, dest_tile.z)
                    new_cost = current_cost + len(transport_walking) + nearest_transport.cost

                    if dest_key not in visited or new_cost < visited[dest_key]:
                        visited[dest_key] = new_cost

                        # Create path segments
                        walking_segment = self._create_walking_path(transport_walking)
                        transport_segment = PathSegment(
                            start=nearest_transport.source,
                            end=dest_tile,
                            transport_type=transport_type,
                            cost=nearest_transport.cost,
                            requirements=self._merge_requirements(
                                [nearest_transport.requirements, dest_reqs]
                            ),
                            interaction_text=nearest_transport.interaction_text,
                        )

                        new_path = current_path + walking_segment.segments + [transport_segment]
                        priority = new_cost + heuristic(dest_tile)
                        heapq.heappush(frontier, (priority, new_cost, dest_tile, new_path))

        return None

    def _merge_requirements(self, requirement_list: List[Dict[str, any]]) -> Dict[str, any]:
        """Merge multiple requirement dictionaries."""
        merged = {}
        for reqs in requirement_list:
            if not reqs:
                continue
            for key, value in reqs.items():
                if key in merged:
                    if isinstance(value, (int, float)):
                        merged[key] = max(merged[key], value)
                    elif isinstance(value, set):
                        merged[key] = merged[key].union(value)
                    else:
                        merged[key] = value
                else:
                    merged[key] = value
        return merged

    def optimize_path(self, path: Path) -> Path:
        """Optimize a path by removing unnecessary segments."""
        if not path or len(path.segments) <= 2:
            return path

        optimized_segments = [path.segments[0]]
        current_idx = 0

        while current_idx < len(path.segments) - 1:
            # Try to find furthest segment we can directly reach
            for i in range(len(path.segments) - 1, current_idx, -1):
                if path.segments[i].transport_type:
                    # Don't skip transport segments
                    continue

                if self.web_walking.is_path_clear(
                    path.segments[current_idx].end, path.segments[i].end
                ):
                    # Can directly walk to this point
                    optimized_segments.append(path.segments[i])
                    current_idx = i
                    break
            else:
                current_idx += 1
                optimized_segments.append(path.segments[current_idx])

        # Recalculate costs
        total_distance = 0
        total_cost = 0
        for segment in optimized_segments:
            distance = self.web_walking.calculate_distance(segment.start, segment.end)
            total_distance += distance
            total_cost += segment.cost if segment.transport_type else distance

        return Path(
            segments=optimized_segments,
            total_cost=total_cost,
            total_distance=total_distance,
            requirements=path.requirements,
        )

    def find_nearest_bank(self, start: Tile) -> Optional[Path]:
        """Find path to the nearest bank."""
        nearest_bank = self.transport.get_nearest_location(start, LocationType.BANK)
        if nearest_bank:
            return self.find_path(start, nearest_bank.tile)
        return None

    def find_nearest_transport(self, start: Tile, transport_type: TransportType) -> Optional[Path]:
        """Find path to the nearest transportation of a specific type."""
        nearest = self.transport.get_nearest_transport(start, transport_type)
        if nearest:
            return self.find_path(start, nearest.source, include_transport=False)
        return None

    def estimate_path_time(self, path: Path, is_running: bool = False) -> float:
        """Estimate time to complete path in game ticks."""
        total_ticks = 0
        for segment in path.segments:
            if segment.transport_type:
                # Add teleport/transport animation time
                total_ticks += 3
                if segment.transport_type == TransportType.MINIGAME:
                    total_ticks += 2
            else:
                # Walking/running time
                distance = self.web_walking.calculate_distance(segment.start, segment.end)
                ticks_per_tile = 2 if is_running else 4
                total_ticks += distance * ticks_per_tile

        return total_ticks

    def get_path_description(self, path: Path) -> List[str]:
        """Get human-readable description of path."""
        if not path:
            return ["No path found."]

        description = []
        current_transport = None
        transport_steps = 0

        for segment in path.segments:
            if segment.transport_type != current_transport:
                if transport_steps > 0:
                    description.append(f"Walk {transport_steps} tiles")
                    transport_steps = 0

                if segment.transport_type:
                    description.append(segment.interaction_text)
                current_transport = segment.transport_type
            elif not segment.transport_type:
                transport_steps += 1

        if transport_steps > 0:
            description.append(f"Walk {transport_steps} tiles")

        description.append(f"Total distance: {path.total_distance:.1f} tiles")
        if path.requirements:
            description.append("Requirements:")
            for req, value in path.requirements.items():
                description.append(f"- {req}: {value}")

        return description
