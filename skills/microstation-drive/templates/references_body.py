# list, attach or detach reference files (DGN attachments) of the active model.
# "list" changes nothing; "attach" and "detach" CHANGE THE OPEN FILE: run on a copy only.
# Based on Bentley's DgnElements/Reference/Reference.py.
import os

ACTION = "list"  # "list", "attach" or "detach"
FILE = r"C:\full\path\to\reference.dgn"  # attach: file to attach. detach: matched by file name.
MODEL = ""  # model inside FILE; "" = its default model

model = ISessionMgr.GetActiveDgnModelRef()


def listing():
    out = []
    for att in model.GetDgnAttachments() or []:
        out.append({"model": att.GetAttachModelName(), "file": str(att.GetAttachFileName()), "displayed": att.IsDisplayed()})
    return out


def find():
    want = os.path.basename(FILE).lower()
    for att in model.GetDgnAttachments() or []:
        if os.path.basename(str(att.GetAttachFileName())).lower() == want and (not MODEL or att.GetAttachModelName() == MODEL):
            return att
    return None


status = None
if ACTION == "attach":
    ret = model.CreateDgnAttachment(DgnDocumentMoniker.CreateFromFileName(FILE), MODEL or None, False)
    status = ret[0]
    if status == BentleyStatus.eSUCCESS:
        att = ret[1]
        att.SetIsDisplayed(True)
        att.SetLocateLock(True)
        att.SetSnapLock(True)
        status = att.WriteToModel()
elif ACTION == "detach":
    att = find()
    status = model.DeleteDgnAttachment(att) if att else "not attached"
elif ACTION != "list":
    raise RuntimeError("ACTION must be list, attach or detach")
result = {"action": ACTION, "status": status, "attachments": listing()}
