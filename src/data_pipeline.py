"""
Ethio-Agri Advisor - Data Pipeline
Fetches and processes satellite, weather, and soil data for Ethiopian agriculture
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

load_dotenv()

class AgriDataPipeline:
    """Main data pipeline for agricultural data collection"""
    
    def __init__(self):
        # Ethiopian coordinates (central highlands)
        self.ethiopia_bbox = {
            'min_lat': 3.0,
            'max_lat': 15.0,
            'min_lon': 33.0,
            'max_lon': 48.0
        }
        
        # Free data sources
        self.sources = {
            'weather': 'https://archive-api.open-meteo.com/v1/archive',
            'soil': 'https://rest.isric.org/soilgrids/v2.0/properties/query',
            'vegetation': 'https://firms.modaps.eosdis.nasa.gov/api/area/'
        }
        
    def fetch_weather_data(self, lat=9.03, lon=38.74, days=30):
        """
        Fetch historical weather data from Open-Meteo (FREE)
        
        Data includes: temperature, precipitation, humidity, wind speed
        Source: https://open-meteo.com/en/docs
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': end_date,
            'daily': ['temperature_2m_max', 'temperature_2m_min', 
                     'precipitation_sum', 'rain_sum', 'wind_speed_10m_max'],
            'timezone': 'Africa/Addis_Ababa'
        }
        
        try:
            response = requests.get(self.sources['weather'], params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data['daily'])
            df['date'] = pd.to_datetime(df['time'])
            df.set_index('date', inplace=True)
            
            # Calculate derived features
            df['temp_mean'] = (df['temperature_2m_max'] + df['temperature_2m_min']) / 2
            df['temp_range'] = df['temperature_2m_max'] - df['temperature_2m_min']
            
            print(f"✅ Weather data fetched: {len(df)} days")
            return df
            
        except Exception as e:
            print(f"❌ Weather API error: {e}")
            return self._generate_sample_weather_data()
    
    def _generate_sample_weather_data(self):
        """Fallback: Generate realistic Ethiopian weather data"""
        print("🔄 Using simulated weather data (Ethiopian conditions)")
        
        dates = pd.date_range(start='2024-01-01', periods=365, freq='D')
        
        # Ethiopian climate patterns: Rainy seasons (June-Sept), Dry season (Oct-May)
        seasonal_temps = {
            'Jan': 22, 'Feb': 23, 'Mar': 24, 'Apr': 23, 'May': 22,
            'Jun': 20, 'Jul': 19, 'Aug': 19, 'Sep': 20, 'Oct': 21,
            'Nov': 21, 'Dec': 21
        }
        
        seasonal_rain = {
            'Jan': 20, 'Feb': 30, 'Mar': 60, 'Apr': 80, 'May': 100,
            'Jun': 120, 'Jul': 150, 'Aug': 150, 'Sep': 120, 'Oct': 60,
            'Nov': 30, 'Dec': 15
        }
        
        data = []
        for date in dates:
            month = date.strftime('%b')
            base_temp = seasonal_temps[month] + np.random.normal(0, 2)
            rain = seasonal_rain[month] * np.random.uniform(0.5, 1.5)
            
            data.append({
                'date': date,
                'temperature_2m_max': base_temp + 5 + np.random.normal(0, 1),
                'temperature_2m_min': base_temp - 5 + np.random.normal(0, 1),
                'precipitation_sum': max(0, rain),
                'rain_sum': max(0, rain * 0.9),
                'wind_speed_10m_max': np.random.uniform(2, 10)
            })
        
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        df['temp_mean'] = (df['temperature_2m_max'] + df['temperature_2m_min']) / 2
        df['temp_range'] = df['temperature_2m_max'] - df['temperature_2m_min']
        
        return df
    
    def get_soil_data(self, lat=9.03, lon=38.74):
        """
        Fetch soil properties from ISRIC SoilGrids (FREE)
        
        Properties: pH, organic carbon, nitrogen, available water capacity
        Source: https://soilgrids.org/
        """
        # Since API requires registration, we'll use Ethiopian soil data
        print("Using Ethiopian soil database")
        
        # Ethiopian soil types and their properties
        ethiopian_soils = {
            'Nitosol': {'ph': 6.5, 'organic_carbon': 1.8, 'nitrogen': 0.15, 
                       'water_capacity': 0.25, 'texture': 'clay_loam'},
            'Vertisol': {'ph': 7.2, 'organic_carbon': 1.5, 'nitrogen': 0.12,
                        'water_capacity': 0.40, 'texture': 'clay'},
            'Luvisol': {'ph': 6.8, 'organic_carbon': 1.2, 'nitrogen': 0.10,
                       'water_capacity': 0.20, 'texture': 'sandy_loam'},
            'Cambisol': {'ph': 6.0, 'organic_carbon': 2.0, 'nitrogen': 0.18,
                        'water_capacity': 0.30, 'texture': 'loam'},
            'Fluvisol': {'ph': 7.0, 'organic_carbon': 1.0, 'nitrogen': 0.08,
                        'water_capacity': 0.35, 'texture': 'silty_clay'}
        }
        
        # Select based on location (simplified)
        # Northern Ethiopia = Vertisol, Highlands = Nitosol, etc.
        if lat > 12:
            soil_type = 'Vertisol'
        elif lat > 8:
            soil_type = 'Nitosol'
        else:
            soil_type = 'Luvisol'
            
        return {**ethiopian_soils[soil_type], 'type': soil_type}
    
    def get_vegetation_index(self, lat=9.03, lon=38.74):
        """
        Get NDVI from MODIS (FREE)
        
        Normalized Difference Vegetation Index for crop health monitoring
        Source: https://modis.gsfc.nasa.gov/data/
        """
        # Simplified - using simulated data
        # In production, use: https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MOD13A2
        
        dates = pd.date_range(start='2024-01-01', periods=365, freq='D')
        
        # Ethiopian growing seasons: Belg (Feb-May), Meher (June-Oct)
        ndvi_values = []
        for date in dates:
            month = date.month
            # Higher NDVI during growing seasons
            if 2 <= month <= 5:  # Belg season
                ndvi = np.random.uniform(0.3, 0.6)
            elif 6 <= month <= 10:  # Meher season
                ndvi = np.random.uniform(0.4, 0.7)
            else:
                ndvi = np.random.uniform(0.1, 0.3)
            
            ndvi_values.append(ndvi)
        
        return pd.Series(ndvi_values, index=dates)
    
    def prepare_training_data(self, num_samples=1000):
        """
        Generate synthetic training data for the model
        Combines weather, soil, and crop data
        """
        print("🌾 Generating training dataset...")
        
        data = []
        
        # Ethiopian crops with their optimal conditions
        crops = {
            'Teff': {'temp_opt': 22, 'rain_opt': 800, 'soil_ph': 6.5, 'growing_days': 90},
            'Wheat': {'temp_opt': 18, 'rain_opt': 600, 'soil_ph': 6.8, 'growing_days': 120},
            'Barley': {'temp_opt': 17, 'rain_opt': 550, 'soil_ph': 7.0, 'growing_days': 110},
            'Maize': {'temp_opt': 25, 'rain_opt': 700, 'soil_ph': 6.0, 'growing_days': 130},
            'Sorghum': {'temp_opt': 28, 'rain_opt': 500, 'soil_ph': 6.5, 'growing_days': 120},
            'Coffee': {'temp_opt': 22, 'rain_opt': 1200, 'soil_ph': 6.2, 'growing_days': 180},
            'Enset': {'temp_opt': 20, 'rain_opt': 1000, 'soil_ph': 6.5, 'growing_days': 150},
            'Millet': {'temp_opt': 28, 'rain_opt': 400, 'soil_ph': 7.2, 'growing_days': 100},
            'Sesame': {'temp_opt': 30, 'rain_opt': 600, 'soil_ph': 6.8, 'growing_days': 110},
            'Lentils': {'temp_opt': 20, 'rain_opt': 450, 'soil_ph': 6.8, 'growing_days': 100}
        }
        
        soil_types = ['Nitosol', 'Vertisol', 'Luvisol', 'Cambisol', 'Fluvisol']
        regions = ['Tigray', 'Amhara', 'Oromia', 'SNNP', 'Somali', 'Benishangul']
        
        for _ in range(num_samples):
            # Random conditions
            temp = np.random.uniform(15, 32)
            rain = np.random.uniform(200, 1400)
            soil_ph = np.random.uniform(5.5, 7.5)
            growing_days = np.random.randint(80, 200)
            
            # Select best crop based on conditions
            best_crop = None
            best_score = -999
            
            for crop, params in crops.items():
                # Calculate suitability score
                temp_score = 1 - abs(temp - params['temp_opt']) / 15
                rain_score = 1 - abs(rain - params['rain_opt']) / 800
                ph_score = 1 - abs(soil_ph - params['soil_ph']) / 2
                days_score = 1 - abs(growing_days - params['growing_days']) / 100
                
                # Weighted combination
                score = (temp_score * 0.3 + rain_score * 0.3 + 
                        ph_score * 0.2 + days_score * 0.2)
                
                if score > best_score:
                    best_score = score
                    best_crop = crop
            
            # Add some randomness to make it realistic
            if np.random.random() < 0.1:  # 10% noise
                best_crop = np.random.choice(list(crops.keys()))
            
            # Add yield based on how well conditions match
            yield_kg_ha = best_score * 3000 + np.random.normal(0, 200)
            yield_kg_ha = max(500, min(5000, yield_kg_ha))
            
            data.append({
                'temperature': temp,
                'rainfall': rain,
                'soil_ph': soil_ph,
                'growing_days': growing_days,
                'soil_type': np.random.choice(soil_types),
                'region': np.random.choice(regions),
                'crop': best_crop,
                'yield_kg_ha': yield_kg_ha,
                'suitability_score': best_score
            })
        
        df = pd.DataFrame(data)
        print(f"Training data generated: {len(df)} samples")
        return df

# Usage example
if __name__ == "__main__":
    pipeline = AgriDataPipeline()
    
    # Fetch weather
    weather = pipeline.fetch_weather_data()
    print(weather.head())
    
    # Get soil data
    soil = pipeline.get_soil_data()
    print(f"Soil type: {soil['type']}")
    
    # Prepare training data
    train_data = pipeline.prepare_training_data(1000)
    train_data.to_csv('data/training_data.csv', index=False)
