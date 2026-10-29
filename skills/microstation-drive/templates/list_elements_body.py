# Read-only: count graphic elements in the active model by level name and element type code. Changes nothing.
# Set LEVEL to also list the id, type and range (in master units) of each element on one level ("" to skip).
LEVEL = "ZZ-AGENT-TEST"

model = ISessionMgr.GetActiveDgnModelRef()
dgn_model = model.GetDgnModel()
names = {lv.GetLevelId(): lv.GetName() for lv in dgn_model.GetDgnFile().GetLevelCache()}
info = dgn_model.GetModelInfo()
_, uor = info.StorageUnit.ConvertDistanceFrom(info.UorPerStorage, info.MasterUnit)  # UOR per master unit

counts = {}
on_level = []
total = 0
for ref in dgn_model.GetGraphicElements():
    total += 1
    name = names.get(ref.GetLevel(), "id" + str(ref.GetLevel()))
    key = name + " | type " + str(ref.GetElementType())
    counts[key] = counts.get(key, 0) + 1
    if LEVEL and (name == LEVEL or ref.GetElementType() == 2):  # cell headers are listed on any level
        item = {"id": ref.GetElementId(), "type": ref.GetElementType(), "level": name}
        try:
            eeh = EditElementHandle(ref, dgn_model)
            rng = DRange3d()
            eeh.GetHandler().CalcElementRange(eeh, rng, None)
            item["range_master"] = [[round(c / uor, 3) for c in (rng.low.x, rng.low.y, rng.low.z)],
                                    [round(c / uor, 3) for c in (rng.high.x, rng.high.y, rng.high.z)]]
        except Exception as ex:
            item["range_error"] = str(ex)
        try:
            getter = ElementPropertiesGetter(eeh)
            item["color"] = getter.GetColor()
            item["weight"] = getter.GetWeight()
            if ref.GetElementType() == 17:  # text
                item["text"] = TextHandlerBase.GetFirstTextPartValue(eeh).ToString()
            elif ref.GetElementType() == 2:  # cell header
                item["cell_name"] = NormalCellHeaderHandler.GetInstance().ExtractName(eeh)[1]
                item["children"] = []
                child = ChildElemIter(eeh, ExposeChildrenReason.eQuery)
                while child.IsValid():
                    cg = ElementPropertiesGetter(child)
                    item["children"].append({"type": child.GetElementType(), "level": names.get(cg.GetLevel(), "id" + str(cg.GetLevel())),
                                             "color": cg.GetColor(), "weight": cg.GetWeight()})
                    child = child.ToNext()
        except Exception as ex:
            item["props_error"] = str(ex)
        on_level.append(item)

result = {"file": str(dgn_model.GetDgnFile().GetFileName()), "total_graphic_elements": total,
          "by_level_and_type": counts, "on_level": on_level}
