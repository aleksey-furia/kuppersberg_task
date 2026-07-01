CREATE TABLE IF NOT EXISTS weather
(
    city  String,
    ts    DateTime,
    temp  Float64
)
ENGINE = MergeTree
ORDER BY (city, ts);
