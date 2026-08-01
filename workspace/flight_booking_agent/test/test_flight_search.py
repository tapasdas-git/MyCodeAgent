from __future__ import annotations

from datetime import date
from unittest import TestCase

from Coding.agents import PreferenceEvaluator, SearchAgent
from Coding.schemas import FlightOption, FlightQuery
from Coding.tools import MockFlightSearchAPI


class FlightSearchTests(TestCase):
    def setUp(self) -> None:
        self.search_agent = SearchAgent()
        self.evaluator = PreferenceEvaluator()
        self.api = MockFlightSearchAPI()

    def test_parse_intent_extracts_trip_constraints(self) -> None:
        query = self.search_agent.parse_intent(
            "Book SFO to JFK on 2026-08-20 nonstop under $400 with 1 bags and window seat"
        )

        self.assertEqual(
            query,
            FlightQuery(
                origin="SFO",
                destination="JFK",
                departure_date=date(2026, 8, 20),
                max_budget=400.0,
                seat_preference="window",
                bags=1,
                nonstop_only=True,
                book=True,
            ),
        )

    def test_parse_intent_handles_natural_language_route_phrasing(self) -> None:
        query = self.search_agent.parse_intent(
            "Fly SFO to JFK on 2026-08-20 with a window seat"
        )

        self.assertEqual(query.origin, "SFO")
        self.assertEqual(query.destination, "JFK")

    def test_search_returns_matching_routes_only(self) -> None:
        query = FlightQuery(
            origin="SFO",
            destination="JFK",
            departure_date=date(2026, 8, 20),
        )

        results = self.search_agent.search(query, self.api)

        self.assertTrue(results)
        self.assertTrue(all(option.origin == "SFO" for option in results))
        self.assertTrue(all(option.destination == "JFK" for option in results))
        self.assertTrue(all(option.departure_date == date(2026, 8, 20) for option in results))

    def test_preference_evaluator_filters_by_budget_seat_and_bags(self) -> None:
        query = FlightQuery(
            origin="SFO",
            destination="JFK",
            departure_date=date(2026, 8, 20),
            max_budget=400.0,
            seat_preference="window",
            bags=1,
            nonstop_only=True,
        )
        options = [
            FlightOption(
                flight_number="A1",
                origin="SFO",
                destination="JFK",
                departure_date=date(2026, 8, 20),
                arrival_date=date(2026, 8, 20),
                price=450.0,
                seat_preference="window",
                bags_allowed=1,
                nonstop=True,
                seats_available=1,
            ),
            FlightOption(
                flight_number="A2",
                origin="SFO",
                destination="JFK",
                departure_date=date(2026, 8, 20),
                arrival_date=date(2026, 8, 20),
                price=380.0,
                seat_preference="window",
                bags_allowed=1,
                nonstop=True,
                seats_available=1,
            ),
            FlightOption(
                flight_number="A3",
                origin="SFO",
                destination="JFK",
                departure_date=date(2026, 8, 20),
                arrival_date=date(2026, 8, 20),
                price=300.0,
                seat_preference="aisle",
                bags_allowed=2,
                nonstop=True,
                seats_available=1,
            ),
        ]

        filtered = self.evaluator.filter_options(query, options)

        self.assertEqual([option.flight_number for option in filtered], ["A2"])
