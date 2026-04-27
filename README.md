# generate-geojson

Small utility project to generate a slightly shifted GeoJSON so geofence hashes are less likely to match existing farms during testing.

## Requirements

- Python 3.9+

## Usage

```bash
python adjust_geojson.py "C:\path\to\farm.geojson"
```

This creates a new file in the same folder automatically:

`farm_shifted_YYYYMMDD_HHMMSS.geojson`

Optional flags:

- `--max-offset-meters 2.0` maximum random offset in meters (default `2.0`)
- `--seed 123` make output reproducible
- `--output "C:\path\to\new_name.geojson"` set your own output file path

Example:

```bash
python adjust_geojson.py "D:\geo\farm.geojson" --max-offset-meters 1.5
```

## Notes

- Each geometry is translated by a small random amount (latitude/longitude).
- Polygon rings are re-closed after shifting.
- Keep offsets small so farm boundaries stay realistic for your test scenarios.
