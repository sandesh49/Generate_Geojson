# generate-geojson

Small utility project to generate a slightly shifted GeoJSON so geofence hashes are less likely to match existing farms during testing.

## Requirements

- Python 3.9+

## Usage

Set your files directly inside `adjust_geojson.py` in `DEFAULT_INPUT_FILES`, then run:

```bash
python adjust_geojson.py
```

CMD (Windows):

```cmd
cd /d E:\QA_Assesment-1
python adjust_geojson.py
```

If `python` is not recognized:

```cmd
cd /d E:\QA_Assesment-1
py adjust_geojson.py
```

This processes all configured files and creates outputs automatically in the same folder:

`<original_name>_shifted_YYYYMMDD_HHMMSS.geojson`

Optional flags:

- `--max-offset-meters 4.0` maximum random offset in meters (default `4.0`)
- `--seed 123` make output reproducible
- `--output-dir "C:\path\to\output_folder"` save all outputs in one folder

Example:

```bash
python adjust_geojson.py --max-offset-meters 5
```

You can still pass one or many files directly if needed:

```bash
python adjust_geojson.py "C:\path\a.geojson" "C:\path\b.geojson"
```

## Notes

- Each geometry is translated by a small random amount (latitude/longitude).
- Polygon rings are re-closed after shifting.
- Keep offsets small so farm boundaries stay realistic for your test scenarios.
