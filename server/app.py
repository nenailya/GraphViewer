from enum import Enum

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import os

from python.handler import handler as py_handler
from kotlin.handler import handler as kt_handler
from c.handler import handler as c_handler
from go.handler import handler as go_handler
from java.handler import handler as java_handler
from javascript.handler import handler as js_handler

functions = {'python': ('ast', 'cfg'), 'kotlin': ('ast', 'cfg'), 'c': ('ast', 'cfg', 'ssa'), 'go': ('ast', 'cfg'),
             'java': ('ast', 'cfg'), 'javascript': ('ast',)}
handlers = {"python": py_handler, "kotlin": kt_handler, "c": c_handler, 'go': go_handler, 'java': java_handler,
            'javascript': js_handler}


class Format(str, Enum):
    png = 'image/png'
    svg = 'image/svg+xml'
    pdf = 'application/pdf'
    dot = 'text/dot'


example_code = """
a = 2 + 2 * (c * d / 2)
b = a + a / 2
if b > 4:
    print('hello')
else:
    print('nooo')
print('exit')
"""

app = FastAPI()
app.mount("/client", StaticFiles(directory="../client"), name="client")


@app.get("/")
async def root(request: Request):
    return FileResponse('../client/views/index.html')


@app.get("/vk", tags=['User'])
async def vk(request: Request, code: str):
    #return code
    site = "https://oauth.vk.com/access_token"
    client_id = os.environ['client_id']
    secret = os.environ['client_secret']
    redirect = 'http://localhost:8000/vk'
    url = f"{site}?client_id={client_id}&client_secret={secret}&redirect_uri={redirect}&code={code}"
    res = requests.get(url)
    data: dict = res.json()
    code = data.get('access_token')
    if code is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Error')


@app.get("/save")
async def save(request: Request):
    pass


@app.get('/functions')
async def all_functions():
    """return all available languages and models"""
    return functions


@app.get('/view_graph')
async def view_graph(code: str = example_code, lang: str = "python", model: str = "ast"):
    if lang in functions and model in functions[lang]:
        try:
            data = handlers.get(lang)(code, model)
            return Response(data, media_type=f"text/dot")
        except SyntaxError as e:
            raise HTTPException(400, detail=str(e))
        except Exception as e:
            raise HTTPException(400, detail=str(e))
    else:
        raise HTTPException(400, "Language and model not implemented")


# @app.get('/python_ast', response_class=StreamingResponse)
# async def ast(format: Format, code: str = example_code):
#     data = python_ast.make(code, format=format.name)
#     return StreamingResponse(data, media_type=format.value)
#
#
# @app.get('/python_cfg')
# async def cfg(code: str = example_code):
#     data = python_cfg.make(code)
#     return StreamingResponse(data, media_type=f"text/dot")
#

# @app.get('/c_ssa', response_class=Response)
# async def c_ssa(code: str = c_handler_.example_code):
#     try:
#         data = c_handler_.handler(code, model='ssa')
#     except RuntimeError as e:
#         raise HTTPException(400, detail=str(e))
#     return Response(data, media_type=f"text/dot")
#
#
# @app.get('/c_cfg', response_class=Response)
# async def c_cfg(code: str = c_handler_.example_code):
#     try:
#         data = c_handler_.handler(code, model='cfg')
#     except RuntimeError as e:
#         raise HTTPException(400, detail=str(e))
#     return Response(data, media_type=f"text/dot")


if __name__ == '__main__':
    print(os.environ['client_id'])
    uvicorn.run('app:app', host='0.0.0.0', port=8000, reload=True, debug=True)
