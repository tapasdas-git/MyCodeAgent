from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Callable, Iterable, Optional

from .schemas import BookingConfirmation, FlightOption, FlightQuery
from .tools import MockFlightSearchAPI, MockReservationGateway


_SEAT_PATTERN = re.compile(r"\b(window|aisle|middle)\b", re.IGNORECASE)
_AIRPORT_PATTERN = re.compile(r"\b[A-Z]{3}\b")
_DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_BUDGET_PATTERN = re.compile(r"\b(?:budget|under|max(?:imum)?)\s*\$?(\d+(?:\.\d+)?)", re.IGNORECASE)
_BAGS_PATTERN = re.compile(r"\b(\d+)\s*bags?\b", re.IGNORECASE)
_PASSENGERS_PATTERN = re.compile(r"\b(\d+)\s*passengers?\b", re.IGNORECASE)


class SearchAgent:
    def parse_intent(self, request_text: str) -> FlightQuery:
        normalized_request = request_text.upper()
        route_match = re.search(r"\b([A-Z]{3})\s+TO\s+([A-Z]{3})\b", normalized_request)
        airports = _AIRPORT_PATTERN.findall(normalized_request)
        if route_match:
            origin, destination = route_match.group(1), route_match.group(2)
        elif len(airports) >= 2:
            origin, destination = airports[0], airports[1]
        else:
            raise ValueError("request must include origin and destination airport codes")

        departure_date_match = _DATE_PATTERN.search(normalized_request)
        if not departure_date_match:
            raise ValueError("request must include a departure date in YYYY-MM-DD format")

        budget_match = _BUDGET_PATTERN.search(request_text)
        seat_match = _SEAT_PATTERN.search(request_text)
        bags_match = _BAGS_PATTERN.search(request_text)
        passengers_match = _PASSENGERS_PATTERN.search(request_text)

        book = bool(re.search(r"\b(book|reserve|purchase)\b", request_text, re.IGNORECASE))
        nonstop_only = bool(re.search(r"\bnonstop\b", request_text, re.IGNORECASE))

        return FlightQuery(
            origin=origin,
            destination=destination,
            departure_date=date.fromisoformat(departure_date_match.group(1)),
            max_budget=float(budget_match.group(1)) if budget_match else None,
            seat_preference=seat_match.group(1).lower() if seat_match else None,
            bags=int(bags_match.group(1)) if bags_match else 0,
            passengers=int(passengers_match.group(1)) if passengers_match else 1,
            nonstop_only=nonstop_only,
            book=book,
        )

    def search(self, query: FlightQuery, api: MockFlightSearchAPI) -> list[FlightOption]:
        return api.search(query)


@dataclass
class PreferenceEvaluator:
    def filter_options(
        self,
        query: FlightQuery,
        options: Iterable[FlightOption],
        available_seats: Callable[[FlightOption], int] | None = None,
    ) -> list[FlightOption]:
        filtered = list(options)
        if query.max_budget is not None:
            filtered = [option for option in filtered if option.price <= query.max_budget]
        if query.seat_preference is not None:
            filtered = [option for option in filtered if option.seat_preference == query.seat_preference]
        if query.bags > 0:
            filtered = [option for option in filtered if option.bags_allowed >= query.bags]
        if query.nonstop_only:
            filtered = [option for option in filtered if option.nonstop]
        seat_lookup = available_seats or (lambda option: option.seats_available)
        filtered = [option for option in filtered if seat_lookup(option) >= query.passengers]
        return sorted(filtered, key=lambda option: option.price)


@dataclass
class SupervisorOrchestrator:
    search_agent: SearchAgent
    preference_evaluator: PreferenceEvaluator
    flight_api: MockFlightSearchAPI
    reservation_gateway: MockReservationGateway

    def handle_request(self, request_text: str) -> dict[str, object]:
        query = self.search_agent.parse_intent(request_text)
        search_results = self.search_agent.search(query, self.flight_api)
        filtered_results = self.preference_evaluator.filter_options(
            query,
            search_results,
            available_seats=self.reservation_gateway.available_seats,
        )

        if not filtered_results:
            return {
                "query": query,
                "options": [],
                "confirmation": None,
                "message": "No flights matched the requested preferences.",
            }

        selected = filtered_results[0]
        confirmation: Optional[BookingConfirmation] = None
        if query.book:
            try:
                booking_id = self.reservation_gateway.reserve(selected, query)
            except ValueError as exc:
                confirmation = BookingConfirmation(
                    booking_id="",
                    flight_number=selected.flight_number,
                    status="rejected",
                    message=str(exc),
                    total_price=0.0,
                )
            else:
                confirmation = BookingConfirmation(
                    booking_id=booking_id,
                    flight_number=selected.flight_number,
                    status="confirmed",
                    message=f"Booked {selected.flight_number} for {query.origin} to {query.destination}.",
                    total_price=selected.price * query.passengers,
                )

        if confirmation is None:
            response_message = "Flights found."
        elif confirmation.status == "rejected":
            response_message = f"Booking rejected: {confirmation.message}"
        else:
            response_message = "Booking confirmed."

        return {
            "query": query,
            "options": filtered_results,
            "selected_option": selected,
            "confirmation": confirmation,
            "message": response_message,
        }
