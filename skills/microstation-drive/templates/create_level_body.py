# CHANGES THE OPEN FILE: creates one level and writes it. Run on a copy only.
# APIs: FileLevelCache.CreateLevel, EditLevelHandle.SetByLevel*, PersistentLevelCache.Write.
NAME = "ZZ-AGENT-TEST"

dgn = ISessionMgr.GetActiveDgnFile()
cache = dgn.GetLevelCache()
before = cache.GetLevelCount()

if cache.GetLevelByName(NAME).IsValid():
    raise RuntimeError("level already exists: " + NAME)

lv = cache.CreateLevel(NAME, LEVEL_NULL_CODE, LEVEL_NULL_ID)
if not lv.IsValid():
    raise RuntimeError("CreateLevel failed for " + NAME)

weight_ok = lv.SetByLevelWeight(3)
color_ok = lv.SetByLevelColor(LevelDefinitionColor(3, dgn))
write_status = cache.Write()

back = cache.GetLevelByName(NAME)  # read back from the cache
result = {
    "created": back.IsValid(),
    "name": back.GetName(),
    "id": back.GetLevelId(),
    "weight": back.GetByLevelWeight(),
    "color_index": back.GetByLevelColor().GetColor(),
    "set_weight_ok": weight_ok,
    "set_color_ok": color_ok,
    "write_status": str(write_status),
    "count_before": before,
    "count_after": cache.GetLevelCount(),
}
