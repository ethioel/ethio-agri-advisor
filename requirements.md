cat > requirements.txt << 'EOF'
# Core dependencies
streamlit==1.28.1
pandas==2.1.0
numpy==1.24.3
scikit-learn==1.3.1
joblib==1.3.2

# Data fetching & APIs
requests==2.31.0
python-dotenv==1.0.0

# Visualization
plotly==5.17.0
matplotlib==3.8.0
seaborn==0.12.2
folium==0.14.0
streamlit-folium==0.7.0

# Data processing
scipy==1.11.2
pydantic==2.2.1

# Development & Testing
pytest==7.4.2
pytest-cov==4.1.0
black==23.9.1
flake8==6.1.0
pylint==2.17.5

# Logging & Monitoring
python-json-logger==2.0.7

# Telegram Bot (optional)
python-telegram-bot==20.1

# Additional utilities
tqdm==4.66.1
pytz==2023.3
pillow==10.0.0
EOF
