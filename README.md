
# ☕ V60 Brew Dial-In Studio

I love using a V60 for filter coffee—the whole pour-over process is a nice morning ritual—but I kept getting different results from cup to cup. One morning it would turn out bright and balanced, and the next day the exact same bag of coffee would taste sharp and sour or dry and bitter.

Since I brew with pre-ground coffee and don't own a burr grinder, I couldn't just adjust grind clicks like most coffee guides tell you to. So I built this app to track each brew and dial in the variables I *can* control—water temperature, brew ratio, pour structure, and swirling—until every cup hits the exact taste profile I want.

---

## Features

* **Per-Bean Dial-In Profiles:** Track multiple coffee bags separately. Every coffee gets its own brew history, taste trend, and tailored recipe target.
* **Built-In Drawdown Stopwatch:** Time your pour and drawdown right in the browser; stopping the timer automatically fills in your drawdown seconds.
* **Two-Stage Pre-Ground Extraction Advisor:** Automatically switches from extraction physics rules (brews 1–3) to a **Ridge Regression** model (`scikit-learn`) once you have logged at least 4 varied cups for that bag.
* **Persistent Local Storage:** Automatically saves every brew to a local SQLite database (`~/.v60-dial-in/v60_brews.db`) so your recipes stay saved across restarts.
* **One-Click Recipe Copy:** Apply the advisor's suggested temperature, water weight, pour count, and swirl setting straight into your next brew form.

---

## Tech Stack

* **Backend:** Python 3, FastAPI, Pydantic, SQLite
* **Optimization / ML:** `scikit-learn` (Ridge Regression), NumPy
* **Frontend:** Vanilla HTML/CSS/JS with a custom animated V60 UI
* **Testing:** `pytest`

---

## Getting Started

### Option 1: Run from Terminal (macOS / Linux / Windows)
1. Clone the repository and enter the project folder:
   ```bash
   git clone (https://github.com/svet111/v60-dial-in.git)
   cd v60-dial-in
    ```

2. Create a virtual environment and install dependencies:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate   # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    
    ```

3. Start the server:
    ```bash
    uvicorn app.main:app --reload
    
    ```

4. Open `http://127.0.0.1:8000` in your browser. *(You can also inspect the interactive FastAPI / OpenAPI documentation at `http://127.0.0.1:8000/docs`.)*

### Option 2: Double-Click Launcher on macOS (No Terminal Needed)

Once you have set up `.venv` above, you can launch the app anytime directly from Finder or your Dock:

1. Make sure `Start V60 Studio.command` is executable (only needed once):
    ```bash
    chmod +x "Start V60 Studio.command"
    ```

2. Double-click **`Start V60 Studio.command`**. It starts the FastAPI server automatically and opens `http://127.0.0.1:8000` in your browser.

---

## Step-by-Step User Guide

### 1. Brewing Your First Cup with a New Bag

1. **Enter the Coffee / Bag Name:** Type the name of the coffee you are brewing (e.g., `Ethiopia Guji Pre-Ground`) and select its **Roast Level** (`Light`, `Medium`, or `Dark`).
2. **Check the Starting Recipe:** On the right panel (**Next Cup Recipe**), the app gives you a baseline pre-ground starting recipe (`93°C`, `15g` coffee to `250g` water / `1:16.7`, `3 pours`, `gentle swirl`).
3. **Time Your Brew:** Click **Start Pour** on the **Drawdown Stopwatch** when you begin pouring your bloom, and click **Stop** as soon as the water finishes draining through the coffee bed. Your drawdown time (in seconds) automatically fills into the form.
4. **Rate the Taste (`-5` to `+5`):**
* **`-5` to `-1` (Sour / Under-extracted):** Sharp, salty, thin, or overly acidic.
* **`0` (Balanced Sweet Spot):** Sweet, clear, and pleasant finish.
* **`+1` to `+5` (Bitter / Over-extracted):** Dry, harsh, hollow, or astringent.

5. **Log the Brew:** Add any optional tasting notes and click **Log Brew & Dial In Next Cup**.

### 2. Understanding the Brew Parameters

| Parameter | What It Means | Practical Range & Tips |
| :--- | :--- | :--- |
| **Coffee / Bag Name** | Separates brew logs and ML models per coffee bag. | Pick a saved bag from the dropdown, type a new name for a new bag, or leave it blank to view **All Beans** combined. |
| **Roast Level** | `Light`, `Medium`, or `Dark`. | Recorded alongside each brew in your log history for reference. |
| **Coffee Dose (g) & Total Water (g)** | Dry coffee weight and total brew water weight. | Automatically computes the **brew ratio** (e.g., `15g` coffee to `250g` water = `1:16.7`). Higher ratios extract more; lower ratios taste stronger and less extracted. |
| **Water Temp (°C)** | Kettle water temperature (`80°C – 100°C`). | Primary lever for pre-ground coffee: hotter water (`94–98°C`) fixes sourness; cooler water (`86–91°C`) tames bitterness. |
| **Pour Structure** | Total water pours including the initial bloom (`2`, `3`, or `4` pours). | `2 pours` = bloom + 1 main pour (gentle). `3 pours` = bloom + 2 pours (balanced). `4 pours` = higher agitation and higher extraction. |
| **Gentle Rao Swirl** | Swirling the V60 cone right after the final pour to flatten the coffee bed. | **Yes** promotes even extraction; **No** reduces fine particle migration and bitterness in fine pre-ground bags. |
| **Drawdown Time (sec)** | Total time from the start of your bloom pour until the water finishes draining. | Typically `140s – 210s` (`2:20 – 3:30`). Use the built-in **Drawdown Stopwatch** to fill this automatically. |
| **Cup Balance (`-5` to `+5`)** | Your taste feedback on the finished cup. | `-5` = very sour/under-extracted, `0` = balanced sweet spot, `+5` = very bitter/over-extracted. |

### 3. How Suggestions Work (and When ML Kicks In)

The **Next Cup Recipe** panel updates immediately every time you log a cup, adapting to how much data you have for that specific bag:

* **0 Brews Logged (`Baseline Starting Recipe`):** Suggests a safe, balanced starting point for pre-ground filter coffee (`93°C`, `1:16.7` ratio, `3` pours with a gentle swirl).
* **1–3 Brews Logged (`Pre-Ground Extraction Heuristic`):** Since grind size cannot be changed with pre-ground coffee, the advisor adjusts the remaining physical extraction levers:
* **Too Sour (`< 0`):** Raises water temperature (`+2°C` to `+3°C`), increases brew ratio (`+1.0` for severe sourness), enables a gentle Rao swirl, or adds an extra pour to boost agitation.
* **Too Bitter (`> 0`):** Drops water temperature (`-2°C` to `-4°C`), removes the swirl first (to avoid migrating fine particles), reduces pour stages, or tightens the brew ratio.


* **4+ Brews Logged with Varied Scores (`Ridge Regression Optimizer`):** Once you have logged at least 4 brews with at least 2 different taste scores for a bag, the app trains a **Ridge Regression** model (`alpha=1.0`) mapping `(water_temp, ratio, pour_count, swirl) → taste_score`. It searches nearby parameter combinations and picks the smallest tweak predicted to land closest to `0.00` (the sweet spot).
* **Hit `0` (`Locked In`):** Once a cup lands on `0`, the advisor locks in those exact parameters so you can repeat that cup consistently every morning.

To use a recommendation on your next brew, click **`↓ Copy Recommended Recipe into Form`** on the right card.

### 4. Switching Between Different Coffee Bags

* **Starting a New Bag:** Simply type a new name into the **Coffee / Bag Name** field and click outside the box (or press `Tab`). The brew history table and recommendation engine immediately switch to a clean profile for that new bag without deleting your previous bags.
* **Returning to a Previous Bag:** Click the **Coffee / Bag Name** input field to pick any previously logged coffee from the autocomplete dropdown—your full brew history and dialed-in recipe for that bag reload automatically.

### 5. Where Your Data Is Stored

* All brews are saved locally in an SQLite database at:
    ```text
    ~/.v60-dial-in/v60_brews.db
    ```


* Because the database lives in your user home directory rather than inside the code folder, your brew logs persist safely even if you update the project or launch it from different locations.
* To back up your data, copy `~/.v60-dial-in/v60_brews.db`. To reset everything from scratch, delete that file and restart the app.

---

## Running Tests

Run the automated test suite (`pytest`) to verify the heuristic extraction rules, Ridge regression activation, and FastAPI database endpoints:

    ```bash
    pytest
    ```

```

*(Note: Make sure you've also added the `GET /api/beans` endpoint and `~/.v60-dial-in/v60_brews.db` path to `app/database.py`, `app/main.py`, and `static/index.html` from the previous step so the autocomplete dropdown and persistent database path match the guide!)*

```