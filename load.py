import csv
import io
from datetime import datetime

import requests
import clickhouse_connect

URL = "https://api.open-meteo.com/v1/forecast"
CITIES = {
    "Berlin": (52.52, 13.41),
    "Moscow": (55.75, 37.62),
}


def fetch_csv(lat: float, lon: float) -> str:
    resp = requests.get(
        URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m",
            "past_days": 7,
            "forecast_days": 1,
            "format": "csv",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.text


def parse(text: str):
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("time,"))
    reader = csv.reader(io.StringIO("\n".join(lines[start:])))
    next(reader)
    for row in reader:
        if row and row[1] != "":
            yield row[0], row[1]


def main():
    client = clickhouse_connect.get_client(host="localhost", port=8123)

    rows = []
    for city, (lat, lon) in CITIES.items():
        for ts, temp in parse(fetch_csv(lat, lon)):
            ts = datetime.fromisoformat(ts)
            rows.append([city, ts, temp])

    client.insert("weather", rows, column_names=["city", "ts", "temp"])
    print(f"inserted {len(rows)} rows")


if __name__ == "__main__":
    main()
