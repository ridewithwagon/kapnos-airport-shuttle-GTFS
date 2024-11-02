import zipfile
import os

agency = """agency_id,agency_name,agency_lang,agency_timezone,agency_url,agency_phone,agency_email,agency_fare_url
1,Kapnos Airport Shuttle,en,Asia/Nicosia,https://kapnosairportshuttle.com,+357 24 00 87 18,info@kapnosairportshuttle.com,https://kapnosairportshuttle.com/routes"""
trips = "route_id,service_id,trip_id"
stop_times = "trip_id,arrival_time,departure_time,stop_id,stop_sequence"
calendar = "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date"
stops = "stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station,wheelchair_boarding"
routes = "route_id,route_short_name,route_long_name,route_type,route_url"

__id = 0


def id():
    global __id
    __id += 1
    return __id


def stop(stop_name, stop_lat, stop_lon):
    global stops
    stop_point_id = id()
    stop_area_id = id()
    stop_point = f"\n{stop_point_id},{stop_name},{stop_lat},{stop_lon},0,{stop_area_id},0"
    stop_area = f"\n{stop_area_id},{stop_name},{stop_lat},{stop_lon},1,,0"
    stops += (stop_point + stop_area)
    return stop_point_id


def service(monday, tuesday, wednesday, thursday, friday, saturday, sunday, valid_from, valid_to):
    global calendar
    service_id = id()
    calendar += f"\n{service_id},{monday},{tuesday},{wednesday},{thursday},{friday},{saturday},{sunday},{valid_from},{valid_to}"
    return service_id


def route(route_name, route_url):
    global routes
    ROUTE_SHORT_NAME = "Airport Shuttle"
    route_id = id()
    routes += f"\n{route_id},{ROUTE_SHORT_NAME},{route_name},3,{route_url}"
    return route_id


def trip(route_id, service_id):
    global trips
    trip_id = id()
    trips += f"\n{route_id},{service_id},{trip_id}"
    return trip_id


def __append_minutes(time: str,  minutes: int):
    h, m, s = 0, 0, 0
    if len(time) == 8:
        h, m, s = time.split(":")
    else:
        h, m = time.split(":")
    m = int(m) + minutes
    h = int(h) + m // 60
    m = m % 60
    return f"{h:02d}:{m:02d}:{s}"


def add_trip(route_id, service_id,
             start_stop_point_id, end_stop_point_id,
             start_time, travel_time_minutes):
    global stop_times, trips
    trip_id = trip(route_id, service_id)
    start_time = f"{start_time}:00"
    end_time = __append_minutes(start_time, travel_time_minutes)
    stop_times += f"\n{trip_id},{start_time},{start_time},{start_stop_point_id},1"
    stop_times += f"\n{trip_id},{end_time},{end_time},{end_stop_point_id},2"


def add_trips(route_id, service_id,
              start_stop_point_id, end_stop_point_id,
              travel_time_minutes, start_times):
    for start_time in start_times:
        add_trip(route_id, service_id, start_stop_point_id,
                 end_stop_point_id, start_time, travel_time_minutes)


def generate():
    """
    Create all txt files and zip it in a single file
    """
    files = [
        ("agency.txt", agency),
        ("trips.txt", trips),
        ("stop_times.txt", stop_times),
        ("calendar.txt", calendar),
        ("stops.txt", stops),
        ("routes.txt", routes)
    ]
    with zipfile.ZipFile("gtfs.zip", "w") as z:
        for file_name, content in files:
            with open(file_name, "w") as f:
                f.write(content)
            z.write(file_name)
            os.remove(file_name)


if __name__ == "__main__":
    VALID_FROM = "20200101"
    VALID_TO = "20241231"

    week_end_service = service(0, 0, 0, 0, 0, 1, 1, VALID_FROM, VALID_TO)
    week_day_service = service(1, 1, 1, 1, 1, 0, 0, VALID_FROM, VALID_TO)
    week_service = service(1, 1, 1, 1, 1, 1, 1, VALID_FROM, VALID_TO)

    larnaca_airport = stop("Kapnos Bus Station - Larnaca Airport",
                           34.870561341994815, 33.606514350233944)
    nicosia = stop("Kapnos Bus Station - Nicosia (Kyrenias Ave.)",
                   35.14871877404405, 33.37542849791872)

    larnaca_nicosia_route = route(
        "Larnaca - Nicosia", "https://kapnosairportshuttle.com/routes/4/en/1")

    add_trips(larnaca_nicosia_route, week_service,
              larnaca_airport, nicosia, 40,
              ["02:15", "07:45", "09:00", "10:00", "11:45",
               "13:45", "14:45", "15:45", "16:45", "17:45",
               "18:45", "19:45", "20:45", "21:45", "22:45", "23:45"])

    add_trips(larnaca_nicosia_route, week_day_service,
              larnaca_airport, nicosia, 40,
              ["10:30", "11:00", "12:30", "18:15", "20:15"])

    add_trips(larnaca_nicosia_route, week_end_service,
              larnaca_airport, nicosia, 40,
              ["04:45", "05:45", "10:45", "12:45"])

    generate()
