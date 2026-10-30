# Prints the active model to a PDF with MicroStation's own PDF driver. Changes nothing in the drawing.
# Based on Bentley's Plot/Pdf/PdfPlot.py. Printing can block MicroStation for minutes on a big drawing: warn first.
import os

OUT = os.path.join(os.environ["USERPROFILE"], "MicroStation-Agent", "results", "plot.pdf")

printref = PrintDescriptionRef.Create()
desc = printref.GetP()
init_status = desc.InitializeFromTCB("pdf.pltcfg")  # the PDF driver config shipped with MicroStation
desc.Maximize()  # fill the paper size the driver selects; the area printed is what view 1 shows (SetFenceFromFitRange gave a blank page)
if os.path.exists(OUT):
    os.remove(OUT)
print_status = desc.Print(OUT)
exists = os.path.exists(OUT)
result = {"pdf": OUT, "init_status": init_status, "print_status": print_status,
          "exists": exists, "bytes": os.path.getsize(OUT) if exists else 0}
