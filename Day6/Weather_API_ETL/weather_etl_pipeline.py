import os
import time
import sqlite3
import requests
import pandas as pd
import numpy as np

from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# =========================
# CONFIGURATION
# =========================

API_KEY = os.getenv("OPENWEATHER_API_KEY")

LAT = 17.3850
LON = 78.4867
CITY = "Hyderabad"

DB_NAME = "weather_data.db"
RAW_CSV = "raw_weather_data.csv"
CLEAN_CSV = "clean_weather_data.csv"
FORECAST_CSV = "weather_forecast_output.csv"


# =========================
# EXTRACT
# =========================

def get_unix_timestamp(date_obj):
    return int(time.mktime(date_obj.timetuple()))


def extract_historical_weather():
    """
    Extract last 6 months weather data from OpenWeather historical API.

    Note:
    OpenWeather historical API may require paid subscription.
    """

    if not API_KEY:
        raise ValueError("OPENWEATHER_API_KEY environment variable is missing.")

    all_rows = []

    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    current_date = start_date

    while current_date <= end_date:
        timestamp = get_unix_timestamp(current_date)

        url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"

        params = {
            "lat": LAT,
            "lon": LON,
            "dt": timestamp,
            "appid": API_KEY,
            "units": "metric"
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()

            data = response.json()

            for hour_data in data.get("data", []):
                row = {
                    "city": CITY,
                    "latitude": LAT,
                    "longitude": LON,
                    "datetime": datetime.fromtimestamp(
                        hour_data.get("dt")
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    "temperature": hour_data.get("temp"),
                    "feels_like": hour_data.get("feels_like"),
                    "pressure": hour_data.get("pressure"),
                    "humidity": hour_data.get("humidity"),
                    "dew_point": hour_data.get("dew_point"),
                    "clouds": hour_data.get("clouds"),
                    "visibility": hour_data.get("visibility"),
                    "wind_speed": hour_data.get("wind_speed"),
                    "wind_deg": hour_data.get("wind_deg"),
                    "weather_main": hour_data.get("weather", [{}])[0].get("main"),
                    "weather_description": hour_data.get("weather", [{}])[0].get("description"),
                    "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                all_rows.append(row)

            print(f"Extracted data for {current_date.date()}")

        except Exception as e:
            print(f"Failed for {current_date.date()} | Error: {e}")

        current_date += timedelta(days=1)

    df = pd.DataFrame(all_rows)
    df.to_csv(RAW_CSV, index=False)

    print(f"Raw data saved to {RAW_CSV}")
    return df


# =========================
# TRANSFORM + EDA
# =========================

def transform_and_eda(df):
    print("\nEDA Started")

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns)

    print("\nMissing Values:")
    print(df.isnull().sum())

    print("\nData Types:")
    print(df.dtypes)

    print("\nStatistical Summary:")
    print(df.describe())

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    # Remove duplicates
    df = df.drop_duplicates(subset=["datetime"])

    # Handle missing numerical values
    numeric_cols = [
        "temperature",
        "feels_like",
        "pressure",
        "humidity",
        "dew_point",
        "clouds",
        "visibility",
        "wind_speed",
        "wind_deg"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].interpolate(method="linear")
            df[col] = df[col].fillna(df[col].mean())

    # Handle missing categorical values
    categorical_cols = ["weather_main", "weather_description"]

    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    # Feature engineering
    df["hour"] = df["datetime"].dt.hour
    df["day"] = df["datetime"].dt.day
    df["month"] = df["datetime"].dt.month
    df["day_of_week"] = df["datetime"].dt.dayofweek

    # Time series lag features
    df["temp_lag_1"] = df["temperature"].shift(1)
    df["temp_lag_2"] = df["temperature"].shift(2)
    df["temp_lag_24"] = df["temperature"].shift(24)

    # Rolling features
    df["temp_rolling_3"] = df["temperature"].rolling(window=3).mean()
    df["temp_rolling_24"] = df["temperature"].rolling(window=24).mean()

    df = df.dropna()

    # Normalization
    scaler = MinMaxScaler()

    scale_cols = [
        "temperature",
        "feels_like",
        "pressure",
        "humidity",
        "dew_point",
        "clouds",
        "visibility",
        "wind_speed"
    ]

    available_scale_cols = [col for col in scale_cols if col in df.columns]

    df[available_scale_cols] = scaler.fit_transform(df[available_scale_cols])

    df.to_csv(CLEAN_CSV, index=False)

    print(f"\nCleaned data saved to {CLEAN_CSV}")

    return df


# =========================
# LOAD
# =========================

def load_to_sqlite(df):
    conn = sqlite3.connect(DB_NAME)

    df.to_sql(
        "weather_time_series",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print(f"Data loaded into SQLite database: {DB_NAME}")


# =========================
# ML MODEL
# =========================

def train_forecasting_model(df):
    """
    Time series forecasting using RandomForestRegressor.

    Target:
    temperature

    Features:
    lag values, rolling values, humidity, pressure, wind speed, hour, month.
    """

    features = [
        "humidity",
        "pressure",
        "wind_speed",
        "clouds",
        "hour",
        "day",
        "month",
        "day_of_week",
        "temp_lag_1",
        "temp_lag_2",
        "temp_lag_24",
        "temp_rolling_3",
        "temp_rolling_24"
    ]

    features = [col for col in features if col in df.columns]

    target = "temperature"

    X = df[features]
    y = df[target]

    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    print("\nModel Evaluation:")
    print(f"MAE  : {mae}")
    print(f"RMSE : {rmse}")

    forecast_df = pd.DataFrame({
        "actual_temperature": y_test.values,
        "predicted_temperature": predictions
    })

    forecast_df.to_csv(FORECAST_CSV, index=False)

    print(f"Forecast output saved to {FORECAST_CSV}")


# =========================
# PIPELINE RUNNER
# =========================

def run_etl_pipeline():
    print("Weather ETL Pipeline Started")

    raw_df = extract_historical_weather()

    if raw_df.empty:
        print("No data extracted. Pipeline stopped.")
        return

    clean_df = transform_and_eda(raw_df)

    load_to_sqlite(clean_df)

    train_forecasting_model(clean_df)

    print("Weather ETL Pipeline Completed Successfully")


if __name__ == "__main__":
    run_etl_pipeline()