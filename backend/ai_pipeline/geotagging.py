"""
Geotagging & Geospatial Coordinate Mapping Module.
Interpolates latitude, longitude, and depth from navigation ping records
along the vessel trackline and projects across-track sonar slant-range offsets.
"""

import math
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np


@dataclass
class NavigationPing:
    ping_index: int
    latitude: float
    longitude: float
    timestamp: str
    depth_m: Optional[float] = 20.0
    heading_deg: Optional[float] = 0.0
    speed_knots: Optional[float] = 3.5


def destination_point(
    lat: float,
    lon: float,
    distance_meters: float,
    bearing_deg: float
) -> Tuple[float, float]:
    """
    Computes destination (lat, lon) given a starting coordinate,
    distance in meters, and bearing angle in degrees (Haversine forward calculation).
    """
    R = 6371000.0  # Earth radius in meters
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg % 360.0)
    
    ang_dist = distance_meters / R
    
    lat2_rad = math.asin(
        math.sin(lat_rad) * math.cos(ang_dist) +
        math.cos(lat_rad) * math.sin(ang_dist) * math.cos(bearing_rad)
    )
    
    lon2_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(ang_dist) * math.cos(lat_rad),
        math.cos(ang_dist) - math.sin(lat_rad) * math.sin(lat2_rad)
    )
    
    return math.degrees(lat2_rad), math.degrees(lon2_rad)


class SonarGeotagger:
    def __init__(
        self,
        pings: Optional[List[NavigationPing]] = None,
        slant_range_m: float = 75.0,
        altitude_m: float = 15.0
    ):
        self.slant_range_m = slant_range_m
        self.altitude_m = altitude_m
        self.pings: List[NavigationPing] = sorted(pings, key=lambda p: p.ping_index) if pings else []

    def set_altitude(self, altitude_m: float) -> None:
        """Update sensor altitude for SRR calculations."""
        self.altitude_m = max(0.5, float(altitude_m))

    @classmethod
    def from_ping_records(
        cls,
        ping_dicts: List[Dict[str, Any]],
        slant_range_m: float = 75.0,
        altitude_m: float = 15.0
    ) -> "SonarGeotagger":
        """Builds geotagger directly from parsed sonar packet records (XTF, JSF, SDF)."""
        pings = []
        for p in ping_dicts:
            pings.append(NavigationPing(
                ping_index=p.get("ping_index", len(pings)),
                latitude=float(p.get("lat", p.get("latitude", 0.0))),
                longitude=float(p.get("lon", p.get("longitude", 0.0))),
                timestamp=str(p.get("timestamp", "")),
                depth_m=float(p.get("depth_m", p.get("depth", 20.0))),
                heading_deg=float(p.get("heading_deg", p.get("heading", 0.0))),
                speed_knots=float(p.get("speed_knots", p.get("speed", 3.5)))
            ))
        return cls(pings=pings, slant_range_m=slant_range_m, altitude_m=altitude_m)

    @classmethod
    def from_csv_or_json(
        cls,
        file_path_or_str: str,
        slant_range_m: float = 75.0,
        altitude_m: float = 15.0
    ) -> "SonarGeotagger":
        """
        Loads navigation pings from a CSV or JSON file.
        Accepts columns: ping_index, latitude/lat, longitude/lon, timestamp, depth_m/depth, heading/heading_deg
        """
        pings = []
        try:
            if file_path_or_str.endswith(".csv"):
                df = pd.read_csv(file_path_or_str)
            else:
                df = pd.read_json(file_path_or_str)
                
            # Normalize column names
            df.columns = [c.lower().strip() for c in df.columns]
            
            lat_col = next((c for c in ["latitude", "lat", "y"] if c in df.columns), None)
            lon_col = next((c for c in ["longitude", "lon", "lng", "x"] if c in df.columns), None)
            ping_col = next((c for c in ["ping_index", "ping", "index", "id"] if c in df.columns), None)
            time_col = next((c for c in ["timestamp", "time", "date", "datetime"] if c in df.columns), None)
            depth_col = next((c for c in ["depth_m", "depth", "altitude"] if c in df.columns), None)
            heading_col = next((c for c in ["heading_deg", "heading", "course"] if c in df.columns), None)
            
            if lat_col and lon_col:
                for idx, row in df.iterrows():
                    p_idx = int(row[ping_col]) if ping_col else int(idx)
                    lat = float(row[lat_col])
                    lon = float(row[lon_col])
                    ts = str(row[time_col]) if time_col else datetime.now(timezone.utc).isoformat()
                    depth = float(row[depth_col]) if depth_col and not pd.isna(row[depth_col]) else 25.0
                    heading = float(row[heading_col]) if heading_col and not pd.isna(row[heading_col]) else 0.0
                    
                    pings.append(NavigationPing(
                        ping_index=p_idx,
                        latitude=lat,
                        longitude=lon,
                        timestamp=ts,
                        depth_m=depth,
                        heading_deg=heading
                    ))
        except Exception as e:
            print(f"Warning: Failed to parse navigation metadata ({e}). Using synthetic trackline.")
            
        return cls(pings=pings, slant_range_m=slant_range_m, altitude_m=altitude_m)

    @classmethod
    def generate_synthetic_trackline(
        cls,
        num_pings: int = 1024,
        start_lat: float = 36.6025,
        start_lon: float = -121.8970,
        heading_deg: float = 45.0,
        speed_knots: float = 3.5,
        ping_rate_hz: float = 5.0,
        slant_range_m: float = 75.0,
        altitude_m: float = 15.0
    ) -> "SonarGeotagger":
        """
        Generates a realistic vessel trackline for surveys without explicit GPS logs.
        Default location: Monterey Bay National Marine Sanctuary.
        """
        pings = []
        speed_mps = speed_knots * 0.514444
        dt = 1.0 / ping_rate_hz
        dist_per_ping = speed_mps * dt
        
        cur_lat = start_lat
        cur_lon = start_lon
        base_time = datetime.now(timezone.utc).timestamp()
        
        for idx in range(num_pings):
            # Slight wave drift / heading sway
            sway_heading = heading_deg + 2.0 * math.sin(idx * 0.05)
            cur_lat, cur_lon = destination_point(cur_lat, cur_lon, dist_per_ping, sway_heading)
            
            ping_time = datetime.fromtimestamp(base_time + idx * dt, tz=timezone.utc).isoformat()
            depth = 28.0 + 3.0 * math.sin(idx * 0.01)
            
            pings.append(NavigationPing(
                ping_index=idx,
                latitude=cur_lat,
                longitude=cur_lon,
                timestamp=ping_time,
                depth_m=round(depth, 1),
                heading_deg=round(sway_heading, 1)
            ))
            
        return cls(pings=pings, slant_range_m=slant_range_m, altitude_m=altitude_m)

    def geotag_pixel(
        self,
        pixel_x: int,
        pixel_y: int,
        image_width: int,
        image_height: int,
        nadir_x: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Maps a 2D waterfall image pixel (pixel_x, pixel_y) to geospatial coordinates
        using true Slant-Range to Ground-Range (SRR) geometric correction:
        1. Vertical y-coordinate -> ping index along trackline.
        2. Interpolates vessel lat, lon, heading, timestamp at that ping.
        3. Horizontal x-coordinate -> across-track ground range R_g = sqrt(max(0, R_s^2 - H^2)).
        4. Calculates target (lat, lon) using forward geodetic projection.
        """
        if not self.pings:
            self.pings = self.generate_synthetic_trackline(
                num_pings=max(1024, image_height),
                slant_range_m=self.slant_range_m,
                altitude_m=self.altitude_m
            ).pings

        if nadir_x is None:
            nadir_x = image_width // 2

        # Map y to ping index
        total_pings = len(self.pings)
        ratio = max(0.0, min(1.0, pixel_y / float(image_height)))
        ping_pos = ratio * (total_pings - 1)
        
        low_idx = int(math.floor(ping_pos))
        high_idx = int(math.ceil(ping_pos))
        frac = ping_pos - low_idx
        
        p1 = self.pings[low_idx]
        p2 = self.pings[high_idx] if high_idx < total_pings else p1
        
        # Linear interpolation of trackline position
        vessel_lat = p1.latitude + frac * (p2.latitude - p1.latitude)
        vessel_lon = p1.longitude + frac * (p2.longitude - p1.longitude)
        vessel_depth = (p1.depth_m or 20.0) + frac * ((p2.depth_m or 20.0) - (p1.depth_m or 20.0))
        vessel_heading = (p1.heading_deg or 0.0) + frac * ((p2.heading_deg or 0.0) - (p1.heading_deg or 0.0))
        timestamp = p1.timestamp
        ping_index = int(p1.ping_index + frac * (p2.ping_index - p1.ping_index))

        # True Across-Track Ground Range Calculation (SRR)
        half_width_px = image_width / 2.0
        pixel_offset = pixel_x - nadir_x
        norm_r = abs(pixel_offset) / max(1.0, half_width_px)
        slant_r = norm_r * self.slant_range_m
        
        # R_g = sqrt(max(0, R_s^2 - H^2))
        alt = getattr(self, "altitude_m", 15.0) or 15.0
        if slant_r >= alt:
            ground_r = math.sqrt(slant_r**2 - alt**2)
            in_water_column = False
        else:
            # Target located in nadir water column
            ground_r = 0.0
            in_water_column = True
            
        across_track_m = (1.0 if pixel_offset >= 0 else -1.0) * ground_r
        
        # Sonar beam is perpendicular to vessel heading:
        # Starboard (positive offset): heading + 90 deg
        # Port (negative offset): heading - 90 deg
        if across_track_m >= 0:
            target_bearing = (vessel_heading + 90.0) % 360.0
        else:
            target_bearing = (vessel_heading - 90.0) % 360.0
            
        target_dist = abs(across_track_m)
        
        # Target lat/lon via forward geodetic calculation
        det_lat, det_lon = destination_point(vessel_lat, vessel_lon, target_dist, target_bearing)

        # Ground-range resolution at this offset
        max_gr = math.sqrt(max(0.0, self.slant_range_m**2 - alt**2))
        m_per_pixel = max_gr / max(1.0, half_width_px)

        return {
            "latitude": round(det_lat, 7),
            "longitude": round(det_lon, 7),
            "depth_m": round(vessel_depth, 2),
            "vessel_lat": round(vessel_lat, 7),
            "vessel_lon": round(vessel_lon, 7),
            "vessel_heading": round(vessel_heading, 1),
            "across_track_distance_m": round(across_track_m, 2),
            "slant_range_m": round(slant_r, 2),
            "ground_range_m": round(ground_r, 2),
            "sensor_altitude_m": round(alt, 2),
            "in_water_column": in_water_column,
            "ping_index": ping_index,
            "timestamp": timestamp,
            "meters_per_pixel": round(m_per_pixel, 4)
        }

    def calculate_physical_dimensions(
        self,
        bbox_w_px: float,
        bbox_h_px: float,
        pixel_x: int,
        image_width: int,
        nadir_x: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculates physical length, width, and area (in meters) of a detected object,
        correcting for non-linear across-track ground-range scaling and along-track resolution.
        """
        if nadir_x is None:
            nadir_x = image_width // 2
            
        half_w = image_width / 2.0
        px_offset = abs(pixel_x - nadir_x)
        norm_r = px_offset / max(1.0, half_w)
        slant_r = norm_r * self.slant_range_m
        alt = getattr(self, "altitude_m", 15.0) or 15.0
        
        # Ground range derivative d(R_g)/d(R_s) = R_s / sqrt(R_s^2 - H^2)
        if slant_r > (alt + 0.5):
            gr_scale = slant_r / math.sqrt(slant_r**2 - alt**2)
        else:
            gr_scale = 1.0
            
        max_gr = math.sqrt(max(0.0, self.slant_range_m**2 - alt**2))
        base_m_per_px = max_gr / max(1.0, half_w)
        width_m = bbox_w_px * base_m_per_px * min(2.5, max(0.5, gr_scale))
        
        # Along track resolution (ping interval, typically 0.08 - 0.15 m)
        along_track_res = 0.10
        length_m = bbox_h_px * along_track_res
        
        return {
            "width_meters": round(float(width_m), 2),
            "length_meters": round(float(length_m), 2),
            "area_sq_meters": round(float(width_m * length_m), 2),
            "physical_width_m": round(float(width_m), 2),
            "physical_height_m": round(float(length_m), 2),
            "effective_m_per_px_x": round(float(base_m_per_px * min(2.5, max(0.5, gr_scale))), 4),
            "effective_m_per_px_y": round(float(along_track_res), 4)
        }
