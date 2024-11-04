import os
import zipfile
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from requests_toolbelt.multipart.encoder import MultipartEncoder

agency = """agency_id,agency_name,agency_lang,agency_timezone,agency_url,agency_phone,agency_email,agency_fare_url
1,Kapnos Airport Shuttle,en,Asia/Nicosia,https://kapnosairportshuttle.com,+357 24 00 87 18,info@kapnosairportshuttle.com,https://kapnosairportshuttle.com/routes"""
trips = "route_id,service_id,trip_id"
stop_times = "trip_id,arrival_time,departure_time,stop_id,stop_sequence"
calendar = "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date"
stops = "stop_id,stop_name,stop_lat,stop_lon,zone_id,location_type,parent_station,wheelchair_boarding"
routes = "route_id,route_short_name,route_long_name,route_type,route_url"
fare_rules = "fare_id,route_id,origin_id,destination_id"
fare_attributes = "fare_id,price,currency_type,payment_method,transfers"

__id = 0


class Period:
    def __convert_date(self, date: str):
        day, month, year = date.split("/")
        return f"{year}{month}{day}"

    def __init__(self, id, start_date, end_date):
        self.id = id
        self.start_date = self.__convert_date(start_date)
        self.end_date = self.__convert_date(end_date)


def id():
    global __id
    __id += 1
    return __id


def stop(stop_name, stop_lat, stop_lon):
    global stops
    stop_point_id = id()
    stop_area_id = id()
    zone_id = stop_point_id
    stop_point = f"\n{stop_point_id},{stop_name},{
        stop_lat},{stop_lon},{zone_id},0,{stop_area_id},0"
    stop_area = f"\n{stop_area_id},{stop_name},{
        stop_lat},{stop_lon},{zone_id},1,,0"
    stops += (stop_point + stop_area)
    return stop_point_id


def service(monday, tuesday, wednesday, thursday, friday, saturday, sunday, valid_from, valid_to):
    global calendar
    service_id = id()
    calendar += f"\n{service_id},{monday},{tuesday},{wednesday},{
        thursday},{friday},{saturday},{sunday},{valid_from},{valid_to}"
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


def add_fare_rule(route_id, origin_id, destination_id, price_eur):
    global fare_rules, fare_attributes
    fare_id = id()
    fare_rules += f"\n{fare_id},{route_id},{origin_id},{destination_id}"
    fare_attributes += f"\n{fare_id},{price_eur},EUR,1,0"


def parse_table(soup: BeautifulSoup) -> Dict[str, List[str]]:
    table = soup.find("table", {"id": "route-table"})
    headers = [th.text.strip() for th in table.find_all("th")]
    schedule = {day: [] for day in headers}

    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) == len(headers):
            for i, cell in enumerate(cells):
                time_text = cell.get_text(strip=True)
                if time_text and time_text != "-":
                    schedule[headers[i]].append(time_text)

    return schedule


def get_adult_price(soup: BeautifulSoup) -> float:
    prices_div = soup.find("div", class_="route-tickets-col")

    for price_div in prices_div.find_all("div", class_="price-div"):
        person = price_div.find("p", class_="person").get_text(strip=True)
        if "Adult" in person:
            price_text = price_div.find(
                "p", class_="price").get_text(strip=True)
            return float(price_text.replace("€", "").replace(",", "."))

    return 0.0


def parse_periods(soup: BeautifulSoup):
    options = soup.find(
        "select", {"name": "period_id"}).find_all("option")
    periods = []
    current_period = None
    for option in options:
        period = Period(option["value"], *option.text.split(" - "))
        if option.has_attr("selected"):
            current_period = period
        else:
            periods.append(period)
    return periods, current_period


def add_trips_from_url(route_id,
                       start_stop_point_id, end_stop_point_id,
                       travel_time_minutes, url):
    print(f"Fetching data from {url}")
    session = requests.Session()
    page = session.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    _token = soup.find("input", {"name": "_token"})["value"]

    periods, current_period = parse_periods(soup)

    periods_schedule = [(current_period, parse_table(soup))]

    print(f"Found period from {current_period.start_date} to {
          current_period.end_date}")

    for period in periods:
        form_data = MultipartEncoder(
            fields={
                "_token": _token,
                "period_id": str(period.id)
            }
        )
        headers = {
            "Content-Type": form_data.content_type
        }
        page = session.post(url, data=form_data, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        periods_schedule.append((period, parse_table(soup)))
        print(f"Found period from {period.start_date} to {period.end_date}")

    for period, schedule in periods_schedule:
        for day, start_times in schedule.items():
            service_id = service(
                int(day == "Monday"),
                int(day == "Tuesday"),
                int(day == "Wednesday"),
                int(day == "Thursday"),
                int(day == "Friday"),
                int(day == "Saturday"),
                int(day == "Sunday"),
                period.start_date,
                period.end_date
            )
            add_trips(route_id, service_id, start_stop_point_id,
                      end_stop_point_id, travel_time_minutes, start_times)

    adult_price_eur = get_adult_price(soup)
    add_fare_rule(route_id, start_stop_point_id,
                  end_stop_point_id, adult_price_eur)
    print(f"Adult price: {adult_price_eur}€")


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
        ("routes.txt", routes),
        ("fare_rules.txt", fare_rules),
        ("fare_attributes.txt", fare_attributes)
    ]
    with zipfile.ZipFile("gtfs.zip", "w") as z:
        for file_name, content in files:
            with open(file_name, "w") as f:
                f.write(content)
            z.write(file_name)
            os.remove(file_name)


if __name__ == "__main__":
    larnaca_airport = stop("Kapnos Bus Station - Larnaca Airport",
                           34.870561341994815, 33.606514350233944)
    paphos_airport = stop("Paphos Airport Bus Station",
                          34.71147673509841, 32.48893335140306)
    nicosia = stop("Kapnos Bus Station - Nicosia (Kyrenias Ave.)",
                   35.14871877404405, 33.37542849791872)

    larnaca_nicosia_route = route(
        "Larnaca - Nicosia", "https://kapnosairportshuttle.com/routes/4/en/1")
    paphos_nicosia_route = route(
        "Paphos - Nicosia", "https://kapnosairportshuttle.com/routes/11/en/1")

    add_trips_from_url(larnaca_nicosia_route, larnaca_airport,
                       nicosia, 40, "https://kapnosairportshuttle.com/routes/4/en/1")

    add_trips_from_url(larnaca_nicosia_route, nicosia, larnaca_airport,
                       40, "https://kapnosairportshuttle.com/routes/5/en/1")

    add_trips_from_url(paphos_nicosia_route, nicosia, paphos_airport,
                       100, "https://kapnosairportshuttle.com/routes/11/en/1")

    add_trips_from_url(paphos_nicosia_route, paphos_airport, nicosia,
                       100, "https://kapnosairportshuttle.com/routes/10/en/1")

    generate()
