# Downhill World Cup Split Analysis

A Python-based system for extracting and analyzing downhill mountain bike timing data from PDF results. This project processes official World Cup timing PDFs and provides interactive analysis through Streamlit applications.

## Features

- **Multi-page PDF processing** for both timed training and qualification results
- **Automatic handling of "Best" column artifacts** - prevents duplicate entries
- **Duplicate detection and removal** - ensures clean data output
- **Consistent CSV output format** compatible with existing Streamlit analysis tools
- **Support for 2025 World Cup season format** with improved parsing logic
- **Interactive web interface** for data visualization and analysis

## Screenshots

### Timed Training Analysis
![Timed Training Dashboard](screenshots/timed_training_dashboard.png)
*Interactive dashboard showing rider performance across multiple runs*

### Qualification Results Analysis  
![Qualification Analysis](screenshots/qualification_analysis.png)
*Split time analysis and sector performance visualization*

### Data Processing
![PDF Processing](screenshots/pdf_processing.png)
*Real-time processing output showing rider extraction progress*

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dh-worldcup-split-analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Processing PDF Files

#### Qualification Results
```bash
python split_pdf_extraction_2025.py
```
This will process `data/leog_2025_dhi_me_results_q1.pdf` and generate `data/leog_2025_dhi_me_results_q1.csv`

#### Timed Training Results
```bash
python tt_split_pdf_extraction.py
```
This will process `data/vdso_2025_dhi_me_results_tt.pdf` and generate `data/vdso_2025_dhi_me_results_tt.csv`

### Running the Analysis Apps

#### Main Application
```bash
streamlit run app.py
```

#### Individual Analysis Modules
```bash
# Timed Training Analysis
streamlit run timed_training.py

# Event Results Analysis  
streamlit run event_results.py
```

## Project Structure

```
dh-worldcup-split-analysis/
├── data/                          # PDF input files and CSV outputs
│   ├── *.pdf                      # Official timing PDFs
│   └── *.csv                      # Processed CSV files
├── split_pdf_extraction_2025.py   # Qualification PDF processor
├── tt_split_pdf_extraction.py     # Timed training PDF processor
├── timed_training.py              # Timed training analysis app
├── event_results.py               # Qualification analysis app
├── app.py                         # Main Streamlit application
├── plot_helper.py                 # Visualization utilities
├── columns.py                     # Column definitions
├── utils.py                       # Utility functions
└── requirements.txt               # Python dependencies
```

## Key Improvements (2025)

### Multi-Page Support
- **Before**: Only processed first page, missing ~70% of riders
- **After**: Processes all pages automatically, captures 100% of riders

### "Best" Column Handling
- **Before**: Created duplicate runs from "Best" column artifacts
- **After**: Automatically detects and skips "Best" column entries

### Duplicate Detection
- **Before**: Multiple runs with identical times were treated as separate runs
- **After**: Intelligent duplicate detection prevents artificial run creation

### Error Handling
- **Before**: Scripts would fail on malformed data
- **After**: Robust error handling with detailed logging

## Data Format

### Input
- Official World Cup timing PDFs from ChronoRace
- Multi-page documents with rider results tables

### Output
- Clean CSV files with consistent column structure
- Individual split times and calculated sector times
- Rider rankings and performance metrics

### CSV Columns
- `rank`, `rider_number`, `name`, `team`, `country`
- `split_1` through `split_4` (intermediate times)
- `sector_1` through `sector_5` (calculated sector times)
- `final_time`, `gap`, `points`
- Performance rankings for all metrics

## Troubleshooting

### Common Issues

**Missing riders in output**
- Ensure PDF has multiple pages - check with `python check_pages.py`
- Verify PDF format matches expected structure

**Duplicate runs appearing**
- Script now automatically handles "Best" column artifacts
- Check if issue persists with latest version

**CSV format errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check PDF structure matches expected format

### Debug Tools

```bash
# Check PDF structure
python check_pages.py

# Find specific rider
python -c "import fitz; doc = fitz.open('data/your_file.pdf'); print([line for line in doc[0].get_text('text').split('\n') if 'RIDER_NAME' in line])"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with sample PDFs
5. Submit a pull request

## License

[Add your license information here]

## Acknowledgments

- UCI World Cup for providing timing data
- ChronoRace for timing system
- Streamlit for the web framework
- PyMuPDF for PDF processing capabilities

---

**Note**: Screenshots should be added to a `screenshots/` directory and referenced in this README. The placeholder text above shows where they should be inserted. 