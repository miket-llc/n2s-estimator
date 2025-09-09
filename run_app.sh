#!/bin/bash
echo "🚀 Starting N2S Delivery Estimator..."
echo "📍 Working directory: $(pwd)"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
    echo "🐍 Python version: $(python --version)"
    echo "📦 Virtual environment: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment found, using system Python"
    echo "🐍 Python version: $(python3 --version)"
fi

echo ""

if [ ! -f "src/n2s_estimator/ui/main.py" ]; then
    echo "❌ Error: main.py not found"
    exit 1
fi

if [ ! -f "src/n2s_estimator/data/n2s_estimator.xlsx" ]; then
    echo "❌ Error: Configuration workbook not found"
    exit 1
fi

echo "✅ All files present"
echo "🌐 Starting Streamlit on http://localhost:8501"
echo "💡 Press Ctrl+C to stop"
echo ""

if [ -d "venv" ]; then
    streamlit run src/n2s_estimator/ui/main.py
else
    python3 -m streamlit run src/n2s_estimator/ui/main.py
fi

