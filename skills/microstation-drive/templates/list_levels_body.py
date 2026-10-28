# Read-only: list every level in the active model's file. Changes nothing.
# APIs checked in MSPyDgnPlatform.pyi (LevelCache, LevelHandle, LevelDefinitionColor).
model = ISessionMgr.GetActiveDgnModelRef()
dgn = model.GetDgnFile()
cache = dgn.GetLevelCache()

levels = []
for lv in cache:
    levels.append({
        "id": lv.GetLevelId(),
        "code": lv.GetLevelCode(),
        "name": lv.GetName(),
        "description": lv.GetDescription(),
        "color_index": lv.GetByLevelColor().GetColor(),  # index in the color table, not RGB
        "weight": lv.GetByLevelWeight(),
        "style": lv.GetByLevelLineStyle().GetStyle(),
        "display": lv.GetDisplay(),
        "frozen": lv.GetFrozen(),
        "plot": lv.GetPlot(),
    })

# count = levels stored in the file; with_libraries also counts attached level libraries (DGNLIB)
result = {"file": str(dgn.GetFileName()), "count": cache.GetLevelCount(),
          "count_with_libraries": cache.GetLevelCount(True), "levels": levels}
