# CHANGES THE OPEN FILE: places elements from SPEC on level ZZ-AGENT-TEST (creates the level if missing). Run on a copy only.
# APIs follow Bentley's samples: CreateElements.py (LineHandler, ShapeHandler, ArcHandler, TextElemHandler, NormalCellHeaderHandler,
# SharedCellDefHandler, DgnBoxDetail, ElementPropertiesSetter), DrawBSPLine.py, TextTableSample.py, DimensionAuto.py.
import math

LEVEL = "ZZ-AGENT-TEST"
# Spec in MASTER units (the model's working unit, for example meters). One dict per element.
# Optional on every item: "level" (a level name; made if the file has none; default LEVEL), "color" (color table index),
# "rgb" [r, g, b] (true colour, wins over "color"), "weight" (0 to 31),
# "style" (line style code 0 to 7: 0 is solid, the others are the standard dashed codes).
# Item types: line, shape, box, arc, circle, ellipse, polyline, bspline, chain, text, cell, shared_cell, table, dimension. Examples:
#   {"type": "bspline", "points": [[0, 0, 0], [10, 8, 0], [20, -4, 0]]}                    curve through the points
#   {"type": "chain", "segments": [{"line": [[0, 0], [40, 0]]}, {"arc": [[40, 0], [55, 4], [66, 15]]}], "offsets": [3.5, -3.5]}
#       line and arc (start, a point on the arc, end) segments; each offset adds a parallel chain, positive = right of the travel direction
#   {"type": "text", "origin": [5, 5, 0], "text": "ROOM 1", "height": 0.5, "just": "cm", "rot_deg": 0, "text_style": "AGENT-TEXT"}
#       "just" is two letters: l c r (left center right) + t m b (top middle baseline); default is "lt". "\n" starts a new line.
#   {"type": "shared_cell", "name": "TREE", "lines": [[[-1, 0], [1, 0]], [[0, -1], [0, 1]]], "at": [[10, 10], [20, 10]], "scale": 1, "deg": 0}
#       "lines" defines the cell (leave it out when the cell already exists in the file); every "at" gets one instance
#   {"type": "table", "origin": [0, 50, 0], "rows": [["ID", "ITEM"], ["D1", "DOOR"]], "height": 0.5}   origin is the top-left corner
#   {"type": "dimension", "kind": "linear", "points": [[0, 0], [10, 0]], "offset": 2}
#       "offset" is how far the dimension line sits from the points: positive = to the LEFT of the direction a to b, negative = to the right
#       (for a to b along +x, positive is above the line, negative below)
#   kinds: linear [a, b] with "offset"; radius [center, point on the circle, where the text goes]; diameter [center, point on the circle];
#          angle [vertex, point on the first leg, point on the second leg]. "text_height" sets the dimension text size (default 1).
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


def level_id_of(name):  # the level id for a name; creates the level if the file does not have it
    if not cache.GetLevelByName(name).IsValid():
        if not cache.CreateLevel(name, LEVEL_NULL_CODE, LEVEL_NULL_ID).IsValid():
            raise RuntimeError("CreateLevel failed for " + name)
        cache.Write()
    return cache.GetLevelByName(name).GetLevelId()


level_id = level_id_of(LEVEL)  # the default level; an item can name its own with "level"
ident = RotMatrix()
ident.InitIdentity()
JUST = {"l": "Left", "c": "Center", "r": "Right"}
JUST_V = {"t": "Top", "m": "Middle", "b": "Baseline"}


class DimData(IDimCreateData):  # what DimensionHandler.CreateDimensionElement asks for, as in Bentley's DimensionAuto.py
    def __init__(self, dim_style, text_style, rmat, level):
        super().__init__()
        self.dim_style, self.text_style, self.rmat, self.level = dim_style, text_style, rmat, level
        self.formatter = DirectionFormatter.Create()

    def _GetDimStyle(self):
        return self.dim_style

    def _GetTextStyle(self):
        return self.text_style

    def _GetSymbology(self):
        return Symbology(0, 0, 0)

    def _GetLevelID(self):
        return self.level

    def _GetViewNumber(self):
        return 1

    def _GetDimRMatrix(self):
        return self.rmat

    def _GetViewRMatrix(self):
        return self.rmat

    def _GetDirFormat(self):
        return self.formatter

    def _GetAnnScaleAllowed(self):
        return True


def style(eeh, item):
    setter = ElementPropertiesSetter()
    setter.SetLevel(level_id_of(item["level"]) if "level" in item else level_id)
    if "rgb" in item:
        setter.SetColor(DgnColorMap.CreateElementColor(IntColorDef(*item["rgb"]), None, None, dgn))
    elif "color" in item:
        setter.SetColor(item["color"])
    if "weight" in item:
        setter.SetWeight(item["weight"])
    if "style" in item and item["type"] not in ("text", "table", "dimension"):
        setter.SetLinestyle(item["style"], None)
    setter.Apply(eeh)


def add(eeh, item):
    style(eeh, item)
    if eeh.AddToModel() != BentleyStatus.eSUCCESS:
        raise RuntimeError("AddToModel failed")
    return eeh.GetElementId()


def text_style(name, height, bold=False, italic=False):  # gets the named text style from the file or makes it
    ts = DgnTextStyle.GetByName(name, dgn)
    if ts is None:
        ts = DgnTextStyle(name, dgn)
        ts.SetDoubleProperty(TextStyleProperty.eTextStyle_Height, height * uor)
        ts.SetDoubleProperty(TextStyleProperty.eTextStyle_Width, height * uor)
        ts.SetBoolProperty(TextStyleProperty.eTextStyle_Bold, bold)
        ts.SetBoolProperty(TextStyleProperty.eTextStyle_Italics, italic)
        if ts.Add(dgn) != BentleyStatus.eSUCCESS:
            raise RuntimeError("text style " + name + " could not be added")
        ts = DgnTextStyle.GetByName(name, dgn)  # the stored copy has an ID
    return ts


def dim_style(name, text_h, item):  # gets the named dimension style from the file or makes one with visible text and arrowheads
    ds = DimensionStyle.GetByName(name, dgn)
    if ds is None:
        ds = DimensionStyle(name, dgn)
        ds.SetAccuracyProp(item.get("accuracy", 130), DimStyleProp.eDIMSTYLE_PROP_Value_Accuracy_ACCURACY)  # length: 130 = 2 decimals, 129 = 1, 132 = 4, 0 = whole numbers, 1 to 8 = fractions
        ds.SetBooleanProp(item.get("trailing_zeros", True), DimStyleProp.eDIMSTYLE_PROP_Value_ShowTrailingZeros_BOOLINT)  # 12.00, not 12
        ds.SetBooleanProp(item.get("angle_measure", True), DimStyleProp.eDIMSTYLE_PROP_Value_AngleMeasure_BOOLINT)  # False shows the arc LENGTH, not the angle
        if "angle_precision" in item:
            ds.SetIntegerProp(item["angle_precision"], DimStyleProp.eDIMSTYLE_PROP_Value_AnglePrecision_INTEGER)
        ds.SetDoubleProp(1.0, DimStyleProp.eDIMSTYLE_PROP_General_DimensionScale_DOUBLE)
        ds.SetBooleanProp(True, DimStyleProp.eDIMSTYLE_PROP_Text_OverrideHeight_BOOLINT)
        ds.SetBooleanProp(True, DimStyleProp.eDIMSTYLE_PROP_Text_OverrideWidth_BOOLINT)
        ds.SetDistanceProp(text_h * uor, DimStyleProp.eDIMSTYLE_PROP_Text_Height_DISTANCE, None)
        ds.SetDistanceProp(text_h * uor, DimStyleProp.eDIMSTYLE_PROP_Text_Width_DISTANCE, None)
        ds.SetIntegerProp(1, DimStyleProp.eDIMSTYLE_PROP_Terminator_Mode_INTEGER)
        ds.SetIntegerProp(0, DimStyleProp.eDIMSTYLE_PROP_Terminator_Arrowhead_INTEGER)
        ds.SetIntegerProp(1, DimStyleProp.eDIMSTYLE_PROP_Terminator_Left_TEMPLATEFLAG)
        ds.SetIntegerProp(1, DimStyleProp.eDIMSTYLE_PROP_Terminator_Right_TEMPLATEFLAG)
        if ds.Add() != BentleyStatus.eSUCCESS:
            raise RuntimeError("dimension style " + name + " could not be added")
        ds = DimensionStyle.GetByName(name, dgn)
    return ds


def build_dimension(eeh, item):
    h = item.get("text_height", 1)
    dstyle = dim_style(item.get("dim_style", "AGENT-DIM"), h, item)
    kinds = {"linear": DimensionType.eSizeArrow, "radius": DimensionType.eRadius, "diameter": DimensionType.eDiameter, "angle": DimensionType.eAngleSize}
    pts = [pt(p) for p in item["points"]]
    rmat = ident
    if item["kind"] == "linear":  # the dimension runs along a to b
        xv = DVec3d.FromStartEnd(pts[0], pts[1])
        xv.Normalize()
        rmat = RotMatrix.From2Vector(xv, DVec3d(-xv.y, xv.x, 0.0))
    data = DimData(dstyle, text_style(item.get("dim_text_style", "AGENT-DIM-TEXT"), h), rmat, level_id_of(item["level"]) if "level" in item else level_id)
    status = DimensionHandler.GetInstance().CreateDimensionElement(eeh, data, kinds[item["kind"]], is3d, dgn_model)
    if status == BentleyStatus.eSUCCESS:
        dim = eeh.GetHandler()
        for p in pts:
            if dim.InsertPoint(eeh, p, None, dstyle, -1) != BentleyStatus.eSUCCESS:
                raise RuntimeError("dimension InsertPoint failed")
        if item["kind"] == "linear":
            dim.SetHeight(eeh, item.get("offset", 1) * uor * dstyle.GetUorScale(dgn_model))
    return status


def build(item):  # returns the list of ids it placed
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
        status = ArcHandler.CreateArcElement(eeh, None, pt(item["center"]), item["rx"] * uor, item["ry"] * uor, ident,
                                             math.radians(item.get("start_deg", 0)), math.radians(item["sweep_deg"]), is3d, model)
    elif kind in ("circle", "ellipse"):  # in the XY plane; a circle is an ellipse with rx = ry
        rx = item["r"] if kind == "circle" else item["rx"]
        ry = item["r"] if kind == "circle" else item["ry"]
        status = EllipseHandler.CreateEllipseElement(eeh, None, pt(item["center"]), rx * uor, ry * uor, ident, is3d, model)
    elif kind == "polyline":  # open line string, 2 or more points
        status = LineStringHandler.CreateLineStringElement(eeh, None, [pt(p) for p in item["points"]], is3d, model)
    elif kind == "bspline":  # a smooth curve that passes through the points (verified: distance to every point 0.0000)
        pts = DPoint3dArray()
        for p in item["points"]:
            pts.append(pt(p))
        curve = MSBsplineCurve.CreateFromInterpolationAtBasisFunctionPeaks(pts, item.get("order", 4), 0)
        # note: CalcElementRange of a B-spline is the range of its control polygon, which is larger than the curve
        status = BentleyStatus.eSUCCESS if BSplineCurveHandler.CreateBSplineCurveElement(eeh, None, curve, is3d, model) == BSplineStatus.eBSPLINE_STATUS_Success else BentleyStatus.eERROR
    elif kind == "chain":  # connected lines and arcs as one complex string, e.g. a road centre line, with optional parallel offsets
        cv = CurveVector(CurveVector.eBOUNDARY_TYPE_Open)
        for seg in item["segments"]:
            if "line" in seg:
                cv.Add(ICurvePrimitive.CreateLine(DSegment3d(pt(seg["line"][0]), pt(seg["line"][1]))))
            else:
                a, m, b = seg["arc"]
                cv.Add(ICurvePrimitive.CreateArc(DEllipse3d.FromPointsOnArc(pt(a), pt(m), pt(b))))
        ids = []
        for d in ([None] if item.get("base", True) else []) + list(item.get("offsets", [])):  # "base": false places only the offsets
            curves = cv if d is None else cv.CloneOffsetCurvesXY(CurveOffsetOptions(d * uor))
            e = EditElementHandle()
            if DraftingElementSchema.ToElement(e, curves, None, is3d, model) != BentleyStatus.eSUCCESS:
                raise RuntimeError("chain create failed")
            ids.append(add(e, item))
        return ids
    elif kind == "text":  # "height" is the character height; default font is the default TrueType font
        h = item.get("height", 1) * uor
        para = ParagraphProperties.Create(dgn_model)
        if "just" in item:
            para.SetJustification(getattr(TextElementJustification, "e" + JUST[item["just"][0]] + JUST_V[item["just"][1]]))
        if "text_style" in item:
            run = RunProperties.Create(text_style(item["text_style"], item.get("height", 1), item.get("bold", False), item.get("italic", False)), dgn_model)
        else:
            run = RunProperties.Create(DgnFontManager.GetDefaultTrueTypeFont(), DPoint2d(h, h), dgn_model)
        block = TextBlock(TextBlockProperties.Create(dgn_model), para, run, dgn_model)
        for i, part in enumerate(item["text"].split("\n")):
            if i:
                block.AppendLineBreak()
            block.AppendText(part)
        block.SetUserOrigin(pt(item["origin"]))
        if "rot_deg" in item:
            block.SetOrientation(RotMatrix.FromAxisAndRotationAngle(2, math.radians(item["rot_deg"])))
        if TextElemHandler.CreateElement(eeh, None, block) != TextBlockToElementResult.eTEXTBLOCK_TO_ELEMENT_RESULT_Success:
            raise RuntimeError("text create failed")
        status = BentleyStatus.eSUCCESS
    elif kind == "cell":  # an unshared cell built from lines; level, color and weight go on every child. The header stays on level 0 (six ways tried, see SKILL.md)
        NormalCellHeaderHandler.CreateOrphanCellElement(eeh, item["name"], is3d, model)
        for a, b in item["lines"]:
            child = EditElementHandle()
            if LineHandler.CreateLineElement(child, None, DSegment3d(pt(a), pt(b)), is3d, model) != BentleyStatus.eSUCCESS:
                raise RuntimeError("cell child create failed")
            style(child, item)
            NormalCellHeaderHandler.AddChildElement(eeh, child)
        NormalCellHeaderHandler.AddChildComplete(eeh)
        status = BentleyStatus.eSUCCESS
    elif kind == "shared_cell":  # one definition, many instances: the definition lives in the file, each instance only points to it
        if item.get("lines"):
            d = EditElementHandle()
            SharedCellDefHandler.CreateSharedCellDefElement(d, item["name"], is3d, dgn_model)
            for a, b in item["lines"]:
                child = EditElementHandle()
                LineHandler.CreateLineElement(child, None, DSegment3d(pt(a), pt(b)), is3d, model)
                style(child, item)
                SharedCellDefHandler.AddChildElement(d, child)
            SharedCellDefHandler.AddChildComplete(d)
            if d.AddToModel() != BentleyStatus.eSUCCESS:
                raise RuntimeError("shared cell definition failed")
        ids = []
        s = item.get("scale", 1)
        for at in item["at"]:
            inst = EditElementHandle()
            SharedCellHandler.CreateSharedCellElement(inst, None, item["name"], pt(at), RotMatrix.FromAxisAndRotationAngle(2, math.radians(item.get("deg", 0))),
                                                      DPoint3d(s, s, s), is3d, dgn_model)
            if SharedCellHandler.CreateSharedCellComplete(inst) != BentleyStatus.eSUCCESS:
                raise RuntimeError("shared cell instance failed (is the definition in the file?)")
            ids.append(add(inst, item))
        return ids
    elif kind == "table":  # a real MicroStation text table; origin is the top-left corner
        ts = text_style(item.get("text_style", "AGENT-TEXT-TABLE"), item.get("height", 1))
        rows = item["rows"]
        tbl = TextTable.Create(len(rows), max(len(r) for r in rows), ts.ID, ts.GetDoubleProperty(TextStyleProperty.eTextStyle_Height)[1], dgn_model)
        tbl.Origin = pt(item["origin"])
        if "col_width" in item:
            tbl.DefaultColumnWidth = item["col_width"] * uor
        if "row_height" in item:
            tbl.DefaultRowHeight = item["row_height"] * uor
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                tb = TextBlock(ts, dgn_model)
                tb.AppendText(str(val))
                tbl.GetCell(TableCellIndex(r, c)).SetTextBlock(tb)
        status = TextTableHandler.CreateTextTableElement(eeh, tbl, dgn_model)
    elif kind == "dimension":
        status = build_dimension(eeh, item)
    else:
        raise RuntimeError("unknown type: " + kind)
    if status != BentleyStatus.eSUCCESS:
        raise RuntimeError("create failed, status " + str(status))
    return [add(eeh, item)]


placed = []
for item in SPEC:
    try:
        ids = build(item)
        placed.append({"type": item["type"], "ok": True, "id": ids[0], "ids": ids})
    except Exception as ex:  # keep going so one bad item does not hide the others
        placed.append({"type": item["type"], "ok": False, "error": str(ex)})

result = {"level": LEVEL, "level_id": level_id, "is3d": is3d, "uor_per_master": uor, "placed": placed}
