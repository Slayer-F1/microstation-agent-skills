# CHANGES THE OPEN FILE: removes one UNUSED level and writes the file's level table. Run on a copy only.
# RemoveLevel refuses a level that has elements; never force it. APIs: FileLevelCache.RemoveLevel, Write.
NAME = "ZZ-AGENT-TEST"

dgn = ISessionMgr.GetActiveDgnFile()
cache = dgn.GetLevelCache()
before = cache.GetLevelCount()

lv = cache.GetLevelByName(NAME)
if not lv.IsValid():
    raise RuntimeError("level not found: " + NAME)
if cache.IsLevelUsedInFile(lv.GetLevelId()):
    raise RuntimeError("level has elements, not removing: " + NAME)

remove_status = cache.RemoveLevel(None, lv)
write_status = cache.Write()

result = {
    "removed": not cache.GetLevelByName(NAME).IsValid(),
    "remove_status": str(remove_status),
    "write_status": str(write_status),
    "count_before": before,
    "count_after": cache.GetLevelCount(),
}
