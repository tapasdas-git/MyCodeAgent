from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from itertools import count
from typing import Iterable, List

from .schemas import FlightOption, FlightQuery


@dataclass
class MockFlightSearchAPI:
    catalog: List[FlightOption] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.catalog:
            self.catalog = [
                FlightOption(
                    flight_number="AB101",
                    origin="SFO",
                    destination="JFK",
                    departure_date=date(2026, 8, 20),
                    arrival_date=date(2026, 8, 20),
                    price=450.0,
                    seat_preference="window",
                    bags_allowed=1,
                    nonstop=True,
                    seats_available=3,
                ),
                FlightOption(
                    flight_number="AB102",
                    origin="SFO",
                    destination="JFK",
                    departure_date=date(2026, 8, 20),
                    arrival_date=date(2026, 8, 20),
                    price=380.0,
                    seat_preference="aisle",
                    bags_allowed=2,
                    nonstop=False,
                    seats_available=0,
                ),
                FlightOption(
                    flight_number="AB201",
                    origin="SFO",
                    destination="LAX",
                    departure_date=date(2026, 8, 20),
                    arrival_date=date(2026, 8, 20),
                    price=140.0,
                    seat_preference="aisle",
                    bags_allowed=1,
                    nonstop=True,
                    seats_available=5,
                ),
                FlightOption(
                    flight_number="AB202",
                    origin="SFO",
                    destination="JFK",
                    departure_date=date(2026, 8, 21),
                    arrival_date=date(2026, 8, 21),
                    price=300.0,
                    seat_preference="window",
                    bags_allowed=1,
                    nonstop=True,
                    seats_available=2,
                ),
            ]

    def search(self, query: FlightQuery) -> list[FlightOption]:
        results = [
            option
            for option in self.catalog
            if option.origin == query.origin
            and option.destination == query.destination
            and option.departure_date == query.departure_date
        ]
        if query.nonstop_only:
            results = [option for option in results if option.nonstop]
        return sorted(results, key=lambda option: option.price)


@dataclass
class MockReservationGateway:
    reservation_counter: Iterable[int] = field(default_factory=lambda: count(1))
    inventory: dict[str, int] = field(default_factory=dict)

    def available_seats(self, option: FlightOption) -> int:
        return self.inventory.get(option.flight_number, option.seats_available)

    def reserve(self, option: FlightOption, query: FlightQuery) -> str:
        remaining = self.inventory.setdefault(option.flight_number, option.seats_available)
        if remaining < query.passengers:
            raise ValueError("not enough seats available")
        self.inventory[option.flight_number] = remaining - query.passengers
        return f"BK-{next(self.reservation_counter):05d}"
