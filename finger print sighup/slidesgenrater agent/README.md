 # AI PowerPoint Generator (Local & Private)

This AI agent automatically generates PowerPoint presentations from a user topic using a local LLM (Ollama) and Python. It requires **no external API keys**, ensuring complete privacy and offline capability.

## Prerequisites & Installation

### 1. Install Python
If you don't have Python installed:
* Download and install from [python.org](https://www.python.org/downloads/).
* **Important:** During installation, check the box that says **"Add Python to PATH"**.

### 2. Install Ollama (Local AI Engine)
* Download Ollama from [ollama.com](https://ollama.com/).
* Install it on your system.
* Open your terminal (Command Prompt or PowerShell) and run the following command to download the Llama 3 model:
  ```bash
  ollama pull llama3
  ```

### 3. Install Python Dependencies
Open your terminal in the project folder and run:
```bash
pip install -r requirements.txt
```
*(This installs `python-pptx` and `requests`)*

## How to Use

1. **Start Ollama**: Ensure the Ollama application is running in the background.
2. **Run the Script**:
   ```bash
   python slides_agent.py
   ```
3. **Enter Topic**: When prompted, type a topic (e.g., "The Future of Quantum Computing").
4. **Result**: The agent will communicate with the AI, generate an outline, and save the result in the `generated_presentations/` folder. A copy named `latest_presentation.pptx` is also kept in the root folder for quick access.

## Features
* **Private**: No data leaves your machine.
* **Structured**: Generates 5–8 slides with clear titles and 3–5 bullet points each.
* **Deterministic Data Extraction**: Automatically extracts exact figures, categories, and milestones from source documents.
* **No Generic Placeholders**: Investor presentations use actual data from documents, not AI-generated generic text.
* **Error Handling**: Gracefully handles connection issues with Ollama or formatting errors from the AI.
* **Modular Code**: Easy to extend or integrate into other workflows.

## Recent Updates
### v2.0 - Deterministic Data Injection (April 2026)
- **Fixed**: Generic placeholder text issue in investor presentations
- **Added**: Automatic extraction of exact figures (GBP amounts, percentages, years)
- **Added**: Validation engine to ensure source document data is used
- **Improved**: Revenue pillars, financial projections, and equity terms now extracted directly from documents
- **Result**: Presentations now show "GBP 350,000" instead of "+25% Growth" when the source document contains specific data

## Project Structure
* `slides_agent.py`: The main script containing the logic.
* `requirements.txt`: List of required Python libraries.
* `README.md`: Instructions and documentation.
