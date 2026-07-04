""" MY GENRE TREND FORECASTER
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
from getpass import getpass

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except ImportError:  # Forecasting still works with a fallback method.
    ExponentialSmoothing = None


# ============================================================
# CONFIGURATION
# ============================================================

LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"

# Change this path if needed.
DATA_PATH = Path(
    r"C:/Users/csyriac/OneDrive - Reconnect Community Health Services/Desktop/Important/Docs/my_spotify_data/Spotify Extended Streaming History"
)

# Output folder. By default, saves next to the Spotify history folder.
OUTPUT_DIR = DATA_PATH.parent

# Cache folder for Last.fm API responses.
CACHE_DIR = OUTPUT_DIR / "lastfm_genre_cache"

# Only keep plays longer than this many milliseconds.
MIN_MS_PLAYED = 60_000

# API pacing. Last.fm is usually okay with this, and cache reduces repeat calls.
SLEEP_SECONDS_BETWEEN_API_CALLS = 0.30

# Forecast settings.
TOP_N_GENRES_TO_FORECAST = 12
FORECAST_WEEKS = 8


# ============================================================
# SAFE VALUE HELPERS
# ============================================================

def safe_text(value: Any, default: str = "unknown") -> str:
    """Return a safe, stripped string for regex/API/cache usage."""
    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass

    try:
        text = str(value).strip()
    except Exception:
        return default

    if not text or text.lower() in {"none", "nan", "null"}:
        return default

    return text


def clean_music_name(value: Any, default: str = "unknown") -> str:
    """Clean artist/track names while never returning None."""
    text = safe_text(value, default)

    # Remove common feature/version clutter.
    text = re.split(r"\s+(feat\.?|ft\.?|featuring)\s+", text, flags=re.IGNORECASE)[0]
    text = re.split(r"[\(\[]", text)[0]

    # Keep common artist/title characters.
    text = re.sub(r"[^\w\s'&-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text or default


def normalize_tags(tags: Any) -> list[dict[str, Any]]:
    """Last.fm sometimes returns a list, a single dict, or no tags."""
    if isinstance(tags, list):
        return [tag for tag in tags if isinstance(tag, dict)]
    if isinstance(tags, dict):
        return [tags]
    return []


# ============================================================
# LAST.FM GENRE FETCHER
# ============================================================

class LastFMGenreFetcher:
    def __init__(self, api_key: str, cache_dir: Path = CACHE_DIR):
        self.api_key = safe_text(api_key, "")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.api_calls = 0

    def _get_cache_path(self, artist_name: Any, track_name: Any = None) -> Path:
        """Create a safe hashed cache path. This avoids regex/filename issues."""
        artist = safe_text(artist_name, "unknown_artist").lower()
        track = safe_text(track_name, "unknown_track").lower()
        raw_key = f"{artist}::{track}"
        hashed_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"

    def get_artist_genres(self, artist_name: Any, track_name: Any = None) -> list[str]:
        """Get genres/tags for an artist, with a track-level fallback."""
        original_artist = safe_text(artist_name, "unknown_artist")
        original_track = safe_text(track_name, "unknown_track")

        clean_artist = clean_music_name(original_artist, "unknown_artist")
        clean_track = clean_music_name(original_track, "unknown_track")

        if clean_artist == "unknown_artist":
            return ["unknown"]

        cache_file = self._get_cache_path(clean_artist, clean_track)

        cached = self._read_cache(cache_file)
        if cached is not None:
            return cached

        self.misses += 1

        genres = self._fetch_artist_tags(clean_artist)

        if (not genres or genres == ["unknown"]) and clean_track != "unknown_track":
            genres = self._fetch_track_tags(clean_artist, clean_track)

        genres = self._clean_genre_list(genres)

        self._write_cache(
            cache_file,
            {
                "artist_name": original_artist,
                "track_name": original_track,
                "clean_artist": clean_artist,
                "clean_track": clean_track,
                "genres": genres,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            },
        )

        return genres

    def _read_cache(self, cache_file: Path) -> list[str] | None:
        if not cache_file.exists():
            return None

        try:
            with cache_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            genres = data.get("genres")
            if isinstance(genres, list) and genres:
                self.hits += 1
                return [safe_text(g, "unknown").lower() for g in genres]
        except Exception:
            # Bad cache files should not crash the run.
            pass

        return None

    def _write_cache(self, cache_file: Path, data: dict[str, Any]) -> None:
        try:
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _fetch_artist_tags(self, artist_name: str, max_retries: int = 3) -> list[str]:
        if not artist_name or artist_name == "unknown_artist":
            return ["unknown"]

        params = {
            "method": "artist.gettoptags",
            "artist": artist_name,
            "api_key": self.api_key,
            "format": "json",
        }

        return self._fetch_tags(params, max_retries=max_retries)

    def _fetch_track_tags(self, artist_name: str, track_name: str, max_retries: int = 3) -> list[str]:
        if not artist_name or not track_name:
            return ["unknown"]

        params = {
            "method": "track.gettoptags",
            "artist": artist_name,
            "track": track_name,
            "api_key": self.api_key,
            "format": "json",
        }

        return self._fetch_tags(params, max_retries=max_retries)

    def _fetch_tags(self, params: dict[str, str], max_retries: int = 3) -> list[str]:
        for attempt in range(max_retries):
            try:
                self.api_calls += 1
                response = requests.get(LASTFM_API_URL, params=params, timeout=15)

                if response.status_code == 429:
                    time.sleep(5)
                    continue

                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    self.errors += 1
                    return ["unknown"]

                data = response.json()

                if "error" in data:
                    # Last.fm error 6 = not found, 29 = rate limit.
                    if data.get("error") == 29 and attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                    return ["unknown"]

                tags = normalize_tags(data.get("toptags", {}).get("tag"))
                return self._extract_genres_from_tags(tags)

            except requests.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                self.errors += 1
                return ["unknown"]
            except Exception:
                self.errors += 1
                return ["unknown"]

        return ["unknown"]

    def _extract_genres_from_tags(self, tags: list[dict[str, Any]]) -> list[str]:
        if not tags:
            return ["unknown"]

        genre_tags: list[str] = []
        fallback_tags: list[str] = []

        for tag in tags[:15]:
            tag_name = safe_text(tag.get("name"), "").lower()
            if not tag_name:
                continue

            tag_name = tag_name.strip()
            fallback_tags.append(tag_name)

            if self._is_likely_genre_tag(tag_name):
                genre_tags.append(tag_name)

            if len(genre_tags) >= 5:
                break

        if genre_tags:
            return self._clean_genre_list(genre_tags)

        if fallback_tags:
            return self._clean_genre_list(fallback_tags[:5])

        return ["unknown"]

    def _is_likely_genre_tag(self, tag: str) -> bool:
        tag = safe_text(tag, "").lower()
        if not tag:
            return False

        non_genres = {
            "seen live", "favorite", "favourite", "favorites", "favourites",
            "love", "loved", "great", "awesome", "amazing", "best", "good",
            "cool", "nice", "perfect", "wonderful", "fantastic", "brilliant",
            "excellent", "superb", "outstanding", "underrated", "overrated",
            "classic", "timeless", "legendary", "masterpiece", "gem", "banger",
            "vibes", "mood", "my favorite", "spotify", "lastfm", "male vocalists",
            "female vocalists", "beautiful", "happy", "sad", "summer", "winter",
        }

        if tag in non_genres:
            return False

        genre_keywords = {
            "rock", "pop", "hip-hop", "hip hop", "rap", "rnb", "r&b", "soul",
            "funk", "disco", "jazz", "blues", "country", "folk", "metal", "punk",
            "indie", "alternative", "electronic", "edm", "house", "techno",
            "trance", "dubstep", "drum and bass", "dnb", "reggae", "ska",
            "classical", "opera", "orchestral", "soundtrack", "ambient",
            "experimental", "avant", "progressive", "psychedelic", "garage",
            "grunge", "emo", "screamo", "hardcore", "post-hardcore", "industrial",
            "new wave", "synth", "synthpop", "vaporwave", "lo-fi", "lofi",
            "acoustic", "trap", "drill", "afrobeats", "afrobeat", "dancehall",
            "latin", "k-pop", "kpop", "j-pop", "jpop", "gospel", "christian",
            "worship", "bluegrass", "americana", "shoegaze", "dream pop",
            "hyperpop", "electropop", "emo rap", "cloud rap", "phonk",
        }

        if any(keyword in tag for keyword in genre_keywords):
            return True

        # Many valid Last.fm genre tags are short single words.
        if len(tag) <= 14 and re.match(r"^[a-z0-9&\-\s]+$", tag):
            return True

        return False

    def _clean_genre_list(self, genres: Any) -> list[str]:
        if not isinstance(genres, list):
            return ["unknown"]

        cleaned: list[str] = []
        seen: set[str] = set()

        for genre in genres:
            text = safe_text(genre, "").lower()
            if not text or text == "unknown":
                continue
            text = re.sub(r"\s+", " ", text).strip()
            if text and text not in seen:
                cleaned.append(text)
                seen.add(text)

        return cleaned[:5] if cleaned else ["unknown"]

    def get_stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total else 0
        return {
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "api_calls": self.api_calls,
            "errors": self.errors,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_files": len(list(self.cache_dir.glob("*.json"))),
            "cache_dir": str(self.cache_dir),
        }


# ============================================================
# SPOTIFY DATA LOADING
# ============================================================

def get_lastfm_api_key() -> str:
    api_key = os.getenv("LASTFM_API_KEY", "").strip()

    if api_key:
        return api_key

    print("\n🔑 Getting Last.fm API key...")
    print("   Get a free key at: https://www.last.fm/api/account/create")
    api_key = input("   Paste your Last.fm API key: ").strip()

    if not api_key:
        raise ValueError("No Last.fm API key provided.")

    return api_key


def find_spotify_history_files(data_path: Path) -> list[Path]:
    if not data_path.exists():
        raise FileNotFoundError(f"Path does not exist: {data_path}")

    patterns = [
        "Streaming_History_Audio*.json",
        "StreamingHistory*.json",
        "endsong*.json",
    ]

    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(data_path.glob(pattern)))

    # Deduplicate while preserving order.
    seen: set[Path] = set()
    unique_files: list[Path] = []
    for file in files:
        if file not in seen:
            unique_files.append(file)
            seen.add(file)

    return unique_files


def load_spotify_history(data_path: Path) -> pd.DataFrame:
    print(f"\n📂 Loading data from: {data_path}")

    files = find_spotify_history_files(data_path)
    if not files:
        raise FileNotFoundError(f"No Spotify streaming history JSON files found in: {data_path}")

    print(f"Found {len(files)} files")

    frames: list[pd.DataFrame] = []

    for file in files:
        print(f"  Loading: {file.name}")
        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            temp_df = pd.DataFrame(data)
            frames.append(temp_df)
            print(f"    Loaded {len(temp_df)} rows")
        except Exception as e:
            print(f"    Error loading {file.name}: {e}")

    if not frames:
        raise ValueError("No data could be loaded.")

    df = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(df)} total rows before filtering")
    return df


def detect_columns(df: pd.DataFrame) -> tuple[str, str, str | None, str | None]:
    """Return track_col, artist_col, timestamp_col, ms_col."""
    if "master_metadata_track_name" in df.columns:
        track_col = "master_metadata_track_name"
        artist_col = "master_metadata_album_artist_name"
    elif "trackName" in df.columns:
        track_col = "trackName"
        artist_col = "artistName"
    else:
        raise ValueError(
            "Could not find track/artist columns. Available columns: "
            + ", ".join(df.columns.astype(str).tolist())
        )

    if "ts" in df.columns:
        timestamp_col = "ts"
    elif "endTime" in df.columns:
        timestamp_col = "endTime"
    else:
        timestamp_col = None

    if "ms_played" in df.columns:
        ms_col = "ms_played"
    elif "msPlayed" in df.columns:
        ms_col = "msPlayed"
    else:
        ms_col = None

    return track_col, artist_col, timestamp_col, ms_col


def prepare_spotify_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, str, str, str | None, str | None]:
    track_col, artist_col, timestamp_col, ms_col = detect_columns(df)

    print(f"Using track column: {track_col}")
    print(f"Using artist column: {artist_col}")
    print(f"Using timestamp column: {timestamp_col or 'not found'}")
    print(f"Using milliseconds-played column: {ms_col or 'not found'}")

    # Filter out very short plays if possible.
    if ms_col:
        original_len = len(df)
        df[ms_col] = pd.to_numeric(df[ms_col], errors="coerce").fillna(0)
        df = df[df[ms_col] > MIN_MS_PLAYED].copy()
        print(f"Filtered out {original_len - len(df)} rows shorter than {MIN_MS_PLAYED / 1000:.0f} seconds")

    # Clean metadata once so None/NaN cannot crash regex later.
    df[track_col] = df[track_col].apply(lambda x: safe_text(x, "unknown_track"))
    df[artist_col] = df[artist_col].apply(lambda x: safe_text(x, "unknown_artist"))

    missing_metadata_count = int(
        ((df[track_col] == "unknown_track") | (df[artist_col] == "unknown_artist")).sum()
    )
    if missing_metadata_count:
        print(f"Rows with missing artist/track metadata kept as unknown: {missing_metadata_count}")

    # Prepare timestamp.
    if timestamp_col:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce", utc=True)
        bad_dates = int(df[timestamp_col].isna().sum())
        if bad_dates:
            print(f"Rows with invalid timestamps: {bad_dates}")

    # Listening weight for time-series analysis.
    if ms_col:
        df["listening_minutes"] = df[ms_col] / 60_000
    else:
        df["listening_minutes"] = 1.0

    print(f"Loaded {len(df)} rows after filtering")
    return df, track_col, artist_col, timestamp_col, ms_col


# ============================================================
# GENRE ENRICHMENT
# ============================================================

def test_lastfm_connection(fetcher: LastFMGenreFetcher) -> None:
    print("\n🔍 Testing Last.fm API connection...")

    test_artists = [
        ("The Weeknd", "Blinding Lights"),
        ("Drake", "God's Plan"),
        ("Taylor Swift", "Shake It Off"),
        ("Kendrick Lamar", "HUMBLE"),
        ("Beyoncé", "Halo"),
        ("Eminem", "Lose Yourself"),
    ]

    success_count = 0
    print("\nTesting with multiple artists:")

    for artist, track in test_artists:
        genres = fetcher.get_artist_genres(artist, track)
        if genres != ["unknown"]:
            success_count += 1
        print(f"  {artist}: {genres}")
        time.sleep(SLEEP_SECONDS_BETWEEN_API_CALLS)

    print(f"\n✅ {success_count}/{len(test_artists)} artists returned genres")

    if success_count == 0:
        raise RuntimeError("No genres found. Check your Last.fm API key or internet connection.")


def fetch_genres_for_unique_tracks(
    df: pd.DataFrame,
    fetcher: LastFMGenreFetcher,
    artist_col: str,
    track_col: str,
) -> dict[tuple[str, str], list[str]]:
    """Fetch genres only once per unique artist-track pair."""
    unique_pairs = (
        df[[artist_col, track_col]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    print(f"\n🔄 Fetching genres for {len(unique_pairs)} unique artist-track pairs")
    print("   Repeated listens reuse the same cached genre result.")

    genre_map: dict[tuple[str, str], list[str]] = {}

    for _, row in tqdm(unique_pairs.iterrows(), total=len(unique_pairs), desc="Fetching genres"):
        artist = safe_text(row.get(artist_col), "unknown_artist")
        track = safe_text(row.get(track_col), "unknown_track")
        key = (artist, track)

        if artist == "unknown_artist":
            genres = ["unknown"]
        else:
            try:
                genres = fetcher.get_artist_genres(artist, track)
            except Exception as e:
                print("\n⚠️ Genre lookup error")
                print(f"   Artist: {repr(artist)}")
                print(f"   Track:  {repr(track)}")
                print(f"   Error:  {e}")
                genres = ["unknown"]

        genre_map[key] = genres
        time.sleep(SLEEP_SECONDS_BETWEEN_API_CALLS)

    return genre_map


def apply_genres_to_dataframe(
    df: pd.DataFrame,
    genre_map: dict[tuple[str, str], list[str]],
    artist_col: str,
    track_col: str,
) -> pd.DataFrame:
    df = df.copy()
    df["genres"] = [
        genre_map.get((safe_text(artist, "unknown_artist"), safe_text(track, "unknown_track")), ["unknown"])
        for artist, track in zip(df[artist_col], df[track_col])
    ]
    return df


def print_genre_summary(df: pd.DataFrame) -> None:
    unknown_count = int(df["genres"].apply(lambda g: g == ["unknown"] or "unknown" in g).sum())
    known_count = len(df) - unknown_count

    print("\n" + "=" * 60)
    print("📊 GENRE RESULTS")
    print("=" * 60)
    print(f"✅ Rows with known genres: {known_count} ({known_count / len(df) * 100:.1f}%)")
    print(f"❌ Rows with unknown genres: {unknown_count} ({unknown_count / len(df) * 100:.1f}%)")

    all_genres: list[str] = []
    for genres in df["genres"]:
        if isinstance(genres, list):
            all_genres.extend([g for g in genres if g != "unknown"])

    if not all_genres:
        print("\n⚠️ No known genres found.")
        return

    print("\n🎵 Top 15 genres in your listening history:")
    for genre, count in Counter(all_genres).most_common(15):
        print(f"  {genre}: {count}")


# ============================================================
# WEEKLY TIME SERIES + FORECASTING
# ============================================================

def build_weekly_genre_tables(
    df: pd.DataFrame,
    timestamp_col: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if timestamp_col is None:
        raise ValueError("Cannot build time series because no timestamp column was found.")

    working = df.dropna(subset=[timestamp_col]).copy()
    if working.empty:
        raise ValueError("Cannot build time series because all timestamps are invalid or missing.")

    exploded = working.explode("genres")
    exploded["genres"] = exploded["genres"].apply(lambda x: safe_text(x, "unknown"))
    exploded = exploded[exploded["genres"] != "unknown"].copy()

    if exploded.empty:
        raise ValueError("Cannot build time series because no known genres are available.")

    weekly_genre_minutes = (
        exploded
        .set_index(timestamp_col)
        .groupby("genres")["listening_minutes"]
        .resample("W")
        .sum()
        .reset_index()
    )

    pivot_minutes = (
        weekly_genre_minutes
        .pivot_table(index=timestamp_col, columns="genres", values="listening_minutes", aggfunc="sum")
        .sort_index()
        .fillna(0)
    )

    total_weekly_minutes = (
        working
        .set_index(timestamp_col)["listening_minutes"]
        .resample("W")
        .sum()
        .reindex(pivot_minutes.index)
        .replace(0, np.nan)
    )

    pivot_shares = pivot_minutes.div(total_weekly_minutes, axis=0).fillna(0)

    return pivot_minutes, pivot_shares


def forecast_one_series(series: pd.Series, periods: int = FORECAST_WEEKS) -> pd.Series:
    """Forecast one genre-share series and clip results to [0, 1]."""
    series = series.astype(float).replace([np.inf, -np.inf], np.nan).fillna(0)

    future_index = pd.date_range(
        start=series.index[-1] + pd.Timedelta(weeks=1),
        periods=periods,
        freq="W",
    )

    # Prefer Exponential Smoothing when statsmodels is installed and enough data exists.
    if ExponentialSmoothing is not None and len(series) >= 12 and series.nunique() > 1:
        try:
            model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal=None,
                initialization_method="estimated",
            ).fit(optimized=True)
            forecast_values = model.forecast(periods)
            forecast_values.index = future_index
            return forecast_values.clip(lower=0, upper=1)
        except Exception:
            pass

    # Fallback: simple linear trend on the latest available weeks.
    tail = series.tail(min(12, len(series)))

    if len(tail) >= 3 and tail.nunique() > 1:
        x = np.arange(len(tail), dtype=float)
        y = tail.to_numpy(dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        future_x = np.arange(len(tail), len(tail) + periods, dtype=float)
        values = intercept + slope * future_x
    else:
        values = np.repeat(tail.mean() if len(tail) else 0, periods)

    return pd.Series(values, index=future_index).clip(lower=0, upper=1)


def forecast_top_genres(
    pivot_minutes: pd.DataFrame,
    pivot_shares: pd.DataFrame,
    top_n: int = TOP_N_GENRES_TO_FORECAST,
    periods: int = FORECAST_WEEKS,
) -> pd.DataFrame:
    top_genres = pivot_minutes.sum().sort_values(ascending=False).head(top_n).index.tolist()

    forecast_rows: list[dict[str, Any]] = []

    for genre in top_genres:
        forecast = forecast_one_series(pivot_shares[genre], periods=periods)
        for week, share in forecast.items():
            forecast_rows.append(
                {
                    "week": week,
                    "genre": genre,
                    "predicted_share": float(share),
                    "predicted_percent": float(share * 100),
                }
            )

    return pd.DataFrame(forecast_rows)


def print_forecast_summary(forecast_df: pd.DataFrame) -> None:
    if forecast_df.empty:
        print("\n⚠️ Forecast is empty.")
        return

    ranking = (
        forecast_df
        .groupby("genre")["predicted_percent"]
        .mean()
        .sort_values(ascending=False)
    )

    print("\n" + "=" * 60)
    print(f"🔮 FORECAST: NEXT {FORECAST_WEEKS} WEEKS")
    print("=" * 60)
    print("Predicted average weekly listening share among your top genres:")

    for genre, pct in ranking.head(12).items():
        print(f"  {genre}: {pct:.2f}%")


# ============================================================
# OUTPUT
# ============================================================

def save_outputs(
    df: pd.DataFrame,
    pivot_minutes: pd.DataFrame | None,
    pivot_shares: pd.DataFrame | None,
    forecast_df: pd.DataFrame | None,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    enriched_path = output_dir / "spotify_data_with_genres.csv"
    df_to_save = df.copy()
    df_to_save["genres"] = df_to_save["genres"].apply(lambda g: json.dumps(g, ensure_ascii=False))
    df_to_save.to_csv(enriched_path, index=False)
    print(f"\n💾 Saved enriched data: {enriched_path}")

    if pivot_minutes is not None:
        minutes_path = output_dir / "weekly_genre_minutes.csv"
        pivot_minutes.to_csv(minutes_path)
        print(f"💾 Saved weekly genre minutes: {minutes_path}")

    if pivot_shares is not None:
        shares_path = output_dir / "weekly_genre_shares.csv"
        pivot_shares.to_csv(shares_path)
        print(f"💾 Saved weekly genre shares: {shares_path}")

    if forecast_df is not None and not forecast_df.empty:
        forecast_path = output_dir / "genre_preference_forecast.csv"
        forecast_df.to_csv(forecast_path, index=False)
        print(f"💾 Saved forecast: {forecast_path}")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 60)
    print("🎵 SPOTIFY GENRE TREND FORECASTER using Last.fm")
    print("=" * 60)

    api_key = get_lastfm_api_key()
    fetcher = LastFMGenreFetcher(api_key, CACHE_DIR)
    print("\n✅ Genre fetcher initialized with Last.fm")

    test_lastfm_connection(fetcher)

    df_raw = load_spotify_history(DATA_PATH)
    df, track_col, artist_col, timestamp_col, _ = prepare_spotify_dataframe(df_raw)

    print("\n🧪 Testing first 10 cleaned rows...")
    sample_cols = [track_col, artist_col]
    print(df[sample_cols].head(10).to_string(index=False))

    unique_count = df[[artist_col, track_col]].drop_duplicates().shape[0]
    print(f"\nYou have {len(df)} qualifying listening rows and {unique_count} unique artist-track pairs.")
    response = input("Process genre lookups now? (y/n): ").strip().lower()
    if response != "y":
        print("Exiting before genre lookup.")
        return

    genre_map = fetch_genres_for_unique_tracks(df, fetcher, artist_col, track_col)
    df = apply_genres_to_dataframe(df, genre_map, artist_col, track_col)

    print_genre_summary(df)

    stats = fetcher.get_stats()
    print("\n💾 Cache/API stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    pivot_minutes = None
    pivot_shares = None
    forecast_df = None

    try:
        pivot_minutes, pivot_shares = build_weekly_genre_tables(df, timestamp_col)
        forecast_df = forecast_top_genres(pivot_minutes, pivot_shares)
        print_forecast_summary(forecast_df)
    except Exception as e:
        print("\n⚠️ Could not build forecast.")
        print(f"   Reason: {e}")

    save_outputs(df, pivot_minutes, pivot_shares, forecast_df, OUTPUT_DIR)

    print("\n✅ Done.")


if __name__ == "__main__":
    main()
