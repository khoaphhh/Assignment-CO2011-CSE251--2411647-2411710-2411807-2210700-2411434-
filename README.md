# Create and activate virtual environment
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On Linux/macOS
    source venv/bin/activate

# Install required libraries
    pip install -r requirements.txt

# Test Task 1
    python main.py --task parse --input examples/simple_net.pnml