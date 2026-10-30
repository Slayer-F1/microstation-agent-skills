# Prints the active model to a PDF with MicroStation's own PDF driver. Changes nothing in the drawing.
# Based on Bentley's Plot/Pdf/PdfPlot.py. Printing can block MicroStation for minutes on a big drawing: warn first.
# With BOX it sets view 1 to a plan view of that box (wireframe, no camera) for the print, then puts the view back.
import os

OUT = os.path.join(os.environ["USERPROFILE"], "MicroStation-Agent", "results", "plot.pdf")
BOX = None     # None: print what view 1 shows. Or (x0, y0, x1, y1) in master units: the area to print.
SCALE = None   # None: fit the area to the paper. Or the scale denominator: 200 prints 1:200 (needs BOX).
PAPER = None   # None: the driver's default form (Letter). Or a form name exactly as in the plot config, e.g. "ISO A3", "ISO A4".
CONFIG = "pdf.pltcfg"  # the PDF driver config shipped with MicroStation; the engineer's organisation may have its own
MARGIN = 1.05  # room around BOX

vp = IViewManager.GetActiveViewSet().GetSelectedViewport()
vi = vp.GetViewInfo()
info = vp.GetRootModel().GetModelInfo()  # the model the view shows: units come from it, not from the active model (a sheet has its own)
_, uor = info.StorageUnit.ConvertDistanceFrom(info.UorPerStorage, info.MasterUnit)  # UOR per master unit
MM_PER_MASTER = {"m": 1000.0, "mm": 1.0, "cm": 10.0, "ft": 304.8, "in": 25.4}[str(info.MasterUnit.GetLabel()).strip().lower()]
if SCALE and not BOX:
    raise RuntimeError("SCALE needs BOX")
saved = None
if BOX:
    gi = vi.GetGeomInfo()
    r = gi.rotation
    saved = {"rot": [r.GetComponentByRowAndColumn(i, j) for i in range(3) for j in range(3)],
             "origin": (gi.origin.x, gi.origin.y, gi.origin.z), "delta": (gi.delta.x, gi.delta.y, gi.delta.z),
             "mode": gi.viewFlags.renderMode, "camera": gi.viewFlags.camera}
    x0, y0, x1, y1 = BOX
    aspect = gi.delta.x / gi.delta.y  # the window's shape; the frustum must keep it
    w = max((x1 - x0) * MARGIN, (y1 - y0) * MARGIN * aspect)
    h = w / aspect
    top = RotMatrix()
    top.InitIdentity()
    gi.rotation = top  # plan view: origin and delta are then plain model coordinates (the seed's view 1 is a rotated 3D view)
    gi.origin = DPoint3d(((x0 + x1) / 2 - w / 2) * uor, ((y0 + y1) / 2 - h / 2) * uor, -50 * uor * MM_PER_MASTER / 1000)
    gi.delta = DPoint3d(w * uor, h * uor, 100 * uor * MM_PER_MASTER / 1000)
    fl = gi.viewFlags
    fl.renderMode = 0  # wireframe: a shaded view prints as a raster and flat 2D elements can vanish
    fl.camera = 0
    gi.viewFlags = fl
    vi.SetGeomInfo(gi)
    vp.SynchWithViewInfo(False, False)

desc = PrintDescriptionRef.Create().GetP()
init_status = desc.InitializeFromTCB(CONFIG)
form_status = desc.SetFormName(PAPER) if PAPER else None
printable, total = DPoint2d(), DPoint2d()
desc.GetPaperDimensions(printable, total)
units = str(desc.GetUnits())  # PlotUnits.ein = inches, PlotUnits.emm = millimetres
paper_unit_mm = 25.4 if units.endswith("ein") else 1.0 if units.endswith("emm") else None
if paper_unit_mm is None:
    raise RuntimeError("unsupported print units " + units)
if SCALE:
    desc.SetScale(1.0, MM_PER_MASTER / SCALE / paper_unit_mm)  # 1 master unit -> paper units
else:
    desc.Maximize()
plot_mm = [round(desc.GetPlotSizeX() * paper_unit_mm, 1), round(desc.GetPlotSizeY() * paper_unit_mm, 1)]
paper_mm = [round(printable.x * paper_unit_mm, 1), round(printable.y * paper_unit_mm, 1)]
if os.path.exists(OUT):
    os.remove(OUT)
print_status = desc.Print(OUT)
exists = os.path.exists(OUT)

restored = None
if saved:
    gi = vi.GetGeomInfo()
    rot = RotMatrix()
    rot.InitFromRowValues(*saved["rot"])
    gi.rotation = rot
    gi.origin = DPoint3d(*saved["origin"])
    gi.delta = DPoint3d(*saved["delta"])
    fl = gi.viewFlags
    fl.renderMode = saved["mode"]
    fl.camera = saved["camera"]
    gi.viewFlags = fl
    vi.SetGeomInfo(gi)
    restored = str(vp.SynchWithViewInfo(False, False))
result = {"pdf": OUT, "init_status": init_status, "form_status": form_status, "print_status": print_status,
          "exists": exists, "bytes": os.path.getsize(OUT) if exists else 0,
          "paper_mm": paper_mm, "plot_mm": plot_mm, "fits": plot_mm[0] <= paper_mm[0] + 0.5 and plot_mm[1] <= paper_mm[1] + 0.5,
          "scale": ("1:%g" % SCALE) if SCALE else "fit", "view_restored": restored}
