# CHANGES THE OPEN FILE: places elements from SPEC on level ZZ-AGENT-TEST (creates the level if missing). Run on a copy only.
# APIs follow Bentley's CreateElements.py sample: LineHandler, ShapeHandler, DgnBoxDetail, DraftingElementSchema, ElementPropertiesSetter.
LEVEL = "ZZ-AGENT-TEST"
# Spec in MASTER units (the model's working unit, for example meters). One dict per element.
SPEC = [
    {"type": "line", "points": [[0, 0, 0], [10, 0, 0]]},
    {"type": "shape", "points": [[0, 5, 0], [10, 5, 0], [10, 15, 0], [0, 15, 0]]},  # closed for you
    {"type": "box", "center": [5, 25, 1.5], "size": [10, 6, 3]},                    # needs a 3D model
]

model = ISessionMgr.GetActiveDgnModelRef()
dgn = model.GetDgnFile()
is3d = model.Is3d()
info = model.GetDgnModel().GetModelInfo()
_, uor = info.StorageUnit.ConvertDistanceFrom(info.UorPerStorage, info.MasterUnit)  # UOR per master unit


def pt(p):
    return DPoint3d(p[0] * uor, p[1] * uor, (p[2] if len(p) > 2 else 0) * uor)


cache = dgn.GetLevelCache()
if not cache.GetLevelByName(LEVEL).IsValid():
    if not cache.CreateLevel(LEVEL, LEVEL_NULL_CODE, LEVEL_NULL_ID).IsValid():
        raise RuntimeError("CreateLevel failed for " + LEVEL)
    cache.Write()
level_id = cache.GetLevelByName(LEVEL).GetLevelId()


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
    else:
        raise RuntimeError("unknown type: " + kind)
    if status != BentleyStatus.eSUCCESS:
        raise RuntimeError("create failed, status " + str(status))
    setter = ElementPropertiesSetter()
    setter.SetLevel(level_id)
    setter.Apply(eeh)
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
