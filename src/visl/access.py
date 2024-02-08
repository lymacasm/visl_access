import datetime
import requests
import requests_cache
from bs4 import BeautifulSoup
from utility import get_closest_match
from visl.csv import VislCSV
from io import StringIO
from strenum import StrEnum
from typing import Union

URL = "https://visl.org/webapps/spappz_live/schedule_maint"

# Use caching for results
session = requests_cache.CachedSession("visl_access", expire_after=datetime.timedelta(hours=3))

class Commands(StrEnum):
    CSV = "Excel"
    HTML = "HTML"

class Params(StrEnum):
    ALL = "All"

class WeekDays(StrEnum):
    MONDAY = "1"
    TUESDAY = "2"
    WEDNESDAY = "3"
    THURSDAY = "4"
    FRIDAY = "5"
    SATURDAY = "6"
    SUNDAY = "7"

class ScheduleMaintArgs:
    def __init__(self,
            cmd: Commands = None,
            registration_year: str = None,
            club: Union[str, Params] = Params.ALL,
            season: Union[str, Params] = Params.ALL,
            division: Union[str, Params] = Params.ALL,
            pool: Union[str, Params] = Params.ALL,
            team_id: Union[str, Params] = Params.ALL,
            schedule_type: Union[str, Params] = Params.ALL,
            schedule_name: Union[str, Params] = Params.ALL,
            schedule_status: Union[str, Params] = Params.ALL,
            field_name: Union[str, Params] = Params.ALL,
            start_date: datetime = datetime.date.today(),
            end_date: datetime = datetime.date(9999, 12, 31),
            day_of_week: Union[Params, WeekDays] = Params.ALL,
            start_time: Union[str, Params] = Params.ALL,
            clear_cache = False ):
        self.cmd = str(cmd)
        self.club = str(club)
        self.season = str(season)
        self.division = str(division)
        self.pool = str(pool)
        self.team_id = str(team_id)
        self.schedule_type = str(schedule_type)
        self.schedule_name = str(schedule_name)
        self.schedule_status = str(schedule_status)
        self.field_name = str(field_name)
        self.start_date = start_date
        self.end_date = end_date
        self.day_of_week = str(day_of_week)
        self.start_time = str(start_time)
        self.__clear_cache = clear_cache

        if registration_year is None:
            today = datetime.date.today()
            year = today.year
            if today.month > 6:
                year += 1
            self.registration_year = str(year)
        else:
            self.registration_year = registration_year

    def _get_response(self) -> requests.Response:
        request_dict = {
            "reg_year": self.registration_year,
            "flt_area": self.club,
            "season": self.season,
            "division": self.division,
            "sched_pool": self.pool,
            "team_refno": self.team_id,
            "stype": self.schedule_type,
            "sname": self.schedule_name,
            "sstat": self.schedule_status,
            "fieldref": self.field_name,
            "fdate": self.start_date.strftime("%#m/%#d/%Y"),
            "tdate": self.end_date.strftime("%#m/%#d/%Y"),
            "dow": self.day_of_week,
            "start_time": self.start_time,
            "sortby1": "sched_time",
            "sortby2": "sched_type",
            "sortby3": "sched_name",
            "sortby4": "None",
            "appid": "visl",
            "returnto": "",
            "firsttime": "0"
        }
        if self.cmd is not None:
            request_dict['cmd'] = self.cmd

        return session.get(URL, params=request_dict, force_refresh=self.__clear_cache)

def _get_dropdown_options(request_args: ScheduleMaintArgs, dropdown_name) -> dict[str, str]:
    # Get the schedules page
    response = request_args._get_response()
    response.raise_for_status()

    # Parse the page
    page_soup = BeautifulSoup(response.text, features="lxml")
    dropdown_items = {}
    dropdown_options = page_soup.find("select", {"name": dropdown_name})
    for dropdown_option in dropdown_options.children:
        if dropdown_option.text.strip() and dropdown_option.text != Params.ALL:
            option_name = dropdown_option.text.strip()
            option_value = dropdown_option.get("value")
            if option_value is not None:
                dropdown_items[option_name] = option_value
    return dropdown_items

def _get_divisions(clear_cache = False) -> dict[str, str]:
    return _get_dropdown_options(ScheduleMaintArgs(clear_cache=clear_cache), "division")

def _get_teams_in_division(division: str, clear_cache = False) -> dict[str, str]:
    return _get_dropdown_options(ScheduleMaintArgs(division=str(division), clear_cache=clear_cache), "team_refno")

def _get_clubs(clear_cache = False) -> dict[str, str]:
    return _get_dropdown_options(ScheduleMaintArgs(clear_cache=clear_cache), "flt_area")

def get_team(team_name: str, division: str, clear_cache = False) -> tuple[str, str]:
    # Get division
    divisions = _get_divisions(clear_cache)
    if division in list(divisions.values()):
        # Division is in list of values, just use that (can use div#'s more easily this way as input)
        division_id = division
        print(f'Using division "{division_id}".')
    else:
        # Division not in list of values, find a match on division names
        found_division_name = get_closest_match(division, list(divisions.keys()))
        if found_division_name is None:
            raise NameError(f'Failed to find match for division "{division}". Options: {", ".join(divisions.keys())}')
        print(f'Using division "{found_division_name}".')

        # Grab division id from name
        division_id = divisions[found_division_name]

    # Get team in division
    teams = _get_teams_in_division(division_id, clear_cache)
    found_team_name = get_closest_match(team_name, list(teams.keys()))
    if found_team_name is None:
        raise NameError(f'Failed to find match for team name "{team_name}". Options: {", ".join(teams.keys())}')
    print(f'Using team "{found_team_name}".')
    return (found_team_name, teams[found_team_name])

def get_club(club_name: str, clear_cache = False) -> tuple[str, str]:
    clubs = _get_clubs(clear_cache)
    found_club_name = get_closest_match(club_name, list(clubs.keys()))
    if found_club_name is None:
        raise NameError(f'Failed to find match for club name "{club_name}". Options: {", ".join(clubs.keys())}')
    print(f'Using club "{found_club_name}".')
    return (found_club_name, clubs[found_club_name])

def get_csv_str(sched_args: ScheduleMaintArgs) -> str:
    response = sched_args._get_response()
    response.raise_for_status()
    return response.text

def get_visl_csv(team_name: str, sched_args: ScheduleMaintArgs) -> VislCSV:
    response = sched_args._get_response()
    response.raise_for_status()

    f = StringIO(response.text)
    return VislCSV(team_name, f, close_handle=True)