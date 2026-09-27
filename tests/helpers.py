from datetime import datetime, timezone


def row(year, group, count=10, hours=(1, 2, 3), *, start=None, end=None, matched=False):
    start = start or f"{year}-01-01T00:00:00Z"
    end = end or f"{year+1}-01-01T00:00:00Z"
    a, b = (datetime.fromisoformat(v.replace("Z", "+00:00")) for v in (start, end))
    seconds = (b-a).total_seconds()
    result = {"year":year,"group":group,"window_start":start,"window_end":end,
              "denominator_seconds":seconds,"incident_count":count,
              "full_hours":hours[0],"full_partial_hours":hours[1],"all_hours":hours[2],
              "availability_full":1-hours[0]*3600/seconds,
              "availability_full_partial":1-hours[1]*3600/seconds,
              "availability_all":1-hours[2]*3600/seconds,
              "partial_year": a != datetime(year,1,1,tzinfo=timezone.utc) or b != datetime(year+1,1,1,tzinfo=timezone.utc),
              "unknown_time_count":0}
    if matched:
        result["count_basis"] = "published_at_utc"
    return result
