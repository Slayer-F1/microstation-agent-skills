# CHANGES THE OPEN FILE: places elements from SPEC on level ZZ-AGENT-TEST (creates the level if missing). Run on a copy only.
# APIs follow Bentley's CreateElements.py sample: LineHandler, ShapeHandler, ArcHandler, TextElemHandler,
# NormalCellHeaderHandler, DgnBoxDetail, DraftingElementSchema, ElementPropertiesSetter.
import math

LEVEL = "ZZ-AGENT-TEST"
# Spec in MASTER units (the model's working unit, for example meters). One dict per element.
# Optional on every item: "color" (color table index) and "weight" (0 to 31).
SPEC = [
    {"type": "line", "points": [[0, 0, 0], [10, 0, 0]]},
    {"type": "shape", "points": [[0, 5, 0], [10, 5, 0], [10, 15, 0], [0, 15, 0]]},  # closed for you
    {"type": "box", "center": [5, 25, 1.5], "size": [10, 6, 3]},                    # needs a 3D model
    {"type": "arc", "center": [5, 35, 0], "rx": 4, "ry": 2, "start_deg": 0, "sweep_deg": 270, "color": 3, "weight": 4},
    {"type": "text", "origin": [0, 40, 0], "text": "AGENT TEST", "height": 1, "color": 5},
    {"type": "cell", "name": "AGENT-CELL", "lines": [[[0, 45, 0], [4, 49, 0]], [[4, 45, 0], [8, 49, 0]]], "weight": 2},
]

model = ISessionMgr.GetActiveDgnModelRef()
dgn = model.GetDgnFile()
dgn_model = model.GetDgnModel()
is3d = model.Is3d()
info = dgn_model.GetModelInfo()
_, uor = info.StorageUnit.ConvertDistanceFrom(info.UorPerStorage, info.MasterUnit)  # UOR per master unit


def pt(p):
    return DPoint3d(p[0] * uor, p[1] * uor, (p[2] if len(p) > 2 else 0) * uor)


cache = dgn.GetLevelCache()
if not cache.GetLevelByName(LEVEL).IsValid():
    if not cache.CreateLevel(LEVEL, LEVEL_NULL_CODE, LEVEL_NULL_ID).IsValid():
        raise RuntimeError("CreateLevel failed for " + LEVEL)
    cache.Write()
level_id = cache.GetLevelByName(LEVEL).GetLevelId()


def style(eeh, item):
    setter = ElementPropertiesSetter()
    setter.SetLevel(level_id)
    if "color" in item:
        setter.SetColor(item["color"])
    if "weight" in item:
        setter.SetWeight(item["weight"])
    setter.Apply(eeh)


def build(item):
    eeh = EditElementHandle()
    kind = item["type"]
    if kind == "line":
        a, b = item["points"]
        status = LineHandler.CreateLineElement(eeh, None, DSegment3d(pt(a), pt(b)), is3d, model)
    elif kind == "shape":
        pts = DPoint3dArray()
        for p in item["points"]:
            pts.append(pt(p))
        pts.append(pt(item["points"][0]))  # close the shape
        status = ShapeHandler.CreateShapeElement(eeh, None, pts, is3d, model)
    elif kind == "box":
        if not is3d:
            raise RuntimeError("box needs a 3D model")
        size = item["size"]
        detail = DgnBoxDetail.InitFromCenterAndSize(pt(item["center"]), DPoint3d(size[0] * uor, size[1] * uor, size[2] * uor), True)
        status = DraftingElementSchema.ToElement(eeh, ISolidPrimitive.CreateDgnBox(detail), None, model)
    elif kind == "arc":  # elliptical arc in the XY plane, angles counter-clockwise from the +X axis
        rot = RotMatrix()
        rot.InitIdentity()
        status = ArcHandler.CreateArcElement(eeh, None, pt(item["center"]), item["rx"] * uor, item["ry"] * uor, rot,
                                             math.radians(item.get("start_deg", 0)), math.radians(item["sweep_deg"]),
                                             is3d, model)
    elif kind == "text":  # "height" is the character height; default font is the default TrueType font
        h = item.get("height", 1) * uor
        run = RunProperties.Create(DgnFontManager.GetDefaultTrueTypeFont(), DPoint2d(h, h), dgn_model)
        block = TextBlock(TextBlockProperties.Create(dgn_model), ParagraphProperties.Create(dgn_model), run, dgn_model)
        block.AppendText(item["text"])
        block.SetUserOrigin(pt(item["origin"]))
        if TextElemHandler.CreateElement(eeh, None, block) != TextBlockToElementResult.eTEXTBLOCK_TO_ELEMENT_RESULT_Success:
            raise RuntimeError("text create failed")
        status = BentleyStatus.eSUCCESS
    elif kind == "cell":  # an unshared cell built from lines; level, color and weight go on every child
        NormalCellHeaderHandler.CreateOrphanCellElement(eeh, item["name"], is3d, model)
        for a, b in item["lines"]:
            child = EditElementHandle()
            if LineHandler.CreateLineElement(child, None, DSegment3d(pt(a), pt(b)), is3d, model) != BentleyStatus.eSUCCESS:
                raise RuntimeError("cell child create failed")
            style(child, item)
            NormalCellHeaderHandler.AddChildElement(eeh, child)
        NormalCellHeaderHandler.AddChildComplete(eeh)
        status = BentleyStatus.eSUCCESS
    else:
        raise RuntimeError("unknown type: " + kind)
    if status != BentleyStatus.eSUCCESS:
        raise RuntimeError("create failed, status " + str(status))
    style(eeh, item)
    if eeh.AddToModel() != BentleyStatus.eSUCCESS:
        raise RuntimeError("AddToModel failed")
    return eeh.GetElementId()


placed = []
for item in SPEC:
    try:
        placed.append({"type": item["type"], "ok": True, "id": build(item)})
    except Exception as ex:  # keep going so one bad item does not hide the others
        placed.append({"type": item["type"], "ok": False, "error": str(ex)})

result = {"level": LEVEL, "level_id": level_id, "is3d": is3d, "uor_per_master": uor, "placed": placed}
