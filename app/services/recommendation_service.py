"""Rule-based layout suggestions (AI MVP)."""


def _estimate_cost(width, length, floors, cols, rows, pillar_size):
  pillar_count = cols * rows * floors
  bay_w = width / max(cols - 1, 1)
  bay_l = length / max(rows - 1, 1)
  beam_len = (cols * (rows - 1) * bay_l + rows * (cols - 1) * bay_w) * floors
  slab_area = width * length * floors
  concrete = pillar_count * (pillar_size ** 2) * 3.5 + beam_len * 0.3 * 0.4 + slab_area * 0.15
  steel = concrete * 80
  brick = floors * (width + length) * 2 * 3.0 * 0.2
  return round(concrete * 120 + steel * 1.2 + brick * 45, 2)


def suggest_layouts(width=30.0, length=20.0, floors=3, floor_height=3.5):
  width = float(width or 30)
  length = float(length or 20)
  floors = max(1, int(floors or 1))
  candidates = [
    {
      "id": "balanced",
      "label": "Balanced grid",
      "description": "Even 4×3 spacing — good default for mid-rise.",
      "grid_cols": 4,
      "grid_rows": 3,
      "pillar_width": 0.4,
      "pillar_depth": 0.4,
      "tradeoff": "Best cost-to-span balance for most buildings.",
    },
    {
      "id": "economy",
      "label": "Economy layout",
      "description": "Wider 3×2 bay — fewer pillars, longer beams.",
      "grid_cols": 3,
      "grid_rows": 2,
      "pillar_width": 0.45,
      "pillar_depth": 0.45,
      "tradeoff": "Lower pillar count; beams carry more load.",
    },
    {
      "id": "dense",
      "label": "Dense support",
      "description": "Tighter 5×4 grid with slimmer columns.",
      "grid_cols": 5,
      "grid_rows": 4,
      "pillar_width": 0.35,
      "pillar_depth": 0.35,
      "tradeoff": "Higher material use; shorter spans.",
    },
    {
      "id": "heavy",
      "label": "Heavy columns",
      "description": "3×3 grid with oversized pillars for commercial loads.",
      "grid_cols": 3,
      "grid_rows": 3,
      "pillar_width": 0.55,
      "pillar_depth": 0.55,
      "tradeoff": "Higher capacity per bay; fewer heavier elements.",
    },
  ]

  suggestions = []
  for c in candidates:
    size = (c["pillar_width"] + c["pillar_depth"]) / 2
    cost = _estimate_cost(
      width, length, floors, c["grid_cols"], c["grid_rows"], size
    )
    suggestions.append(
      {
        **c,
        "grid": f"{c['grid_cols']}x{c['grid_rows']}",
        "estimated_cost": cost,
        "floor_height": floor_height,
        "floors": floors,
        "width": width,
        "length": length,
      }
    )
  return suggestions
