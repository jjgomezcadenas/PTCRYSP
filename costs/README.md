# ARGOS cost model

## Startup budget

`costs-reduced.csv` is the independent four-year estimate revised line by line with the user. Calculate it with `load_model(table_names=('costs-reduced',))`. Its funding requirement is EUR 4,000,000, including a fixed EUR 300,000 device contingency and a fixed EUR 252,000 programme reserve. Clinical and external regulatory allowances are EUR 50,000 and EUR 25,000. Lead architect staffing, quality/regulatory staffing, clinical monitoring staffing and working capital are zero; the original budget remains in `costs_startup.csv`. An administrative clerk at EUR 40,000/year employer cost for four years replaces the company administration allowance. An additional fixed EUR 263,000 backup allowance brings the current total to EUR 4M; it remains an editable input when other costs change.

`costs_startup.csv` contains the editable budget from `costs_startup.tex`, using the same input/formula columns as the other models. Amounts are in euros. Edit `value` for inputs; derived rows have only a `formula`. Personnel costs derive from staffing, annual employer cost and funded years. Programme duration controls full-programme roles and annual overhead; technician and monitoring years are separate inputs to review when changing duration.

Calculate the startup budget from the repository root:

```python
from costs.build_costs import load_model
_, _, values, _ = load_model(table_names=('costs_startup',))
print(values['startup_funding'])          # 6660000
print(values['startup_funding_rounded'])  # 6700000
print(values['startup_headroom'])         # 340000
```

The original `costs_startup.csv` remains separate from the presentation workbook and matches the original LaTeX note. The reduced budget now generates the funding-request slide and supplies the linked `startup_team.csv` and `startup_programme.csv` tables. Run the standard generator and rebuild to update the workbook and slides after editing it. Neither startup LaTeX note is automatically regenerated. Three- and five-year ranges in the original note are indicative, not separately calculated budgets.

## Presentation models

The nine CSV files are the source of truth. Each maps to one Excel worksheet/named table and one presentation slide:

| CSV table | Financial slide |
| --- | --- |
| `installation.csv` | Installed-system economics |
| `installation_market.csv` | Bottom-up installation market |
| `annual_service.csv` | Annual services: scope and economics |
| `recurring_market.csv` | Recurring services: annual revenue potential |
| `market_growth.csv` | Proton therapy: market growth |
| `argos_market.csv` | Total potential market |
| `costs-reduced.csv` | Funding request |
| `startup_team.csv` | Development team |
| `startup_programme.csv` | Building the full demonstrator |

All money is in EUR, excluding VAT. Rates are fractions (e.g. `0.05` means 5%). Each row has a stable `id`, label, unit, notes and **either** an input `value` **or** a derived `formula`. Formula identifiers can refer to rows in any of the nine tables. Arithmetic (including exponentiation `**`), `round(value, digits)` and `ceil(value)` are supported; formulas are parsed without Python `eval`. Rounding uses Excel's half-away-from-zero convention.

## Generate and verify

From the repository root:

```sh
python3 -m venv costs/.venv
costs/.venv/bin/python -m pip install -r costs/requirements.txt
costs/.venv/bin/python costs/build_costs.py
latexmk -pdf -interaction=nonstopmode -halt-on-error pbt_argos.tex
costs/.venv/bin/python costs/build_costs.py --check --pdf pbt_argos.pdf
python3 -m unittest discover -s costs -p 'test_*.py'
```

The script works from any current directory; paths for model files are resolved relative to the script. The `--pdf` argument is resolved relative to the current directory. Python 3.9+ and XlsxWriter are needed for workbook generation; `pdftotext` is required for PDF checks. LaTeX rebuilds require the talk's existing TeX installation.

Generated outputs:

- `costs.xlsx`: nine sheets with nine filterable Excel tables. Blue values are editable inputs **for review experiments only**; derived cells have Excel formulas and cached Python-calculated values. Save lasting changes back to CSV and regenerate. Excel edits are not imported automatically.
- `calculated.json`: full-precision values and slide-display metadata for Python consumers.
- `slides.tex` and `slides/<table>.tex`: the nine financial frames, as one block and as one file per frame so the deck can interleave them with other slides; `pbt_argos.tex` includes each `slides/<table>.tex` exactly once. Edit the corresponding `.tex.in` templates for wording/layout, not this generated file. Numeric placeholders such as `{{service_price|k}}` pull values from the model.
- `consistency_report.md`: results for CSV calculations, workbook cached values/formulas, slide count, deck inclusion and optional rendered-PDF number checks. A run without `--pdf` explicitly reports the PDF as unchecked.

`--check` refuses stale generated text/workbook values. It updates only the consistency report, not the model outputs or slides. PDF checks locate each financial slide by title and check all displayed model number strings; they are not a substitute for visual layout inspection. The audit covers these nine financial slides, not unrelated epidemiology or third-party market-survey numbers elsewhere in the deck.

## Manipulate with Python

No pandas dependency is required:

```python
import csv
from pathlib import Path

path = Path('costs/annual_service.csv')
with path.open(newline='') as f:
    rows = list(csv.DictReader(f))
for row in rows:
    if row['id'] == 'country_factor':
        row['value'] = '1.2'  # example only; not the current agreed baseline
with path.open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
```

Then regenerate and rebuild. Or use `pandas.read_csv` / `to_csv(index=False)`, preserving IDs, notes and formula strings. For calculations without exporting:

```python
from costs.build_costs import load_model
tables, rows, values, excel_cells = load_model()
print(values['service_cost'], values['service_margin'])
```

The country factor changes personnel cost only. Agreed selling prices are independent inputs, so a cost change updates margin, not the quoted price. A target-margin price is calculated separately for comparison.

## Accounting and scenario boundaries

- The hardware sub-budgets (cryocooler, spares, calibration, travel) are provisional allocations within the agreed EUR 30k total. Software operating expenses are non-personnel allowances. Supplier scope and staffing availability remain to be validated.
- Spain personnel: salary plus employer allowance, then relief allowance, rounded **up** to the configured increment. Relief is a cost provision for a dedicated position during one shift, not a promise of continuous multi-shift coverage. Country factors are applied after baseline rounding.
- The annual service contract covers local hardware/software and dedicated monitoring support. Treatment decisions remain with the hospital. Hospital electricity/networking, major upgrades and extra shifts are outside the priced scope.
- Central software engineers, expert escalation, sales, regulatory work and company overhead remain company operating expenses funded from gross profit. They are not set to zero; no amount has yet been agreed for them. The reported gross-profit measure follows this planning convention, not a statutory accounting classification.
- Recurring scenarios assume full-year active paying contracts after included installation warranty; no duplicate warranty billing. They are independent volume scenarios, not a forecast of customer acquisition or company share.
- Global room orders are rounded to the nearest room before multiplication. Orders are not same-year installations. Eligible rooms and adoption are assumptions; one-time installed-base potential is not added to annual sales.
- Installation and service margins are proposed commercial-model outcomes, not externally validated market benchmarks.

The growth model uses a provisional 300-room baseline and assumed 3%, 5%, 7% annual net growth. ARGOS market values use the unrounded central projection and existing price inputs, in constant 2026 euros. Cumulative equipment potential covers net room expansion only; annual service potential covers the entire projected room base at full adoption and compatibility. These are total-market ceilings across all suppliers, not company sales forecasts. Construction lists and manufacturer backlogs overlap and are not added.
