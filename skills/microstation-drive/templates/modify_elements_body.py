# CHANGES THE OPEN FILE: moves, copies, rotates, scales, restyles or deletes existing elements. Run on a copy only.
# APIs follow Bentley's DgnTool samples: ElementMover, ElementCopyTool, ElementRotateTool, ElementScaleTool,
# and DeleteCellsOnPath (EditElementHandle.DeleteFromModel).
import math

LEVEL = "ZZ-AGENT-TEST"
# Distances in MASTER units. Each op picks elements with "select" (needs "ids", "level" or "cell" = a cell name; "types" narrows by element type code),
# then applies one operation. "expect" is the number of elements you expect to match: the op does nothing if it differs.
# "expect" is required for delete.
OPS = [
    {"op": "move", "select": {"level": LEVEL, "types": [3]}, "by": [2, 0, 0], "expect": 1},
    {"op": "copy", "select": {"level": LEVEL, "types": [6]}, "by": [20, 0, 0], "expect": 1},
    {"op": "rotate", "select": {"level": LEVEL, "types": [16]}, "about": [5, 35, 0], "deg": 90, "expect": 1},
    {"op": "scale", "select": {"level": LEVEL, "types": [19]}, "about": [5, 25, 0], "factor": 2, "expect": 1},
    {"op": "props", "select": {"level": LEVEL, "types": [17]}, "color": 2, "weight": 3, "expect": 1},
    {"op": "delete", "select": {"cell": "AGENT-CELL"}, "expect": 1},
]

model = ISessionMgr.GetActiveDgnModelRef()
dgn_model = model.GetDgnModel()
cache = dgn_model.GetDgnFile().GetLevelCache()
info = dgn_model.GetModelInfo()
_, uor = info.StorageUnit.ConvertDistanceFrom(info.UorPerStorage, info.MasterUnit)  # UOR per master unit
names = {lv.GetLevelId(): lv.GetName() for lv in cache}


def vec(p):
    return DVec3d(p[0] * uor, p[1] * uor, (p[2] if len(p) > 2 else 0) * uor)


def pnt(p):
    return DPoint3d(p[0] * uor, p[1] * uor, (p[2] if len(p) > 2 else 0) * uor)


def cell_name(ref):
    return NormalCellHeaderHandler.GetInstance().ExtractName(EditElementHandle(ref, dgn_model))[1]


def select(sel):
    if not (sel.get("ids") or sel.get("level") or sel.get("cell")):
        raise RuntimeError("select needs ids, level or cell")
    ids = []
    for ref in dgn_model.GetGraphicElements():  # collect first, change after: never edit while iterating
        if sel.get("ids") and ref.GetElementId() not in sel["ids"]:
            continue
        if sel.get("level") and names.get(ref.GetLevel()) != sel["level"]:
            continue
        if sel.get("types") and ref.GetElementType() not in sel["types"]:
            continue
        if sel.get("cell") and (ref.GetElementType() != 2 or cell_name(ref) != sel["cell"]):  # cell headers sit on level 0, so match by name
            continue
        ids.append(ref.GetElementId())
    return ids


def rng(eeh):
    r = DRange3d()
    eeh.GetHandler().CalcElementRange(eeh, r, None)
    return [[round(c / uor, 3) for c in (r.low.x, r.low.y, r.low.z)], [round(c / uor, 3) for c in (r.high.x, r.high.y, r.high.z)]]


def transform_of(op):
    if op["op"] in ("move", "copy"):
        t = Transform()
        t.InitFrom(vec(op["by"]))
        return t
    if op["op"] == "rotate":
        c = pnt(op["about"])
        return Transform.FromLineAndRotationAngle(c, DPoint3d(c.x, c.y, c.z + uor), math.radians(op["deg"]))
    f = op["factor"]
    return Transform.FromFixedPointAndScaleFactors(pnt(op["about"]), f, f, f)


def restyle(eeh, op):
    setter = ElementPropertiesSetter()
    if "level" in op:
        lv = cache.GetLevelByName(op["level"])
        if not lv.IsValid():
            raise RuntimeError("no level " + op["level"])
        setter.SetLevel(lv.GetLevelId())
    if "color" in op:
        setter.SetColor(op["color"])
    if "weight" in op:
        setter.SetWeight(op["weight"])
    return setter.Apply(eeh)


def run(op):
    if op["op"] == "delete" and "expect" not in op:
        raise RuntimeError("delete needs expect")
    ids = select(op["select"])
    if "expect" in op and len(ids) != op["expect"]:
        return {"op": op["op"], "done": False, "error": "expected %d elements, found %d" % (op["expect"], len(ids)), "ids": ids}
    out = []
    for i in ids:
        eeh = EditElementHandle(i, model)
        old = eeh.GetElementRef()  # keep it: a change can build a new descriptor (text does), and ReplaceInModel needs the old ref
        item = {"id": i, "before": rng(eeh)}
        if op["op"] == "delete":
            item["status"] = eeh.DeleteFromModel()
        elif op["op"] == "props":
            item["applied"] = restyle(eeh, op)  # as in Bentley's samples: replace only when Apply says True
            item["status"] = eeh.ReplaceInModel(old) if item["applied"] else 1
            item["after"] = rng(eeh)
        else:
            target = eeh
            if op["op"] == "copy":
                target = EditElementHandle()
                target.Duplicate(eeh)
            item["status"] = target.GetHandler(eMISSING_HANDLER_PERMISSION_Transform).ApplyTransform(target, TransformInfo(transform_of(op)))
            if item["status"] == 0:
                item["status"] = target.AddToModel() if op["op"] == "copy" else target.ReplaceInModel(old)
            item["after"] = rng(target)
            if op["op"] == "copy":
                item["new_id"] = target.GetElementId()
        out.append(item)
    return {"op": op["op"], "done": all(x["status"] == 0 for x in out), "changed": out}


result = []
for op in OPS:
    try:
        result.append(run(op))
    except Exception as ex:  # keep going so one bad op does not hide the others
        result.append({"op": op["op"], "done": False, "error": str(ex)})
