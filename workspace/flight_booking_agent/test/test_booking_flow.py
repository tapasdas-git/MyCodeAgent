from __future__ import annotations

from datetime import date
from unittest import TestCase

from Coding.agents import PreferenceEvaluator, SearchAgent, SupervisorOrchestrator
from Coding.schemas import FlightOption, FlightQuery
from Coding.tools import MockFlightSearchAPI, MockReservationGateway


class BookingFlowTests(TestCase):
    def setUp(self) -> None:
        self.search_agent = SearchAgent()
        self.evaluator = PreferenceEvaluator()
        self.api = MockFlightSearchAPI()
        self.gateway = MockReservationGateway()
        self.orchestrator = SupervisorOrchestrator(
            search_agent=self.search_agent,
            preference_evaluator=self.evaluator,
            flight_api=self.api,
            reservation_gateway=self.gateway,
        )

    def test_end_to_end_booking_flow_returns_confirmation(self) -> None:
        result = self.orchestrator.handle_request(
            "Book SFO to JFK on 2026-08-20 nonstop under $500 with 1 bags and window seat"
        )

        self.assertIsNotNone(result["confirmation"])
        confirmation = result["confirmation"]
        self.assertEqual(confirmation.status, "confirmed")
        self.assertEqual(confirmation.flight_number, "AB101")
        self.assertEqual(confirmation.total_price, 450.0)
        self.assertEqual(result["message"], "Booking confirmed.")

    def test_reservation_failure_returns_rejected_confirmation(self) -> None:
        class FailingReservationGateway(MockReservationGateway):
            def reserve(self, option: FlightOption, query) -> str:  # type: ignore[override]
                raise ValueError("gateway unavailable")

        orchestrator = SupervisorOrchestrator(
            search_agent=self.search_agent,
            preference_evaluator=self.evaluator,
            flight_api=MockFlightSearchAPI(
                catalog=[
                    FlightOption(
                        flight_number="ZX8",
                        origin="SFO",
                        destination="JFK",
                        departure_date=date(2026, 8, 20),
                        arrival_date=date(2026, 8, 20),
                        price=260.0,
                        seat_preference="window",
                        bags_allowed=1,
                        nonstop=True,
                        seats_available=1,
                    )
                ]
            ),
            reservation_gateway=FailingReservationGateway(),
        )

        result = orchestrator.handle_request(
            "Book SFO to JFK on 2026-08-20 nonstop under $500 for 1 passenger"
        )

        self.assertIsNotNone(result["confirmation"])
        confirmation = result["confirmation"]
        self.assertEqual(confirmation.status, "rejected")
        self.assertEqual(confirmation.message, "gateway unavailable")
        self.assertEqual(result["message"], "Booking rejected: gateway unavailable")

    def test_end_to_end_booking_skips_sold_out_option(self) -> None:
        result = self.orchestrator.handle_request("Book SFO to JFK on 2026-08-20")

        self.assertIsNotNone(result["confirmation"])
        confirmation = result["confirmation"]
        self.assertEqual(confirmation.flight_number, "AB101")
        self.assertEqual(result["selected_option"].flight_number, "AB101")

    def test_budget_edge_case_returns_no_matching_flights(self) -> None:
        result = self.orchestrator.handle_request(
            "Book SFO to JFK on 2026-08-20 nonstop under $200 with window seat"
        )

        self.assertEqual(result["options"], [])
        self.assertIsNone(result["confirmation"])
        self.assertIn("No flights matched", result["message"])

    def test_reservation_gateway_consumes_inventory_until_exhausted(self) -> None:
        scarce_api = MockFlightSearchAPI(
            catalog=[
                FlightOption(
                    flight_number="ZX9",
                    origin="SFO",
                    destination="JFK",
                    departure_date=date(2026, 8, 20),
                    arrival_date=date(2026, 8, 20),
                    price=250.0,
                    seat_preference="window",
                    bags_allowed=1,
                    nonstop=True,
                    seats_available=2,
                )
            ]
        )
        orchestrator = SupervisorOrchestrator(
            search_agent=self.search_agent,
            preference_evaluator=self.evaluator,
            flight_api=scarce_api,
            reservation_gateway=MockReservationGateway(),
        )

        first = orchestrator.handle_request(
            "Book SFO to JFK on 2026-08-20 nonstop under $500 for 1 passenger"
        )
        second = orchestrator.handle_request(
            "Book SFO to JFK on 2026-08-20 nonstop under $500 for 1 passenger"
        )
        third = orchestrator.handle_request(
            "Book SFO to JFK on 2026-08-20 nonstop under $500 for 1 passenger"
        )

        self.assertEqual(first["confirmation"].booking_id, "BK-00001")
        self.assertEqual(second["confirmation"].booking_id, "BK-00002")
        self.assertIsNone(third["confirmation"])
        self.assertEqual(third["options"], [])
        self.assertIn("No flights matched", third["message"])
