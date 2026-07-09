import os
from datetime import datetime

import requests
import clickhouse_connect

CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "de_user")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "de_password")

URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
USER_AGENT = "kuppersberg-task/1.0 github.com/kuppersberg"
CITIES = {
    "Berlin": (52.52, 13.41),
    "Moscow": (55.75, 37.62),
}


def fetch_forecast(lat: float, lon: float):
    resp = requests.get(
        URL,
        params={"lat": lat, "lon": lon},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    resp.raise_for_status()
    for point in resp.json()["properties"]["timeseries"]:
        temp = point["data"]["instant"]["details"].get("air_temperature")
        if temp is not None:
            yield point["time"], temp


def main():
    client = clickhouse_connect.get_client(
        host="localhost",
        port=8123,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
    )

    rows = []
    for city, (lat, lon) in CITIES.items():
        for ts, temp in fetch_forecast(lat, lon):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
            rows.append([city, ts, float(temp)])

    client.insert("weather", rows, column_names=["city", "ts", "temp"])
    print(f"inserted {len(rows)} rows")


if __name__ == "__main__":
    main()
