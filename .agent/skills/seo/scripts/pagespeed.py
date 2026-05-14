#!/usr/bin/env python3
"""
Fetch Core Web Vitals and performance data from Google PageSpeed Insights API.

Uses the free PSI API v5 (no API key required, rate-limited).

Usage:
    python pagespeed.py https://example.com
    python pagespeed.py https://example.com --strategy mobile
    python pagespeed.py https://example.com --json
"""

import argparse
import json
import sys
import time

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


PSI_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

# Current CWV thresholds (as of 2026)
CWV_THRESHOLDS = {
    "LCP": {"good": 2500, "poor": 4000, "unit": "ms", "label": "Largest Contentful Paint"},
    "INP": {"good": 200, "poor": 500, "unit": "ms", "label": "Interaction to Next Paint"},
    "CLS": {"good": 0.1, "poor": 0.25, "unit": "", "label": "Cumulative Layout Shift"},
    "FCP": {"good": 1800, "poor": 3000, "unit": "ms", "label": "First Contentful Paint"},
    "TTFB": {"good": 800, "poor": 1800, "unit": "ms", "label": "Time to First Byte"},
}

# Mapping from PSI API field names to our labels
PSI_METRIC_MAP = {
    "LARGEST_CONTENTFUL_PAINT_MS": "LCP",
    "INTERACTION_TO_NEXT_PAINT": "INP",
    "CUMULATIVE_LAYOUT_SHIFT_SCORE": "CLS",
    "FIRST_CONTENTFUL_PAINT_MS": "FCP",
    "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "TTFB",
}


def get_pagespeed(url: str, strategy: str = "mobile", api_key: str = None) -> dict:
    """
    Fetch PageSpeed Insights data for a URL.

    Args:
        url: URL to analyze
        strategy: 'mobile' or 'desktop'
        api_key: Optional Google API key for higher rate limits

    Returns:
        Dictionary with CWV metrics, performance score, and opportunities
    """
    result = {
        "url": url,
        "strategy": strategy,
        "performance_score": None,
        "metrics": {},
        "opportunities": [],
        "diagnostics": [],
        "field_data_available": False,
        "error": None,
    }

    params = {
        "url": url,
        "strategy": strategy,
        "category": "performance",
    }
    if api_key:
        params["key"] = api_key

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(PSI_API, params=params, timeout=60)

            if resp.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3  # Simple backoff: 3s, 6s
                    print(f"  [pagespeed] Rate limited by API. Retrying in {wait_time}s...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
                else:
                    result["error"] = "Rate limited by Google API. Wait a few minutes or add an API key."
                    return result

            if resp.status_code != 200:
                result["error"] = f"API error: HTTP {resp.status_code}"
                return result

            data = resp.json()
            break  # Success

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"  [pagespeed] Timeout. Retrying...", file=sys.stderr)
                time.sleep(2)
                continue
            result["error"] = "API request timed out (60s) — try again later"
            return result
        except requests.exceptions.RequestException as e:
            result["error"] = f"Request failed: {e}"
            return result
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            result["error"] = f"Failed to parse API response: {e}"
            return result

        # Extract performance score
        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        perf = categories.get("performance", {})
        result["performance_score"] = int((perf.get("score", 0) or 0) * 100)

        # Extract CrUX field data (real user metrics)
        loading = data.get("loadingExperience", {})
        crux_metrics = loading.get("metrics", {})

        if crux_metrics:
            result["field_data_available"] = True
            for api_name, label in PSI_METRIC_MAP.items():
                metric_data = crux_metrics.get(api_name)
                if metric_data:
                    percentile = metric_data.get("percentile")
                    category = metric_data.get("category", "").lower()

                    thresholds = CWV_THRESHOLDS.get(label, {})
                    result["metrics"][label] = {
                        "value": percentile,
                        "unit": thresholds.get("unit", ""),
                        "label": thresholds.get("label", label),
                        "rating": category,  # FAST, AVERAGE, SLOW
                    }

        # Fall back to Lighthouse lab data if no field data
        if not result["field_data_available"]:
            audits = lighthouse.get("audits", {})
            lab_map = {
                "largest-contentful-paint": "LCP",
                "interaction-to-next-paint": "INP",
                "cumulative-layout-shift": "CLS",
                "first-contentful-paint": "FCP",
                "server-response-time": "TTFB",
            }
            for audit_id, label in lab_map.items():
                audit = audits.get(audit_id, {})
                if audit and audit.get("numericValue") is not None:
                    value = audit["numericValue"]
                    thresholds = CWV_THRESHOLDS.get(label, {})

                    # Determine rating
                    good = thresholds.get("good", float("inf"))
                    poor = thresholds.get("poor", float("inf"))
                    if value <= good:
                        rating = "good"
                    elif value <= poor:
                        rating = "needs-improvement"
                    else:
                        rating = "poor"

                    # CLS is reported as a score, not ms
                    if label == "CLS":
                        value = round(value, 3)
                    else:
                        value = round(value)

                    result["metrics"][label] = {
                        "value": value,
                        "unit": thresholds.get("unit", ""),
                        "label": thresholds.get("label", label),
                        "rating": rating,
                    }

        # Extract opportunities
        audits = lighthouse.get("audits", {})
        for audit_id, audit in audits.items():
            if audit.get("details", {}).get("type") == "opportunity":
                savings = audit.get("details", {}).get("overallSavingsMs")
                if savings and savings > 100:
                    result["opportunities"].append({
                        "title": audit.get("title", audit_id),
                        "savings_ms": round(savings),
                        "description": audit.get("description", "")[:200],
                    })

        # Sort opportunities by savings
        result["opportunities"].sort(key=lambda x: x["savings_ms"], reverse=True)

        # Extract key diagnostics
        diagnostic_ids = [
            "dom-size", "total-byte-weight", "render-blocking-resources",
            "uses-responsive-images", "uses-webp-images", "font-display",
        ]
        for diag_id in diagnostic_ids:
            diag = audits.get(diag_id, {})
            if diag and diag.get("score") is not None and diag["score"] < 1:
                result["diagnostics"].append({
                    "title": diag.get("title", diag_id),
                    "score": round(diag["score"] * 100),
                    "display": diag.get("displayValue", ""),
                })

    return result


def main():
    parser = argparse.ArgumentParser(description="Get Core Web Vitals from PageSpeed Insights")
    parser.add_argument("url", help="URL to analyze")
    parser.add_argument("--strategy", "-s", default="mobile",
                        choices=["mobile", "desktop"], help="Analysis strategy")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--api-key", help="Google API key for higher rate limits")

    args = parser.parse_args()
    result = get_pagespeed(args.url, strategy=args.strategy, api_key=args.api_key)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    if result["error"]:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"PageSpeed Insights — {result['url']}")
    print(f"Strategy: {result['strategy'].upper()}")
    print("=" * 50)

    score = result["performance_score"]
    if score >= 90:
        icon = "🟢"
    elif score >= 50:
        icon = "🟡"
    else:
        icon = "🔴"
    print(f"\nPerformance Score: {icon} {score}/100")

    data_source = "Field Data (CrUX)" if result["field_data_available"] else "Lab Data (Lighthouse)"
    print(f"Data Source: {data_source}")

    if result["metrics"]:
        print(f"\nCore Web Vitals:")
        for name, metric in result["metrics"].items():
            rating = metric["rating"]
            if "good" in rating.lower() or "fast" in rating.lower():
                icon = "✅"
            elif "poor" in rating.lower() or "slow" in rating.lower():
                icon = "🔴"
            else:
                icon = "⚠️"

            unit = metric["unit"]
            value = metric["value"]
            if unit == "ms" and value >= 1000:
                display = f"{value/1000:.1f}s"
            elif unit == "ms":
                display = f"{value}ms"
            else:
                display = str(value)

            # Show threshold comparison
            thresholds = CWV_THRESHOLDS.get(name, {})
            good = thresholds.get("good", "?")
            threshold_unit = thresholds.get("unit", "")
            threshold_str = f"(target: <{good}{threshold_unit})" if good != "?" else ""

            print(f"  {icon} {metric['label']}: {display} {threshold_str}")

    if result["opportunities"]:
        print(f"\nTop Opportunities:")
        for opp in result["opportunities"][:5]:
            savings = opp["savings_ms"]
            if savings >= 1000:
                display = f"{savings/1000:.1f}s"
            else:
                display = f"{savings}ms"
            print(f"  💡 {opp['title']} (save ~{display})")

    if result["diagnostics"]:
        print(f"\nDiagnostics:")
        for diag in result["diagnostics"]:
            print(f"  ⚠️ {diag['title']}: {diag['display']}")


if __name__ == "__main__":
    main()
