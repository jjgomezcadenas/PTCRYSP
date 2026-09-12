"""Model invariants and cross-table propagation, without altering agreed inputs."""
import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from build_costs import ROOT, TABLES, load_model


class CostModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        for name in TABLES:
            shutil.copy(ROOT / f'{name}.csv', self.directory)

    def tearDown(self):
        self.temp.cleanup()

    def change(self, table, key, **changes):
        path = self.directory / f'{table}.csv'
        with path.open(newline='') as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            if row['id'] == key: row.update(changes)
        with path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def values(self):
        return load_model(self.directory)[2]

    def test_agreed_baseline_and_rounding(self):
        v = self.values()
        for key, expected in {'delivered_cost': 1300000, 'installation_price': 2200000,
                              'annual_market': 74800000, 'base_potential': 660000000,
                              'personnel_unrounded': 79200, 'personnel_spain': 80000,
                              'service_cost': 115000, 'service_profit': 85000,
                              'medium_revenue': 20000000, 'medium_profit': 8500000}.items():
            self.assertAlmostEqual(v[key], expected, msg=key)

    def test_installation_price_flows_to_market(self):
        self.change('installation', 'installation_price', value='2400000')
        v = self.values()
        self.assertEqual(v['annual_market'], 34 * 2400000)
        self.assertEqual(v['base_potential'], 300 * 2400000)
        self.assertEqual(v['delivered_cost'], 1300000)

    def test_country_cost_flows_to_recurring_profit_not_ticket(self):
        self.change('annual_service', 'country_factor', value='1.2')
        v = self.values()
        self.assertEqual(v['personnel_annual'], 96000)
        self.assertEqual(v['service_price'], 200000)
        self.assertEqual(v['medium_profit'], 100 * (200000 - 131000))

    def test_adoption_does_not_change_stock_opportunity(self):
        self.change('installation_market', 'new_adoption', value='0.5')
        self.change('installation_market', 'retrofit_adoption', value='0')
        v = self.values()
        self.assertEqual(v['annual_market'], 9.5 * 2200000)
        self.assertEqual(v['base_potential'], 660000000)

    def test_invalid_formula_and_cycle_rejected(self):
        self.change('installation', 'delivered_cost', formula='__import__("os")')
        with self.assertRaises(ValueError): self.values()
        self.change('installation', 'delivered_cost', formula='delivered_cost+1')
        with self.assertRaises(ValueError): self.values()

    def test_invalid_fraction_rejected(self):
        self.change('installation_market', 'new_adoption', value='1.1')
        with self.assertRaises(ValueError): self.values()

    def test_loss_scenario_is_reported_not_rejected(self):
        self.change('annual_service', 'country_factor', value='4')
        v = self.values()
        self.assertEqual(v['service_profit'], -155000)
        self.assertLess(v['service_margin'], 0)


if __name__ == '__main__':
    unittest.main()
