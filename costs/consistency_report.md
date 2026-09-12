# Cost model consistency report

- PASS: four CSV tables, four Excel sheets/named tables, four generated financial slides.
- PASS: all 70 input/derived values match Excel cached values; formulas match Python expressions.
- PASS: all displayed model numbers are generated from the CSV calculation model.
- PASS: deck includes the generated slides exactly once.
- Scope: the four installation/service financial slides; unrelated clinical and market-survey slides are outside this audit.
- PASS: installation: rendered PDF page 42; all model number strings found.
- PASS: installation_market: rendered PDF page 43; all model number strings found.
- PASS: annual_service: rendered PDF page 44; all model number strings found.
- PASS: recurring_market: rendered PDF page 45; all model number strings found.
- PDF matching checks displayed numbers and titles, not layout; visual review remains a separate step.
