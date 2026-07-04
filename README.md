**Spotify Genre Preference Forecasting**



A Python project that analyzes Spotify listening history, enriches tracks with genre metadata from the Last.fm API, and forecasts future music genre preferences using time-series analysis.


Instead of just asking, “What have I been listening to?”, this project asks:

**Can my past listening habits predict what genres I will probably listen to next?**

**Project Overview:**

This project takes exported Spotify Extended Streaming History data, cleans and processes the listening records, retrieves genre tags for each unique artist-track pair using the Last.fm API, and builds weekly genre trends.

The final output is a forecast of likely genre preferences over the next several weeks.

Example idea:

 “Just checked the forecast: there’s a 42% chance I’ll be listening to R\&B next week.”

**Features:**

1. Parses Spotify Extended Streaming History JSON files
2. Filters out short plays to focus on meaningful listening activity
3. Handles missing or incomplete artist/track metadata
4. Fetches genre tags from the Last.fm API
5. Uses local caching to avoid repeated API calls
6. Deduplicates artist-track pairs before API requests
7. Aggregates listening history into weekly genre trends
8. Calculates weekly genre shares
9. Forecasts future genre preferences
10. Exports clean CSV files for further analysis or visualization

**Tech Stack:**

1. Python
2. pandas
3. NumPy
4. requests
5. tqdm
6. statsmodels
7. Last.fm API


**Why I Built This?**

Music taste changes over time, but those changes are not always random. They can be influenced by mood, seasons, routines, social environments, and major life events.

I built this project to explore whether my own Spotify listening history could be transformed into a forecasting problem. The goal was to combine data cleaning, API integration, time-series analysis, and personal data storytelling into one practical project.

**How It Works**

The project follows this general pipeline:



```text

Spotify Extended Streaming History

      ↓

Clean and filter listening records

      ↓

Identify unique artist-track pairs

      ↓

Fetch genre metadata from Last.fm

      ↓

Cache API results locally

      ↓

Merge genres back into listening history

      ↓

Aggregate weekly genre listening trends

      ↓

Calculate weekly genre shares

      ↓

Forecast future genre preferences

```

**Data Source:**

This project uses Spotify Extended Streaming History files exported from a personal Spotify account. Spotify exports these files as JSON and includes information such as:

track name
artist name
timestamp
milliseconds played
platform
country
reason the track started or ended

For privacy reasons, this repository does not include my raw Spotify listening history.


**Genre Enrichment**

Spotify streaming history exports do not directly include genre labels for each track. To enrich the dataset, this project uses the Last.fm API to retrieve artist and track tags. To reduce unnecessary API calls, the script first identifies unique artist-track pairs. For example, if a song appears 50 times in the listening history, the script only fetches its genre once and then merges that result back into the full dataset.
This makes the process faster, more efficient, and less likely to run into API rate limits.



**Forecasting Approach**

The project converts listening history into weekly genre shares.

For example, one week might look like:



```text

R\&B: 42%

Hip-Hop: 28%

Pop: 16%

Afrobeats: 9%

Other: 5%

```
These weekly genre shares are then used to estimate future listening preferences.

The current forecasting approach is intentionally simple and interpretable. Future versions may include more advanced modeling techniques and external regressors such as holidays, seasons, concerts, social events, or major personal events.


**Example Outputs:**

The script can generate files such as:

```text

spotify\_data\_with\_genres.csv

weekly\_genre\_minutes.csv

weekly\_genre\_shares.csv

genre\_preference\_forecast.csv

```

These files can be used to create charts, dashboards, LinkedIn visuals, or further analysis in Python, Excel, Tableau, or Power BI.


**Privacy and Security**

This repository does not include:

raw Spotify listening history
Last.fm API keys
personal event data
generated CSV outputs
local cache files

The Last.fm API key should be stored as an environment variable, not hardcoded in the script.


**Setup Instructions**



1. Clone the repository

```bash

git clone https://github.com/YOUR\_USERNAME/spotify-genre-forecast.git

cd spotify-genre-forecast

```

2. Install dependencies

```bash

pip install -r requirements.txt

```

3. Set your Last.fm API key

Create a free Last.fm API key from Last.fm, then set it as an environment variable.

On Windows PowerShell:

```powershell

setx LASTFM\_API\_KEY "your\_api\_key\_here"

```

Close and reopen PowerShell after running that command.

To confirm the key is available:


```powershell

echo $env:LASTFM\_API\_KEY

```

4. Add your Spotify data

Place your Spotify Extended Streaming History JSON files in a local folder.
The script expects files with names similar to:

```text

Streaming\_History\_Audio\_2021.json

Streaming\_History\_Audio\_2022.json

Streaming\_History\_Audio\_2023.json

```
Your raw Spotify files should stay local and should not be committed to GitHub.


5. Run the script

```bash

python spotify\_genre\_trend\_forecaster.py

```

Recommended `.gitignore`

The repository should ignore private data, API keys, generated outputs, and cache files.


```gitignore

\# Secrets

.env



\# Spotify personal data

Spotify Extended Streaming History/

Streaming\_History\_Audio\*.json

StreamingHistory\*.json



\# Generated output files

spotify\_data\_with\_genres.csv

weekly\_genre\_minutes.csv

weekly\_genre\_shares.csv

genre\_preference\_forecast.csv



\# Cache folders

spotify\_cache/

lastfm\_cache/



\# Python

\_\_pycache\_\_/

\*.pyc

.venv/

venv/



\# OS files

.DS\_Store

Thumbs.db

```

**Future Improvements**

Planned improvements include:

1. Adding calendar and seasonal features
2. Incorporating concerts, trips, and social events
3. Adding personal life-event annotations
4. Comparing different forecasting models
5. Building interactive charts or a dashboard
6. Creating genre trend visualizations for LinkedIn
7. Adding model evaluation metrics
8. Supporting multiple forecasting horizons
9. Improving genre normalization and tag filtering


This project demonstrates skills in:

1. data cleaning
2. API integration
3. feature engineering
4. time-series analysis
5. caching
6. personal data analysis
7. Python scripting
8. exploratory data analysis
9. storytelling with data


**Project Status**

This project is complete.
This version focuses on building a working end-to-end pipeline from raw Spotify history to genre forecasts. Future versions will improve modeling accuracy, visualization, and external factor integration.

**License:**

This project is for portfolio purposes.
Do not upload private Spotify data, API keys, or personal event files to this repository.



