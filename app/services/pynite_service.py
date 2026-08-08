"""Build and optionally analyze the real floor-owned structure with PyNite.

The geometry description is produced even when PyNite is not installed. This
keeps API validation and tests deterministic while making the analysis
dependency explicit instead of depending on generated ``.pyc`` artifacts.
"""

import math
from typing import Any, Dict, List, Optional

from app.models.building import Building


def _safe_float(value: Any, default: float = 0.0) -> float:
  try:
    return float(value)
  except (TypeError, ValueError):
    return default


def _member_ref(member: Any) -> str:
  return str(getattr(member, "client_id", None) or getattr(member, "id", "member"))


def _floor_ref(floor: Any) -> str:
  return str(getattr(floor, "client_id", None) or getattr(floor, "id", "floor"))


def _section(width: float, depth: float) -> Dict[str, float]:
  area = width * depth
  return {
    "width": width,
    "depth": depth,
    "area": area,
    "iy": width * depth ** 3 / 12,
    "iz": depth * width ** 3 / 12,
    "j": width * depth * (width ** 2 + depth ** 2) / 12,
  }


class PyniteModelBuilder:
  @staticmethod
  def build(building: Building, run_analysis: bool = False) -> Dict[str, Any]:
    floors = sorted(building.floors, key=lambda floor: floor.floor_number)
    nodes: List[Dict[str, Any]] = []
    members: List[Dict[str, Any]] = []
    pillar_top_nodes: Dict[tuple[str, str], str] = {}
    model = None
    analysis_error: Optional[str] = None

    if run_analysis:
      try:
        from Pynite import FEModel3D
        model = FEModel3D()
      except ImportError as exc:
        analysis_error = f"PyNiteFEA is not installed: {exc}"

    material_name = "BuildVisionConcrete"
    if model is not None:
      model.add_material(material_name, 25e9, 10e9, 0.2, 2400, 500e6)

    for floor in floors:
      floor_id = _floor_ref(floor)
      floor_elevation = _safe_float(floor.elevation)
      for pillar in floor.pillars:
        member_id = _member_ref(pillar)
        base_elevation = _safe_float(pillar.base_elevation, floor_elevation)
        height = _safe_float(pillar.height, _safe_float(floor.height, 3.0))
        bottom_name = f"{floor_id}:pillar:{member_id}:bottom"
        top_name = f"{floor_id}:pillar:{member_id}:top"
        nodes.extend([
          {
            "id": bottom_name,
            "floorId": floor_id,
            "memberId": member_id,
            "x": _safe_float(pillar.x_position),
            "y": _safe_float(pillar.y_position),
            "z": base_elevation,
          },
          {
            "id": top_name,
            "floorId": floor_id,
            "memberId": member_id,
            "x": _safe_float(pillar.x_position),
            "y": _safe_float(pillar.y_position),
            "z": base_elevation + height,
          },
        ])
        pillar_top_nodes[(floor_id, str(pillar.id))] = top_name
        pillar_top_nodes[(floor_id, _member_ref(pillar))] = top_name
        section = _section(_safe_float(pillar.width, 0.3), _safe_float(pillar.depth, 0.3))
        members.append({
          "id": member_id,
          "floorId": floor_id,
          "memberId": member_id,
          "stackId": getattr(pillar, "stack_id", None),
          "memberType": "pillar",
          "startNodeId": bottom_name,
          "endNodeId": top_name,
          "width": section["width"],
          "depth": section["depth"],
          "section": section,
          "height": height,
          "loads": getattr(pillar, "loads", None),
        })
        if model is not None:
          model.add_node(bottom_name, _safe_float(pillar.x_position), _safe_float(pillar.y_position), base_elevation)
          model.add_node(top_name, _safe_float(pillar.x_position), _safe_float(pillar.y_position), base_elevation + height)
          model.def_support(bottom_name, True, True, True, True, True, True)
          section_name = f"section:{member_id}"
          model.add_section(section_name, section["area"], section["iy"], section["iz"], section["j"])
          model.add_member(member_id, bottom_name, top_name, material_name, section_name)
          loads = getattr(pillar, "loads", None) or {}
          axial_kn = _safe_float(loads.get("axialKN", 0)) if isinstance(loads, dict) else 0
          if axial_kn:
            model.add_node_load(top_name, "FZ", -axial_kn * 1000, "Case 1")

      for beam in floor.beams:
        member_id = _member_ref(beam)
        start_node = pillar_top_nodes.get((floor_id, str(getattr(beam, "start_pillar_id", ""))))
        end_node = pillar_top_nodes.get((floor_id, str(getattr(beam, "end_pillar_id", ""))))
        if not start_node or not end_node:
          start_node = f"{floor_id}:beam:{member_id}:start"
          end_node = f"{floor_id}:beam:{member_id}:end"
          z = floor_elevation + _safe_float(floor.height, 3.0)
          nodes.extend([
            {"id": start_node, "floorId": floor_id, "memberId": member_id, "x": _safe_float(beam.start_x), "y": _safe_float(beam.start_y), "z": z},
            {"id": end_node, "floorId": floor_id, "memberId": member_id, "x": _safe_float(beam.end_x), "y": _safe_float(beam.end_y), "z": z},
          ])
          if model is not None:
            model.add_node(start_node, _safe_float(beam.start_x), _safe_float(beam.start_y), z)
            model.add_node(end_node, _safe_float(beam.end_x), _safe_float(beam.end_y), z)
        width = _safe_float(beam.width, 0.25)
        depth = _safe_float(beam.depth, 0.4)
        section = _section(width, depth)
        members.append({
          "id": member_id,
          "floorId": floor_id,
          "memberId": member_id,
          "stackId": None,
          "memberType": "beam",
          "startNodeId": start_node,
          "endNodeId": end_node,
          "width": width,
          "depth": depth,
          "section": section,
          "length": _safe_float(beam.length),
          "loads": getattr(beam, "loads", None),
        })
        if model is not None:
          section_name = f"section:{member_id}"
          model.add_section(section_name, section["area"], section["iy"], section["iz"], section["j"])
          model.add_member(member_id, start_node, end_node, material_name, section_name)
          loads = getattr(beam, "loads", None) or {}
          if isinstance(loads, dict):
            line_load_kn_m = _safe_float(loads.get("deadLoadKNm2", loads.get("deadLoadKNm", 0)))
            line_load_kn_m += _safe_float(loads.get("liveLoadKNm2", loads.get("liveLoadKNm", 0)))
            if line_load_kn_m:
              model.add_member_dist_load(
                member_id,
                "FZ",
                -line_load_kn_m * 1000,
                -line_load_kn_m * 1000,
                case="Case 1",
              )

    if model is not None and not model.load_combos:
      model.add_load_combo("Dead", {"Case 1": 1.0})

    if model is not None and run_analysis:
      try:
        model.analyze_linear(log=False, check_stability=False)
        combo = next(iter(model.load_combos), "Dead")
        analysis_members = getattr(model, "Members", None) or getattr(model, "members", {})
        for member in members:
          analysis_member = analysis_members.get(member["id"])
          if analysis_member is None:
            continue
          length = max(_safe_float(member.get("length"), analysis_member.L()), 1e-6)
          axial = abs(_safe_float(analysis_member.max_axial(combo)))
          shear = max(
            abs(_safe_float(analysis_member.max_shear("Fy", combo))),
            abs(_safe_float(analysis_member.max_shear("Fz", combo))),
          )
          moment = max(
            abs(_safe_float(analysis_member.max_moment("My", combo))),
            abs(_safe_float(analysis_member.max_moment("Mz", combo))),
          )
          displacement = max(
            abs(_safe_float(analysis_member.deflection("dy", length / 2, combo))),
            abs(_safe_float(analysis_member.deflection("dz", length / 2, combo))),
          )
          capacity = max(member["section"]["area"] * 25e6, 1.0)
          member["result"] = {
            "loadCombinations": [combo],
            "axialForce": axial,
            "shearForce": shear,
            "bendingMoment": moment,
            "displacement": displacement,
            "utilization": axial / capacity,
            "status": "pass" if axial / capacity <= 1 else "warning",
            "warnings": [],
          }
      except Exception as exc:  # PyNite errors are returned as structured analysis errors.
        analysis_error = str(exc)

    return {
      "available": model is not None,
      "analyzed": bool(model is not None and run_analysis and not analysis_error),
      "analysisError": analysis_error,
      "nodes": nodes,
      "members": members,
    }
