#!/usr/bin/env python3
"""
Adjust GeoJSON coordinates slightly to generate non-identical geofence hashes.

Testing use case:
- Your backend rejects a farm when the geofence hash matches an existing one.
- This script translates each feature by a tiny random offset so hashes differ.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Any


def meters_to_lat_degrees(meters: float) -> float:
    # Approximation: 1 degree latitude ~= 111_320 meters.
    return meters / 111_320.0


def meters_to_lon_degrees(meters: float, lat_deg: float) -> float:
    # Approximation scaled by latitude for longitude shrinkage toward poles.
    cos_lat = math.cos(math.radians(lat_deg))
    if abs(cos_lat) < 1e-12:
        return 0.0
    return meters / (111_320.0 * cos_lat)


def clamp_lat(lat: float) -> float:
    return max(-90.0, min(90.0, lat))


def wrap_lon(lon: float) -> float:
    while lon > 180.0:
        lon -= 360.0
    while lon < -180.0:
        lon += 360.0
    return lon


def is_position(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    )


def offset_position(position: list[Any], d_lat: float, d_lon: float) -> list[Any]:
    lon = wrap_lon(float(position[0]) + d_lon)
    lat = clamp_lat(float(position[1]) + d_lat)
    out = [lon, lat]
    if len(position) > 2:
        out.extend(position[2:])
    return out


def apply_offset_recursive(coords: Any, d_lat: float, d_lon: float) -> Any:
    if is_position(coords):
        return offset_position(coords, d_lat, d_lon)
    if isinstance(coords, list):
        return [apply_offset_recursive(item, d_lat, d_lon) for item in coords]
    return coords


def close_polygon_rings(geometry: dict[str, Any]) -> None:
    geom_type = geometry.get("type")
    if geom_type == "Polygon":
        for ring in geometry.get("coordinates", []):
            if ring and ring[0] != ring[-1]:
                ring[-1] = ring[0][:]
    elif geom_type == "MultiPolygon":
        for polygon in geometry.get("coordinates", []):
            for ring in polygon:
                if ring and ring[0] != ring[-1]:
                    ring[-1] = ring[0][:]


def random_offset_degrees(max_meters: float, lat_ref: float) -> tuple[float, float]:
    d_lat_m = random.uniform(-max_meters, max_meters)
    d_lon_m = random.uniform(-max_meters, max_meters)
    return meters_to_lat_degrees(d_lat_m), meters_to_lon_degrees(d_lon_m, lat_ref)


def geometry_lat_ref(geometry: dict[str, Any]) -> float:
    coords = geometry.get("coordinates")
    stack = [coords]
    while stack:
        cur = stack.pop()
        if is_position(cur):
            return float(cur[1])
        if isinstance(cur, list):
            stack.extend(cur)
    return 0.0


def adjust_geometry(geometry: dict[str, Any], max_meters: float) -> dict[str, Any]:
    lat_ref = geometry_lat_ref(geometry)
    d_lat, d_lon = random_offset_degrees(max_meters, lat_ref)
    geometry["coordinates"] = apply_offset_recursive(geometry.get("coordinates"), d_lat, d_lon)
    close_polygon_rings(geometry)
    return geometry


def adjust_geojson(doc: dict[str, Any], max_meters: float) -> dict[str, Any]:
    doc_type = doc.get("type")
    if doc_type == "FeatureCollection":
        for feature in doc.get("features", []):
            geometry = feature.get("geometry")
            if isinstance(geometry, dict):
                adjust_geometry(geometry, max_meters)
        return doc
    if doc_type == "Feature":
        geometry = doc.get("geometry")
        if isinstance(geometry, dict):
            adjust_geometry(geometry, max_meters)
        return doc
    if "coordinates" in doc:
        return adjust_geometry(doc, max_meters)
    raise ValueError("Unsupported GeoJSON structure.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Slightly adjust GeoJSON coordinates to avoid identical geofence hashes."
    )
    parser.add_argument("input", type=Path, help="Input GeoJSON file path from your local folder.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Optional output path. If omitted, a new file is created next to input as "
            "<name>_shifted_<timestamp>.geojson"
        ),
    )
    parser.add_argument(
        "--max-offset-meters",
        type=float,
        default=2.0,
        help="Maximum random shift (in meters) on each axis. Default: 2.0",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_offset_meters <= 0:
        raise ValueError("--max-offset-meters must be > 0")
    if args.seed is not None:
        random.seed(args.seed)

    with args.input.open("r", encoding="utf-8-sig") as f:
        doc = json.load(f)

    adjusted = adjust_geojson(doc, args.max_offset_meters)

    if args.output is not None:
        output_path = args.output
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = args.input.with_name(f"{args.input.stem}_shifted_{stamp}.geojson")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(adjusted, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Adjusted GeoJSON written to: {output_path}")


if __name__ == "__main__":
    main()
