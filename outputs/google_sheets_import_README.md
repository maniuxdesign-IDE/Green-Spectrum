# Google Sheets import

The test runner writes a summary CSV here:

- `outputs/green_spectrum_dummy_test_results.csv`

It also writes detailed Google Sheets tabs as separate CSV files here:

- `outputs/green_spectrum_google_sheets_tabs/`

Recommended import order:

1. Import `00_summary.csv` as the first sheet.
2. Import each numbered CSV from `01_...` to `19_...` as additional sheets.
3. Keep the file number prefixes as sheet/tab names so cross-stage comparison remains easy.

A direct Google Sheets API push can be added later, but it requires Google Cloud credentials and OAuth/service-account setup.