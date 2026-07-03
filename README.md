\# Spotify Genre Preference Forecasting



A Python project that analyzes Spotify listening history, enriches tracks with genre metadata from the Last.fm API, and forecasts future music genre preferences using time-series analysis.



Instead of just asking, “What have I been listening to?”, this project asks:



> Can my past listening habits predict what genres I will probably listen to next?



\## Project Overview



This project takes exported Spotify Extended Streaming History data, cleans and processes the listening records, retrieves genre tags for each unique artist-track pair using the Last.fm API, and builds weekly genre trends.



The final output is a forecast of likely genre preferences over the next several weeks.



Example idea:



> “Just checked the forecast: there’s a 42% chance I’ll be listening to R\&B next week.”



\## Features



\* Parses Spotify Extended Streaming History JSON files

\* Filters out short plays to focus on meaningful listening activity

\* Handles missing or incomplete artist/track metadata

\* Fetches genre tags from the Last.fm API

\* Uses local caching to avoid repeated API calls

\* Deduplicates artist-track pairs before API requests

\* Aggregates listening history into weekly genre trends

\* Calculates weekly genre shares

\* Forecasts future genre preferences

\* Exports clean CSV files for further analysis or visualization

\* Designed to support future external factors such as:



&#x20; \* calendar events

&#x20; \* seasonal trends

&#x20; \* concerts

&#x20; \* social events

&#x20; \* personal life events



\## Tech Stack



\* Python

\* pandas

\* NumPy

\* requests

\* tqdm

\* statsmodels

\* Last.fm API



\## Why I Built This



Music taste changes over time, but those changes are not always random. They can be influenced by mood, seasons, routines, social environments, and major life events.



I built this project to explore whether my own Spotify listening history could be transformed into a forecasting problem. The goal was to combine data cleaning, API integration, time-series analysis, and personal data storytelling into one practical project.



\## How It Works



The project follows this general pipeline:



```text

Spotify Extended Streaming History

&#x20;       ↓

Clean and filter listening records

&#x20;       ↓

Identify unique artist-track pairs

&#x20;       ↓

Fetch genre metadata from Last.fm

&#x20;       ↓

Cache API results locally

&#x20;       ↓

Merge genres back into listening history

&#x20;       ↓

Aggregate weekly genre listening trends

&#x20;       ↓

Calculate weekly genre shares

&#x20;       ↓

Forecast future genre preferences

```



\## Data Source



This project uses Spotify Extended Streaming History files exported from a personal Spotify account.



Spotify exports these files as JSON and includes information such as:



\* track name

\* artist name

\* timestamp

\* milliseconds played

\* platform

\* country

\* reason the track started or ended



For privacy reasons, this repository does not include my raw Spotify listening history.



\## Genre Enrichment



Spotify streaming history exports do not directly include genre labels for each track. To enrich the dataset, this project uses the Last.fm API to retrieve artist and track tags.



To reduce unnecessary API calls, the script first identifies unique artist-track pairs. For example, if a song appears 50 times in the listening history, the script only fetches its genre once and then merges that result back into the full dataset.



This makes the process faster, more efficient, and less likely to run into API rate limits.



\## Forecasting Approach



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



\## Example Outputs



The script can generate files such as:



```text

spotify\_data\_with\_genres.csv

weekly\_genre\_minutes.csv

weekly\_genre\_shares.csv

genre\_preference\_forecast.csv

```



These files can be used to create charts, dashboards, LinkedIn visuals, or further analysis in Python, Excel, Tableau, or Power BI.



\## Privacy and Security



This repository does not include:



\* raw Spotify listening history

\* Last.fm API keys

\* personal event data

\* generated CSV outputs

\* local cache files



The Last.fm API key should be stored as an environment variable, not hardcoded in the script.



\## Setup Instructions



\### 1. Clone the repository



```bash

git clone https://github.com/YOUR\_USERNAME/spotify-genre-forecast.git

cd spotify-genre-forecast

```



\### 2. Install dependencies



```bash

pip install -r requirements.txt

```



\### 3. Set your Last.fm API key



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



\### 4. Add your Spotify data



Place your Spotify Extended Streaming History JSON files in a local folder.



The script expects files with names similar to:



```text

Streaming\_History\_Audio\_2021.json

Streaming\_History\_Audio\_2022.json

Streaming\_History\_Audio\_2023.json

```



Your raw Spotify files should stay local and should not be committed to GitHub.



\### 5. Run the script



```bash

python spotify\_genre\_trend\_forecaster.py

```



\## Recommended `.gitignore`



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



\## Future Improvements



Planned improvements include:



\* Adding calendar and seasonal features

\* Incorporating concerts, trips, and social events

\* Adding personal life-event annotations

\* Comparing different forecasting models

\* Building interactive charts or a dashboard

\* Creating genre trend visualizations for LinkedIn

\* Adding model evaluation metrics

\* Supporting multiple forecasting horizons

\* Improving genre normalization and tag filtering



\## Example Use Cases



This project demonstrates skills in:



\* data cleaning

\* API integration

\* feature engineering

\* time-series analysis

\* caching

\* personal data analysis

\* Python scripting

\* exploratory data analysis

\* storytelling with data



\## Project Status



This project is complete.



This version focuses on building a working end-to-end pipeline from raw Spotify history to genre forecasts. Future versions will improve modeling accuracy, visualization, and external factor integration.



\## License



This project is for educational and portfolio purposes.



Do not upload private Spotify data, API keys, or personal event files to this repository.



