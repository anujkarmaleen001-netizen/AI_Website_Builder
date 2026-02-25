# Backend Setup Commands (macOS)

# 1. Create virtual environment (if not already created)
python3.11 -m venv venvAi

# 2. Activate virtual environment
source venvAi/bin/activate

# 3. Upgrade pip
python3.11 -m pip install --upgrade pip

# 4. Install dependencies
# Note: If you get Rust/maturin errors, ensure you're using Python 3.11 (not 3.13)
# or install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
pip install -r requierments.txt

# env all ready exist then skipp
# 5. Create .env file from example (copy and update with your API keys)
# Copy env.example to .env and update the values:
cp env.example .env

# 6. Run the FastAPI server
# Option 1: Using uvicorn directly
uvicorn app.main:app --reload --port 8000


# The API will be available at:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Alternative Docs: http://localhost:8000/redoc

