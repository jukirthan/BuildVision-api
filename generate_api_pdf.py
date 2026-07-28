"""Generate BuildVision API Endpoints Role-Access PDF (template style)."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
  Paragraph,
  SimpleDocTemplate,
  Spacer,
  Table,
  TableStyle,
)

OUT = Path(__file__).resolve().parent.parent / "BuildVision_API_Endpoints_Role_Access.pdf"

# Columns match: API endpoints --role access - Template.pdf
HEADERS = [
  "#",
  "Endpoint",
  "Method",
  "Description",
  "Access (Role)",
  "Request Body (JSON)",
  "Params / Query",
  "Response (Success)",
  "Response (Error)",
  "Status Codes",
  "Controller / Function",
  "Notes",
]

ROWS = [
  [
    "1",
    "/api/users/register",
    "POST",
    "Register a new user",
    "Public",
    '{ "name": "John", "email": "john@mail.com", "password": "123456", "role": "engineer" }',
    "-",
    '{ "message": "User registered successfully", "data": { "user": {...} } }',
    '{ "error": "Email already exists" }',
    "201, 400",
    "registerUser()",
    "Role: engineer | architect | contractor. Admin cannot self-register. Verification email stubbed.",
  ],
  [
    "2",
    "/api/users/login",
    "POST",
    "Login user",
    "Public",
    '{ "email": "john@mail.com", "password": "123456" }',
    "-",
    '{ "token": "<JWT>", "access_token": "<JWT>", "user": {...} }',
    '{ "error": "Invalid credentials" }',
    "200, 401",
    "loginUser()",
    "Returns JWT token",
  ],
  [
    "3",
    "/api/users/profile",
    "GET",
    "Get logged-in user profile",
    "Private (User, Admin) — engineer, architect, contractor, admin",
    "-",
    "-",
    '{ "name": "John", "email": "john@mail.com", "role": "engineer" }',
    '{ "error": "Unauthorized" }',
    "200, 401",
    "getUserProfile()",
    "Token required",
  ],
  [
    "4",
    "/api/users/profile",
    "PUT",
    "Update logged-in user profile",
    "Private — engineer, architect, contractor, admin",
    '{ "name"?, "email"?, "password"? }',
    "-",
    '{ "data": { user } }',
    '{ "error": "Email already exists" }',
    "200, 400, 401",
    "updateUserProfile()",
    "Cannot self-escalate role",
  ],
  [
    "5",
    "/api/users/",
    "GET",
    "List all users",
    "Admin",
    "-",
    "-",
    '{ "data": [ users ] }',
    '{ "error": "Forbidden" }',
    "200, 403",
    "get_all_users()",
    "Admin only",
  ],
  [
    "6",
    "/api/users/",
    "POST",
    "Create user (any role)",
    "Admin",
    '{ "name", "email", "password", "role"? }',
    "-",
    '{ "data": { user } }',
    '{ "error": "Email already exists" }',
    "201, 400, 403",
    "create_user()",
    "Admin may assign admin role",
  ],
  [
    "7",
    "/api/users/<id>",
    "GET",
    "Get user by ID",
    "Self or Admin",
    "-",
    "user_id",
    '{ "data": { user } }',
    '{ "error": "Forbidden" } / 404',
    "200, 403, 404",
    "get_user()",
    "-",
  ],
  [
    "8",
    "/api/users/<id>",
    "PUT",
    "Update user",
    "Self or Admin",
    '{ "name"?, "email"?, "password"?, "role"? }',
    "user_id",
    '{ "data": { user } }',
    '{ "error": "Forbidden" }',
    "200, 403",
    "update_user()",
    "Only admin can change roles",
  ],
  [
    "9",
    "/api/users/<id>",
    "DELETE",
    "Delete user",
    "Self or Admin",
    "-",
    "user_id",
    '{ "message": "User deleted" }',
    '{ "error": "Forbidden" }',
    "200, 403, 404",
    "delete_user()",
    "-",
  ],
  [
    "10",
    "/api/projects/",
    "GET",
    "List projects",
    "engineer, architect, contractor, admin",
    "-",
    "-",
    '{ "data": [ projects ] }',
    '{ "error": "Unauthorized" }',
    "200, 401",
    "get_projects()",
    "Admin sees all; others see own projects",
  ],
  [
    "11",
    "/api/projects/",
    "POST",
    "Create project",
    "engineer, architect, admin",
    '{ "name": "Tower A", "description"?, "location"? }',
    "-",
    '{ "data": { project } }',
    '{ "error": "Forbidden" }',
    "201, 400, 403",
    "create_project()",
    "Contractor cannot create",
  ],
  [
    "12",
    "/api/projects/<id>",
    "GET",
    "Get project with buildings",
    "engineer, architect, contractor, admin",
    "-",
    "project_id",
    '{ "data": { project, buildings } }',
    "403 / 404",
    "200, 403, 404",
    "get_project()",
    "Owner or admin",
  ],
  [
    "13",
    "/api/projects/<id>",
    "PUT",
    "Update project",
    "engineer, architect, admin",
    '{ "name"?, "description"?, "location"?, "status"? }',
    "project_id",
    '{ "data": { project } }',
    "403 / 404",
    "200, 403, 404",
    "update_project()",
    "Read-only for contractor",
  ],
  [
    "14",
    "/api/projects/<id>",
    "DELETE",
    "Delete project",
    "engineer, architect, admin",
    "-",
    "project_id",
    '{ "message": "Project deleted" }',
    "403 / 404",
    "200, 403, 404",
    "delete_project()",
    "-",
  ],
  [
    "15",
    "/api/buildings/project/<project_id>",
    "GET",
    "List buildings in project",
    "engineer, architect, contractor, admin",
    "-",
    "project_id",
    '{ "data": [ buildings ] }',
    "403 / 404",
    "200, 403, 404",
    "get_buildings()",
    "View role",
  ],
  [
    "16",
    "/api/buildings/project/<project_id>",
    "POST",
    "Create building",
    "engineer, architect, admin",
    '{ "name", "width"?, "length"?, "total_floors"?, "building_type"? }',
    "project_id",
    '{ "data": { building } }',
    "403 / 400",
    "201, 400, 403",
    "create_building()",
    "Design role",
  ],
  [
    "17",
    "/api/buildings/<id>",
    "GET",
    "Get building (with floors)",
    "engineer, architect, contractor, admin",
    "-",
    "building_id",
    '{ "data": { building, floors } }',
    "403 / 404",
    "200, 403, 404",
    "get_building()",
    "-",
  ],
  [
    "18",
    "/api/buildings/<id>",
    "PUT / DELETE",
    "Update or delete building",
    "engineer, architect, admin",
    "PUT: { name?, width?, length?, … }",
    "building_id",
    "Updated building / deleted message",
    "403 / 404",
    "200, 403, 404",
    "update_building() / delete_building()",
    "Contractor read-only",
  ],
  [
    "19",
    "/api/floors/building/<building_id>",
    "GET / POST",
    "List or create floors",
    "GET: all roles · POST: engineer, architect, admin",
    'POST: { "name", "floor_number", "height"? }',
    "building_id",
    "Floor list / created floor",
    "403 / 400",
    "200, 201, 403",
    "get_floors() / create_floor()",
    "-",
  ],
  [
    "20",
    "/api/floors/<id>",
    "GET / PUT / DELETE",
    "Floor CRUD (+ components on GET)",
    "GET: all roles · write: engineer, architect, admin",
    "PUT: { name?, height?, area? }",
    "floor_id",
    "Floor detail / message",
    "403 / 404",
    "200, 403, 404",
    "FloorController",
    "GET includes pillars, beams, slabs",
  ],
  [
    "21",
    "/api/pillars/floor/<floor_id>",
    "GET / POST",
    "List or create pillars",
    "GET: all roles · POST: engineer, architect, admin",
    'POST: { "name", "x_position"?, "y_position"?, "width"?, "depth"?, "height"? }',
    "floor_id",
    "Pillar list / created pillar",
    "403 / 400",
    "200, 201, 403",
    "get_pillars() / create_pillar()",
    "Triggers structural recalculation",
  ],
  [
    "22",
    "/api/pillars/<id>/move",
    "PUT",
    "Move pillar position",
    "engineer, architect, admin",
    '{ "x_position", "y_position" }',
    "pillar_id",
    '{ "data": { pillar } }',
    "403 / 404",
    "200, 403, 404",
    "move_pillar()",
    "Cascades beams / slabs / loads",
  ],
  [
    "23",
    "/api/pillars/<id>/resize",
    "PUT",
    "Resize pillar dimensions",
    "engineer, architect, admin",
    '{ "width"?, "depth"?, "height"? }',
    "pillar_id",
    '{ "data": { pillar } }',
    "403 / 404",
    "200, 403, 404",
    "resize_pillar()",
    "Updates load capacity",
  ],
  [
    "24",
    "/api/pillars/<id>",
    "PUT / DELETE",
    "Update or delete pillar",
    "engineer, architect, admin",
    "PUT: pillar fields",
    "pillar_id",
    "Pillar / deleted message",
    "403 / 404",
    "200, 403, 404",
    "update_pillar() / delete_pillar()",
    "-",
  ],
  [
    "25",
    "/api/beams/floor/<floor_id>",
    "GET / POST",
    "List or create beams",
    "GET: all roles · POST: engineer, architect, admin",
    'POST: { "name", "start_x", "start_y", "end_x", "end_y", "width"?, "depth"? }',
    "floor_id",
    "Beam list / created beam",
    "403 / 400",
    "200, 201, 403",
    "BeamController",
    "Auto length + load bearing",
  ],
  [
    "26",
    "/api/beams/<id>",
    "GET / PUT / DELETE",
    "Beam CRUD",
    "GET: all roles · write: engineer, architect, admin",
    "PUT: beam fields",
    "beam_id",
    "Beam / message",
    "403 / 404",
    "200, 403, 404",
    "BeamController",
    "-",
  ],
  [
    "27",
    "/api/slabs/floor/<floor_id>",
    "GET / POST",
    "List or create slabs",
    "GET: all roles · POST: engineer, architect, admin",
    'POST: { "name", "thickness"?, "area"?, "reinforcement"? }',
    "floor_id",
    "Slab list / created slab",
    "403 / 400",
    "200, 201, 403",
    "SlabController",
    "-",
  ],
  [
    "28",
    "/api/slabs/<id>",
    "GET / PUT / DELETE",
    "Slab CRUD",
    "GET: all roles · write: engineer, architect, admin",
    "PUT: slab fields",
    "slab_id",
    "Slab / message",
    "403 / 404",
    "200, 403, 404",
    "SlabController",
    "-",
  ],
  [
    "29",
    "/api/dashboard/summary",
    "GET",
    "Project summary dashboard",
    "engineer, architect, contractor, admin",
    "-",
    "-",
    '{ "total_projects", "projects": [...] }',
    "401",
    "200, 401",
    "project_summary()",
    "Admin sees all projects",
  ],
  [
    "30",
    "/api/dashboard/building/<id>/statistics",
    "GET",
    "Building statistics & cost",
    "engineer, architect, contractor, admin",
    "-",
    "building_id",
    '{ "building", "materials", "floor_count" }',
    "403 / 404",
    "200, 403, 404",
    "building_statistics()",
    "Live material estimate",
  ],
  [
    "31",
    "/api/dashboard/floor/<id>/materials",
    "GET",
    "Floor materials & cost",
    "engineer, architect, contractor, admin",
    "-",
    "floor_id",
    '{ "materials": { concrete, steel, total_cost }, "components" }',
    "403 / 404",
    "200, 403, 404",
    "material_information()",
    "Contractor-friendly read",
  ],
  [
    "32",
    "/api/recommendations/floor/<floor_id>",
    "GET",
    "AI pillar layout suggestions",
    "engineer, architect, contractor, admin",
    "-",
    "floor_id",
    '{ "suggestions": [ { label, grid, estimated_cost } ] }',
    "403 / 404",
    "200, 403, 404",
    "suggest_layouts()",
    "Rule-based AI MVP",
  ],
  [
    "33",
    "/api/recommendations/layouts",
    "POST",
    "AI suggestions from footprint",
    "engineer, architect, admin",
    '{ "width", "length", "floor_height"?, "floors"? }',
    "-",
    '{ "suggestions": [...] }',
    "403 / 401",
    "200, 401, 403",
    "suggest_from_body()",
    "Compare layout trade-offs",
  ],
  [
    "34",
    "/api/auth/register",
    "POST",
    "Legacy register alias",
    "Public",
    "Same as #1",
    "-",
    "Same as #1",
    "Same as #1",
    "201, 400",
    "AuthController.register()",
    "Frontend compatibility",
  ],
  [
    "35",
    "/api/auth/login",
    "POST",
    "Legacy login alias",
    "Public",
    "Same as #2",
    "-",
    "Same as #2",
    "Same as #2",
    "200, 401",
    "AuthController.login()",
    "Frontend compatibility",
  ],
  [
    "36",
    "/api/auth/refresh",
    "POST",
    "Refresh access token",
    "Private (refresh token)",
    "-",
    "-",
    '{ "access_token": "<JWT>" }',
    "401",
    "200, 401",
    "refresh()",
    "Use refresh JWT",
  ],
  [
    "37",
    "/api/health",
    "GET",
    "API health check",
    "Public",
    "-",
    "-",
    '{ "status": "ok", "service": "BuildVision 3D API" }',
    "-",
    "200",
    "health_check()",
    "-",
  ],
]


def cell(text: str, style: ParagraphStyle) -> Paragraph:
  safe = (
    str(text)
    .replace("&", "&amp;")
    .replace("<", "&lt;")
    .replace(">", "&gt;")
    .replace("\n", "<br/>")
  )
  return Paragraph(safe, style)


def build():
  doc = SimpleDocTemplate(
    str(OUT),
    pagesize=landscape(A3),
    leftMargin=8 * mm,
    rightMargin=8 * mm,
    topMargin=10 * mm,
    bottomMargin=10 * mm,
    title="BuildVision 3D — API Endpoints Role Access",
    author="BuildVision 3D",
  )

  styles = getSampleStyleSheet()
  title_style = ParagraphStyle(
    "TitleBV",
    parent=styles["Heading1"],
    fontSize=16,
    spaceAfter=4,
    textColor=colors.HexColor("#121820"),
  )
  sub_style = ParagraphStyle(
    "SubBV",
    parent=styles["Normal"],
    fontSize=9,
    textColor=colors.HexColor("#5b6570"),
    spaceAfter=8,
  )
  head_style = ParagraphStyle(
    "HeadCell",
    fontName="Helvetica-Bold",
    fontSize=7,
    leading=9,
    alignment=TA_CENTER,
    textColor=colors.white,
  )
  body_style = ParagraphStyle(
    "BodyCell",
    fontName="Helvetica",
    fontSize=6.5,
    leading=8,
    alignment=TA_LEFT,
  )
  mono_style = ParagraphStyle(
    "MonoCell",
    fontName="Courier",
    fontSize=6,
    leading=7.5,
    alignment=TA_LEFT,
  )

  story = [
    Paragraph("BuildVision 3D — API Endpoints &amp; Role Access", title_style),
    Paragraph(
      "Template format filled for the BuildVision backend. "
      "Roles: <b>admin</b> · <b>engineer</b> · <b>architect</b> · <b>contractor</b>. "
      "Auth header: <font face='Courier'>Authorization: Bearer &lt;token&gt;</font>. "
      "Response envelope: <font face='Courier'>{ success, message, data }</font>.",
      sub_style,
    ),
  ]

  col_widths = [
    12 * mm,  # #
    42 * mm,  # endpoint
    18 * mm,  # method
    28 * mm,  # desc
    32 * mm,  # access
    40 * mm,  # body
    22 * mm,  # params
    36 * mm,  # success
    28 * mm,  # error
    18 * mm,  # status
    30 * mm,  # controller
    32 * mm,  # notes
  ]

  data = [[cell(h, head_style) for h in HEADERS]]
  for row in ROWS:
    styled = []
    for i, value in enumerate(row):
      style = mono_style if i in (1, 5, 7, 8) else body_style
      if i in (0, 2, 9):
        style = ParagraphStyle(
          "CenterCell",
          parent=body_style,
          alignment=TA_CENTER,
        )
      styled.append(cell(value, style))
    data.append(styled)

  table = Table(data, colWidths=col_widths, repeatRows=1)
  table.setStyle(
    TableStyle(
      [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2332")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        (
          "ROWBACKGROUNDS",
          (0, 1),
          (-1, -1),
          [colors.white, colors.HexColor("#f4f6f8")],
        ),
      ]
    )
  )
  story.append(table)
  story.append(Spacer(1, 8 * mm))

  role_title = ParagraphStyle(
    "RoleTitle",
    parent=styles["Heading2"],
    fontSize=11,
    textColor=colors.HexColor("#121820"),
    spaceAfter=4,
  )
  story.append(Paragraph("Role Access Summary", role_title))

  role_headers = ["Capability", "admin", "engineer", "architect", "contractor"]
  role_rows = [
    ["Register / login / profile", "✓", "✓", "✓", "✓"],
    ["Manage all users", "✓", "", "", ""],
    ["Create / edit / delete projects", "✓", "✓", "✓", ""],
    ["View projects & 3D structure", "✓", "✓", "✓", "✓"],
    ["Edit pillars / beams / slabs", "✓", "✓", "✓", ""],
    ["View materials & cost", "✓", "✓", "✓", "✓"],
    ["AI layout recommendations (GET)", "✓", "✓", "✓", "✓"],
    ["AI layout recommendations (POST)", "✓", "✓", "✓", ""],
    ["View all users' projects", "✓", "", "", ""],
  ]
  role_data = [[cell(h, head_style) for h in role_headers]]
  center = ParagraphStyle("RC", parent=body_style, alignment=TA_CENTER, fontSize=8)
  for r in role_rows:
    role_data.append(
      [cell(r[0], body_style)] + [cell(x or "—", center) for x in r[1:]]
    )

  role_table = Table(
    role_data,
    colWidths=[70 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm],
  )
  role_table.setStyle(
    TableStyle(
      [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e35b1c")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        (
          "ROWBACKGROUNDS",
          (0, 1),
          (-1, -1),
          [colors.white, colors.HexColor("#fff8f3")],
        ),
      ]
    )
  )
  story.append(role_table)

  doc.build(story)
  print(f"Wrote: {OUT}")


if __name__ == "__main__":
  build()
