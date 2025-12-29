import csv
import sys
import argparse
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

def parse_duration(duration_str):
    """Parses duration string in HH:MM:SS or MM:SS format to timedelta."""
    if not duration_str or duration_str == "--":
        return timedelta(0)
    parts = duration_str.split(':')
    if len(parts) == 3:
        h, m, s = map(float, parts)
        return timedelta(hours=h, minutes=m, seconds=s)
    elif len(parts) == 2:
        m, s = map(float, parts)
        return timedelta(minutes=m, seconds=s)
    return timedelta(0)

def parse_float(val_str):
    """Parses float string, removing commas."""
    if not val_str or val_str == "--":
        return 0.0
    return float(val_str.replace(',', '').replace('"', '')) # Remove quotes just in case

def parse_int(val_str):
    """Parses int string, removing commas."""
    if not val_str or val_str == "--":
        return 0
    return int(val_str.replace(',', '').replace('"', '').split('.')[0])

def parse_pace_decimal(pace_str):
    """Parses MM:SS string to decimal minutes (e.g., 5:30 -> 5.5)."""
    if not pace_str or pace_str == "--":
        return None
    try:
        parts = pace_str.split(':')
        if len(parts) == 2:
            return float(parts[0]) + float(parts[1]) / 60.0
    except ValueError:
        return None
    return None

def load_data(filepath):
    activities = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse key fields
            try:
                activity = {
                    "type": row.get("Activity Type", "Unknown"),
                    "date": row.get("Date"),
                    "title": row.get("Title"),
                    "distance": parse_float(row.get("Distance", "0")),
                    "calories": parse_int(row.get("Calories", "0")),
                    "time_str": row.get("Time", "00:00:00"),
                    "time": parse_duration(row.get("Time", "00:00:00")),
                    "avg_hr": parse_int(row.get("Avg HR", "0")),
                    "max_hr": parse_int(row.get("Max HR", "0")),
                    "ascent": parse_int(row.get("Total Ascent", "0")),
                    "descent": parse_int(row.get("Total Descent", "0")),
                    "avg_cadence": parse_int(row.get("Avg Run Cadence", "0")),
                    "max_cadence": parse_int(row.get("Max Run Cadence", "0")),
                    "avg_pace": row.get("Avg Pace", "--"),
                    "best_pace": row.get("Best Pace", "--"),
                }
                
                # Enriched fields
                dt = datetime.strptime(activity["date"], "%Y-%m-%d %H:%M:%S")
                activity["date_obj"] = dt
                activity["date_display"] = dt.strftime("%Y-%m-%d")
                
                # Normalize distance
                # Track Running is always in meters in this CSV export
                if activity["type"] == "Track Running":
                    activity["distance"] = activity["distance"] / 1000.0
                # Heuristic for others (in case of other meter-based types)
                elif activity["distance"] > 1000:
                    activity["distance"] = activity["distance"] / 1000.0

                activities.append(activity)
            except ValueError as e:
                print(f"Skipping row due to error: {e}, Row: {row}")
                continue
                
    return activities

def calculate_statistics(activities):
    stats = {
        "total_distance": 0.0,
        "total_duration": timedelta(0),
        "total_calories": 0,
        "total_activities": len(activities),
        "activity_types": {}
    }
    
    for act in activities:
        stats["total_distance"] += act["distance"]
        stats["total_duration"] += act["time"]
        stats["total_calories"] += act["calories"]
        
        atype = act["type"]
        if atype not in stats["activity_types"]:
            stats["activity_types"][atype] = {"count": 0, "distance": 0.0, "duration": timedelta(0)}
        
        stats["activity_types"][atype]["count"] += 1
        stats["activity_types"][atype]["distance"] += act["distance"]
        stats["activity_types"][atype]["duration"] += act["time"]
        
        # Monthly Aggregation
        month_key = act["date_obj"].strftime("%Y-%m")
        if "monthly" not in stats:
            stats["monthly"] = {}
        if month_key not in stats["monthly"]:
            stats["monthly"][month_key] = 0.0
        stats["monthly"][month_key] += act["distance"]

    # Cumulative Distance (Year to Date)
    # Sort ascending for calculation
    sorted_acts = sorted(activities, key=lambda x: x["date_obj"])
    cumulative = []
    running_total = 0.0
    for act in sorted_acts:
        running_total += act["distance"]
        cumulative.append({
            "date": act["date_display"],
            "total": running_total
        })
    stats["cumulative"] = cumulative

    # Scatter Plot Data (Pace vs HR)
    # Only include activities with valid pace and HR
    scatter_data = []
    for act in activities:
        # Use existing 'avg_pace' field but we need to re-parse it or parse it during load.
        # Let's parse it here safely or assume we parsed it in load_data if we updated it.
        # Wait, I didn't update load_data yet. I should do that or parse here.
        # Parsing here is safer to avoid changing load_data return structure too much, 
        # but cleaner to do in load_data.
        # I'll enable parsing in load_data in a separate edit or just do it here to minimize file touches?
        # Let's do it here to keep the Logic in calculate_statistics for now, 
        # but wait, I defined parse_pace_decimal global.
        
        pace_dec = parse_pace_decimal(act.get("avg_pace"))
        hr = act.get("avg_hr")
        
        if pace_dec and hr > 0 and "Running" in act["type"]: # Filter for Running types mostly
            scatter_data.append({
                "x": pace_dec,
                "y": hr,
                "type": act["type"],
                "title": act["title"],
                "date": act["date_display"]
            })
    stats["scatter_data"] = scatter_data

    # Cadence Distribution
    buckets = {
        "< 150": 0,
        "150-160": 0,
        "160-170": 0,
        "170-180": 0,
        "180+": 0
    }
    for act in activities:
        cad = act.get("avg_cadence", 0)
        if cad > 0 and "Running" in act["type"]:
            if cad < 150:
                buckets["< 150"] += 1
            elif 150 <= cad < 160:
                buckets["150-160"] += 1
            elif 160 <= cad < 170:
                buckets["160-170"] += 1
            elif 170 <= cad < 180:
                buckets["170-180"] += 1
            else:
                buckets["180+"] += 1
    stats["cadence_dist"] = buckets

    # Leaderboards
    # Top 5 Longest Runs
    # Filter for running to avoid potentially long bike rides confusing "Long Run" stats 
    # (though user might want both. Let's stick to "Longest Activities" generally or just Running if dominant).
    # Based on data seen, it's mixed. Let's do "Longest Activities" but maybe show type.
    sorted_dist = sorted(activities, key=lambda x: x["distance"], reverse=True)
    stats["top_distance"] = sorted_dist[:5]

    # Top 5 Climbs (Ascent)
    sorted_ascent = sorted(activities, key=lambda x: x["ascent"], reverse=True)
    stats["top_climb"] = sorted_ascent[:5]

    # HR Zone Distribution (Heart Rate Reserve)
    # Max: 182, Rest: 50
    # Reserve = 132
    # Z1: 50-60% of Range + Rest
    # Z2: 60-70%
    # Z3: 70-80%
    # Z4: 80-90%
    # Z5: 90-100%
    
    max_hr = 182
    rest_hr = 50
    hrr = max_hr - rest_hr
    
    # Calculate thresholds
    z1_low = (hrr * 0.50) + rest_hr
    z2_low = (hrr * 0.60) + rest_hr
    z3_low = (hrr * 0.70) + rest_hr
    z4_low = (hrr * 0.80) + rest_hr
    z5_low = (hrr * 0.90) + rest_hr
    
    hr_zones = {
        "Z1 (Recovery)": 0,
        "Z2 (Aerobic)": 0,
        "Z3 (Tempo)": 0,
        "Z4 (Threshold)": 0,
        "Z5 (Anaerobic)": 0
    }
    
    for act in activities:
        hr = act.get("avg_hr", 0)
        if hr > 0 and "Running" in act["type"]:
            if hr < z1_low:
                 # Below Z1, maybe ignore or count as Z1/Recovery? Let's skip valid runs with super low HR as errors or recovery.
                 # Actually, let's just count as Z1 if it's reasonable, or separate bucket.
                 if hr > 40: hr_zones["Z1 (Recovery)"] += 1
            elif z1_low <= hr < z2_low:
                hr_zones["Z1 (Recovery)"] += 1
            elif z2_low <= hr < z3_low:
                hr_zones["Z2 (Aerobic)"] += 1
            elif z3_low <= hr < z4_low:
                hr_zones["Z3 (Tempo)"] += 1
            elif z4_low <= hr < z5_low:
                hr_zones["Z4 (Threshold)"] += 1
            else:
                hr_zones["Z5 (Anaerobic)"] += 1
                
    stats["hr_zones"] = hr_zones
        
    return stats

def main():
    parser = argparse.ArgumentParser(description='Generate Garmin Activity Report')
    parser.add_argument('csv_file', help='Path to the Garmin CSV file')
    args = parser.parse_args()

    activities = load_data(args.csv_file)
    stats = calculate_statistics(activities)
    
    # Sort activities by date desc
    activities.sort(key=lambda x: x["date_obj"], reverse=True)

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    
    output_html = template.render(
        activities=activities,
        stats=stats,
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(output_html)
        
    print(f"Report generated: report.html")

if __name__ == "__main__":
    main()
