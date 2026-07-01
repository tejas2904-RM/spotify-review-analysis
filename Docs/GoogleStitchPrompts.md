# Google Stitch UI Generation Prompts
## Spotify Review Analysis Dashboard

Use each prompt below in [Google Stitch](https://stitch.withgoogle.com) to generate screen mockups for the dashboard. Copy one prompt at a time.

---

## Design System Reference (use in every prompt)

> **Always include this block at the start of your Stitch session before the screen-specific prompts.**

```
Design system:
- Theme: dark, Spotify-inspired
- Background: #000000 (page canvas), #121212 (cards/panels), #1a1a1a (sidebar)
- Accent: #1DB954 (Spotify green) — used for active states, icons, highlights, progress bars
- Text: #FFFFFF (headings), #B3B3B3 (secondary), #535353 (muted/placeholder)
- Danger/negative: #E84040
- Border: #2a2a2a (subtle card borders)
- Border radius: 8px on all cards
- Font: Inter, clean sans-serif
- Sidebar: 224px fixed left, full height, black background, Spotify logo + green wordmark at top
- Layout: sidebar + scrollable main content area
- Icon library: Lucide icons (outlined, monochrome)
- Chart colors: #1DB954 green, #E84040 red, #B3B3B3 grey
```

---

## Screen 1 — Overview (Home)

```
Design a dark analytics dashboard screen called "Overview" for a Spotify review analysis tool.

Layout:
- Fixed left sidebar (224px wide, black #000000 background) with Spotify circle logo in green at top, app name "Review Analysis" in white/green, and 7 navigation items: Overview (active, highlighted green icon + white text on dark grey #2a2a2a pill), Sentiment, Themes, Pain Points, User Segments, AI Summaries, Opportunities. Footer: "Spotify Review Engine / 1,799 reviews analysed" in muted grey.
- Main content area (black background) with horizontal padding.

Main content sections (top to bottom):

1. Page title "Overview" in bold white 30px. Subtitle in grey: "AI-powered analysis of 1,799 relevant Spotify user reviews"

2. Four KPI cards in a horizontal row (dark #121212, 8px radius, subtle border):
   - "Relevant Reviews" — value "1,799" large bold white, sub "1,799 enriched (100%)" grey, icon: bar chart (green)
   - "Positive Sentiment" — value "30%" green, sub "Avg score 0.41" grey, icon: trending up (green)
   - "Churn Risk Users" — value "28%" red, sub "511 reviews flagged" grey, icon: users (red)
   - "Opportunities" — value "6" green, sub "Product recommendations" grey, icon: lightbulb (green)

3. Two-column chart row:
   - Left (1/3 width): Card "Sentiment Split" with a donut chart — 30% green, 17% grey, 52% red, legend below
   - Right (2/3 width): Card "Top Themes" with a horizontal bar chart — bars in Spotify green, 8 themes: Competitor Comparison, UI/UX, Feature Request, Pricing, Algorithm, Discovery, Ads, Recommendations

4. Full-width card "Relevant Reviews by Source" — horizontal grouped bar chart showing 4 sources: Google Play (844), YouTube (834), Hacker News (81), Spotify Community (40). Bars in Spotify green.

Style: all cards dark #121212, white headings, grey subtitles, green accent details, Spotify green progress indicators.
```

---

## Screen 2 — Sentiment Analysis

```
Design a dark analytics dashboard screen called "Sentiment" for a Spotify review analysis tool.

Use the same sidebar layout as Screen 1 (Sentiment nav item is now active with green icon).

Main content sections:

1. Page title "Sentiment Analysis" bold white. Subtitle: "How users feel about Spotify across all sources"

2. Three metric summary cards in a row:
   - "Positive" — "30%" in Spotify green (#1DB954), large bold, sub "540 reviews"
   - "Neutral" — "17%" in grey (#B3B3B3), sub "312 reviews"  
   - "Negative" — "52%" in red (#E84040), large bold, sub "947 reviews"

3. Large donut chart card (full width or 50%) titled "Overall Sentiment Distribution" — three segments: green 30%, grey 17%, red 52%. Center shows total "1,799 reviews". Clean legend to the right.

4. "Sentiment by Source" — horizontal stacked bar chart showing 4 rows (Google Play, YouTube, Hacker News, Spotify Community), each bar split into green/grey/red segments proportionally.

5. "Sentiment Over Time" — line chart with 3 lines (green=positive, grey=neutral, red=negative) showing monthly trend over 12 months, x-axis = months, dark grid lines.

Style: dark theme, all cards #121212, Spotify green highlights, clean typography.
```

---

## Screen 3 — Themes

```
Design a dark analytics dashboard screen called "Themes" for a Spotify review analysis tool.

Use the same sidebar layout (Themes nav item active).

Main content sections:

1. Page title "Themes" bold white. Subtitle: "Most discussed topics across 1,799 reviews"

2. Full-width horizontal bar chart card titled "Theme Frequency" — 10 horizontal bars in Spotify green (#1DB954), sorted descending:
   Competitor Comparison (698), UI/UX (354), Feature Request (317), Pricing (278), Algorithm (237), Discovery (233), Ads (199), Recommendations (168), Churn Risk (165), Repetition (139)
   Labels on left, count numbers on right end of each bar.

3. Two-column row:
   - Left: "Theme Sentiment" — small grouped horizontal bars per theme, each split green/grey/red
   - Right: "Theme Co-occurrence" — heatmap or bubble matrix showing which themes appear together (e.g. Algorithm + Discovery frequently co-occur), cells in varying green opacity

4. "Theme Trends Over Time" — area/line chart showing top 5 themes as separate coloured lines over 12 months.

Style: dark cards, Spotify green primary colour, white text headings, grey subtitles.
```

---

## Screen 4 — Pain Points

```
Design a dark analytics dashboard screen called "Pain Points" for a Spotify review analysis tool.

Use the same sidebar layout (Pain Points nav item active).

Main content sections:

1. Page title "Pain Points" bold white. Subtitle: "Top user frustrations ranked by frequency and severity"

2. "Top Pain Points" — ranked list card (dark #121212):
   Each row shows: rank number (green), pain point text (white), frequency badge (grey pill), severity badge (red pill for high, yellow for medium, grey for low), source icons.
   Example rows:
   - #1 "Algorithm repeats the same songs constantly" — 312 mentions — HIGH severity — red badge
   - #2 "Discovery feature fails to surface new artists" — 287 mentions — HIGH — red
   - #3 "Pricing increase not justified by improvement" — 201 mentions — MEDIUM — yellow
   - #4 "Ads too frequent on free tier" — 189 mentions — MEDIUM — yellow
   - #5 "Spotify Wrapped feels shallow and repetitive" — 134 mentions — LOW — grey
   Show 8-10 rows total.

3. "Feature Requests" — similar list card with lightbulb icon, green accent:
   Each row: feature name (white), count (green badge), category tag.
   Examples: "Better new artist recommendations (203)", "Offline mode improvements (156)", "Mood-based playlists (134)"

4. "Pain Points by Theme" — small horizontal bar chart showing which themes have the most pain points.

Style: dark, severity colour coding (red/yellow/grey), Spotify green for positive elements, ranking numbers in green.
```

---

## Screen 5 — User Segments

```
Design a dark analytics dashboard screen called "User Segments" for a Spotify review analysis tool.

Use the same sidebar layout (User Segments nav item active).

Main content sections:

1. Page title "User Segments" bold white. Subtitle: "How different user types experience Spotify"

2. "Segment Distribution" — donut or pie chart card showing 4 segments:
   - Churn Risk: 28% (red)
   - Casual: 35% (grey)
   - Power User: 22% (Spotify green)
   - New User: 15% (light blue/teal)
   Clean legend on right side.

3. Four segment summary cards in a 2x2 grid:
   - "Churn Risk" card: red left border accent, count "511", key complaint "Algorithm repetition, pricing", icon users-x
   - "Casual Users" card: grey left border, count "630", key trait "Occasional listeners, ad-sensitive"
   - "Power Users" card: green left border, count "396", key trait "Feature-hungry, playlist builders"
   - "New Users" card: blue left border, count "262", key trait "Onboarding friction, discovery confusion"

4. "Sentiment by Segment" — grouped horizontal bar chart, 4 rows (one per segment), each split green/grey/red.

5. "Churn Risk Signals" — list card with warning icon:
   Each row: signal text in white, occurrence count in red badge.
   e.g. "Mentions switching to Apple Music (203)", "Cancellation language detected (178)"

Style: segment colour coding consistent throughout, red = churn risk, green = power user.
```

---

## Screen 6 — AI Summaries

```
Design a dark analytics dashboard screen called "AI Summaries" for a Spotify review analysis tool.

Use the same sidebar layout (AI Summaries nav item active).

Main content sections:

1. Page title "AI Summaries" bold white. Subtitle: "LLM-generated summaries per theme and source"

2. Filter tabs row: "By Theme" (active, green underline) | "By Source"

3. Theme summary cards — vertical scrollable list of cards (dark #121212):
   Each card:
   - Header: theme name in white bold + review count badge in grey pill (e.g. "Competitor Comparison · 698 reviews")
   - Spotify green left border accent (3px)
   - Summary paragraph in grey/light text, 3-4 sentences of analytical insight
   - Bottom tags: top keywords as small grey pills (e.g. "Apple Music", "YouTube Music", "switching")

   Show 4-5 theme summary cards:
   - "Competitor Comparison" — summary about users comparing Spotify unfavourably to Apple Music and YouTube Music
   - "Algorithm" — summary about repetition complaints and discovery failures
   - "Pricing" — summary about premium price hikes and perceived value decline
   - "Feature Request" — summary about most-wanted features

4. Small "By Source" tab content (collapsed/shown as tab): 4 source summary cards for Google Play, YouTube, Hacker News, Spotify Community with platform icons.

Style: rich text cards, Spotify green left accents, readable paragraph text, clean keyword tags.
```

---

## Screen 7 — Opportunities

```
Design a dark analytics dashboard screen called "Opportunities" for a Spotify review analysis tool.

Use the same sidebar layout (Opportunities nav item active).

Main content sections:

1. Page title "Opportunities" bold white. Subtitle: "AI-generated product recommendations based on user feedback"

2. Full-width banner card with Spotify green gradient left edge:
   "6 product opportunities identified from 1,799 user reviews"
   Subtext: "Generated by GPT-4o-mini based on pain points, feature requests, and sentiment trends"
   Lightbulb icon in green.

3. Six opportunity cards in a 2-column grid (dark #121212, 8px radius):
   Each card:
   - Priority badge top-right: "HIGH" (red pill) / "MEDIUM" (yellow pill) / "LOW" (grey pill)
   - Bold white title (e.g. "Fix Discovery Algorithm", "Transparent Pricing Communication")
   - Short description paragraph in grey (2-3 lines)
   - Bottom row: impact tag (green) + effort tag (grey) + affected segment tag

   Example cards:
   - "Redesign Discovery Algorithm" — HIGH — "Users cite repetitive recommendations as top reason for churn. Personalisation improvements could directly reduce the 28% churn-risk segment."
   - "Introduce Mood-Based Radio" — MEDIUM — "Strong demand for mood and context-aware playlists across all user segments"
   - "Revamp Spotify Wrapped" — LOW — "Users find current Wrapped shallow; deeper artist insights would increase engagement"
   - "Improve Offline Experience" — MEDIUM
   - "Address Premium Value Perception" — HIGH
   - "Build Better Artist Discovery Pathways" — HIGH

Style: priority colour coding, green impact/action highlights, professional card layout with clear hierarchy.
```

---

## Tips for Google Stitch

1. Start a new Stitch session and paste the **Design System Reference** first to set the global style.
2. Then paste each screen prompt one at a time.
3. If the generated image is too light or too generic, add: *"Make the background strictly #000000 black, not dark grey. Use #1DB954 green only as an accent, not as a background fill."*
4. To iterate: *"Keep the same layout but make the sidebar narrower and the charts taller."*
5. For higher fidelity: *"Generate this as a high-fidelity Figma-ready mockup, pixel-perfect, with realistic data labels."*
