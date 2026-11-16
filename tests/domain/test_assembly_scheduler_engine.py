from __future__ import annotations

import unittest
from assembly_scheduler.nominations.participant import DomainRecord
from assembly_scheduler.allocation.seat_match import match, agenda_pressure, shortlist


class MatchingTests(unittest.TestCase):
    def record(self, key):
        return DomainRecord(key, {"region_group": "manufacturing", "agenda_priority": 8, "nominee_eligibility": 0.8,
            "availability_window": 90, "seat_class": 7, "expertise_area": 2, "accessibility_need": 0.6,
            "schedule_conflicts": 4, "delegate_capacity": 0.7, "representation_weight": 0.8,
            "timezone_penalty": 1, "participation_debt": 0.9})

    def test_shortlist_prefers_compatible_supplier(self):
        record = self.record("d1")
        suppliers = {"good": {"capacity": .9, "evidence": .9, "localization": .8, "integration": .8, "safety": .9},
                     "weak": {"capacity": .2, "evidence": .3, "localization": .1, "integration": .2, "safety": .1}}
        self.assertEqual(shortlist(record, suppliers, 1)[0].supplier_id, "good")
        self.assertGreater(match(record, "good", suppliers["good"]).fit, match(record, "weak", suppliers["weak"]).fit)

    def test_agenda_pressure_tracks_diversity(self):
        self.assertGreater(agenda_pressure([self.record("a"), self.record("b")])["capacity_mean"], 0.0)
