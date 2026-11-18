import numpy as np
from sklearn.linear_model import Ridge
from app.models import BrewRecord, RecommendationResponse

ROAST_DEFAULT_TEMP = {
    "light": 96,
    "medium": 92,
    "dark": 88,
}


def recommend_next_brew(brews: list[BrewRecord]) -> RecommendationResponse:
    if not brews:
        return RecommendationResponse(
            strategy="Baseline Starting Recipe",
            suggested_temp_c=93,
            suggested_water_g=250,
            suggested_ratio=16.67,
            suggested_pour_count=3,
            suggested_swirl=True,
            explanation=[
                "No brews logged yet for this bean.",
                "Start with 15g coffee to 250g water (1:16.7), 93°C, and 3 pours (bloom + 2 main pours).",
            ],
        )

    latest = brews[0]  # Ordered newest first
    if latest.taste_score == 0:
        return RecommendationResponse(
            strategy="Locked In (Sweet Spot)",
            suggested_temp_c=latest.water_temp_c,
            suggested_water_g=round(latest.water_g),
            suggested_ratio=latest.ratio,
            suggested_pour_count=latest.pour_count,
            suggested_swirl=latest.swirl,
            explanation=[
                f"Your last brew hit 0 (Balanced) at {latest.water_temp_c}°C and 1:{latest.ratio}.",
                "Keep these exact parameters for your next cup.",
            ],
        )

    # Use Ridge regression once at least 4 brews exist with varied taste scores
    taste_values = {b.taste_score for b in brews}
    if len(brews) >= 4 and len(taste_values) >= 2:
        return _ml_recommend(brews, latest)

    return _heuristic_recommend(latest)


def _heuristic_recommend(latest: BrewRecord) -> RecommendationResponse:
    temp = latest.water_temp_c
    ratio = latest.ratio
    pours = latest.pour_count
    swirl = latest.swirl
    reasons = []

    if latest.taste_score < 0:
        # Under-extracted (Sour) -> increase thermal energy, solvent ratio, or agitation
        severity = abs(latest.taste_score)
        temp_bump = 3 if severity >= 3 else 2
        temp = min(100, temp + temp_bump)
        reasons.append(f"Taste was sour ({latest.taste_score}): raised water temp to {temp}°C to boost extraction.")

        if severity >= 3 and ratio < 17.5:
            ratio = round(min(18.0, ratio + 1.0), 2)
            reasons.append(f"Increased brew ratio to 1:{ratio} so more water passes through the pre-ground bed.")
        elif not swirl:
            swirl = True
            reasons.append("Added a gentle Rao swirl after the final pour to reduce channeling.")
        elif pours < 4:
            pours += 1
            reasons.append(f"Split water into {pours} pours to increase agitation without a grinder.")
    else:
        # Over-extracted (Bitter/Astringent) -> lower temp, tighten ratio, reduce agitation
        severity = latest.taste_score
        temp_drop = 4 if severity >= 3 else 2
        temp = max(84, temp - temp_drop)
        reasons.append(f"Taste was bitter (+{severity}): dropped water temp to {temp}°C to curb harsh compounds.")

        if swirl:
            swirl = False
            reasons.append("Removed the swirl to reduce fine migration and bitterness.")
        elif pours > 2:
            pours -= 1
            reasons.append(f"Reduced to {pours} pours for gentler agitation.")
        elif ratio > 14.5:
            ratio = round(max(14.0, ratio - 0.8), 2)
            reasons.append(f"Tightened ratio to 1:{ratio} to stop extracting late bitter compounds.")

    suggested_water = round(latest.coffee_g * ratio)
    return RecommendationResponse(
        strategy="Pre-Ground Extraction Heuristic",
        suggested_temp_c=temp,
        suggested_water_g=suggested_water,
        suggested_ratio=round(suggested_water / latest.coffee_g, 2),
        suggested_pour_count=pours,
        suggested_swirl=swirl,
        explanation=reasons,
    )


def _ml_recommend(brews: list[BrewRecord], latest: BrewRecord) -> RecommendationResponse:
    X = np.array([
        [b.water_temp_c, b.ratio, b.pour_count, int(b.swirl)]
        for b in brews
    ], dtype=float)
    y = np.array([b.taste_score for b in brews], dtype=float)

    model = Ridge(alpha=1.0)
    model.fit(X, y)

    # Search practical candidate tweaks around the latest brew
    best_candidate = None
    best_loss = float("inf")

    for d_temp in range(-5, 6):
        cand_temp = latest.water_temp_c + d_temp
        if not (84 <= cand_temp <= 100):
            continue
        for d_ratio in (-1.0, -0.5, 0.0, 0.5, 1.0):
            cand_ratio = round(latest.ratio + d_ratio, 2)
            if not (14.0 <= cand_ratio <= 18.5):
                continue
            for cand_pours in (2, 3, 4):
                for cand_swirl in (0, 1):
                    features = np.array([[cand_temp, cand_ratio, cand_pours, cand_swirl]], dtype=float)
                    pred_taste = float(model.predict(features)[0])
                    # Penalty favors hitting 0 taste with minimal parameter jumps
                    step_penalty = (
                        0.05 * abs(d_temp)
                        + 0.15 * abs(d_ratio)
                        + 0.1 * abs(cand_pours - latest.pour_count)
                        + 0.1 * abs(cand_swirl - int(latest.swirl))
                    )
                    loss = abs(pred_taste) + step_penalty
                    if loss < best_loss:
                        best_loss = loss
                        best_candidate = (cand_temp, cand_ratio, cand_pours, bool(cand_swirl), pred_taste)

    cand_temp, cand_ratio, cand_pours, cand_swirl, pred_taste = best_candidate
    suggested_water = round(latest.coffee_g * cand_ratio)

    reasons = [
        f"Trained Ridge regression across {len(brews)} logged brews for '{latest.bean_name}'.",
        f"Predicted taste score with these adjustments: {pred_taste:+.2f} (target: 0.00).",
    ]
    if cand_temp != latest.water_temp_c:
        reasons.append(f"Adjust water temperature: {latest.water_temp_c}°C → {cand_temp}°C.")
    if cand_ratio != latest.ratio:
        reasons.append(f"Adjust ratio: 1:{latest.ratio} → 1:{cand_ratio} ({suggested_water}g water).")
    if cand_pours != latest.pour_count or cand_swirl != latest.swirl:
        swirl_txt = "with swirl" if cand_swirl else "no swirl"
        reasons.append(f"Use {cand_pours} pours ({swirl_txt}).")

    return RecommendationResponse(
        strategy="Ridge Regression Optimizer",
        suggested_temp_c=cand_temp,
        suggested_water_g=suggested_water,
        suggested_ratio=round(suggested_water / latest.coffee_g, 2),
        suggested_pour_count=cand_pours,
        suggested_swirl=cand_swirl,
        explanation=reasons,
    )