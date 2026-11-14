import sys, resvg_py, pathlib
w=int(sys.argv[1])
for f in sys.argv[2:]:
    try:
        b=resvg_py.svg_to_bytes(svg_path=f,width=w)
        pathlib.Path(f).with_suffix('.png').write_bytes(bytes(b))
    except Exception as e: print('FAIL',f,str(e)[:80])
