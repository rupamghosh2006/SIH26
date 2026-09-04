"""
Unit tests for Geotagging and across-track projection.
"""

import pytest
from ai_pipeline.geotagging import SonarGeotagger, destination_point, NavigationPing


def test_destination_point():
    # Start at 0, 0 and move north 111,139 meters (~1 degree latitude)
    lat, lon = destination_point(0.0, 0.0, 111139.0, 0.0)
    assert abs(lat - 1.0) < 0.02
    assert abs(lon - 0.0) < 0.001


def test_synthetic_trackline_generation():
    geotagger = SonarGeotagger.generate_synthetic_trackline(num_pings=500, start_lat=36.6, start_lon=-121.9)
    assert len(geotagger.pings) == 500
    assert geotagger.pings[0].ping_index == 0
    assert geotagger.pings[-1].ping_index == 499


def test_pixel_geotagging():
    geotagger = SonarGeotagger.generate_synthetic_trackline(
        num_pings=1000,
        start_lat=24.55,
        start_lon=-81.78,
        heading_deg=90.0,  # Heading East
        slant_range_m=75.0
    )
    
    # Pixel on starboard side (x > nadir_x)
    # Heading East (90 deg), so starboard beam points South (180 deg)
    res_starboard = geotagger.geotag_pixel(pixel_x=800, pixel_y=500, image_width=1000, image_height=1000, nadir_x=500)
    
    assert "latitude" in res_starboard
    assert "longitude" in res_starboard
    assert res_starboard["across_track_distance_m"] > 0
    # South of vessel lat:
    assert res_starboard["latitude"] < res_starboard["vessel_lat"]
