# %%
import time
import json

from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

from .brain_render import brain_render

# %%


def index(request):
    ''' Index page '''
    print(request)

    place_holders = dict(
        load_on_time=time.ctime()
    )

    return render(request, 'index.html', place_holders)

# %%


def atlas_table(request):
    ''' Json byte of the atlas table '''
    print(request)

    atlas_table = brain_render.atlas_table

    content = atlas_table.to_dict()

    return JsonResponse(content)

# %%


def volume_render(request):
    ''' PNG bytes of the volume render '''
    print(request)

    params = dict()
    for e in request.GET:
        params[e] = request.GET[e]

    kwargs = dict(
        slice=int(params.get('slice', 50)),
        select=int(params.get('select', 31)),
        degrees=(
            int(float(params.get('degX', 10))),
            int(float(params.get('degY', 20))),
            int(float(params.get('degZ', 30))),
        ),
        degrees_2=(
            int(float(params.get('degX2', 0))),
            int(float(params.get('degY2', 0))),
            int(float(params.get('degZ2', 0))),
        )
    )

    print(kwargs)

    content = brain_render.render(**kwargs)
    content_type = "image/png"

    return HttpResponse(content, content_type)


# %%
def slice_render(request):
    ''' PNG bytes of the slice '''
    print(request)

    params = dict()
    for e in request.GET:
        params[e] = request.GET[e]

    kwargs = dict(
        slice=int(params.get('slice', 50)),
        select=int(params.get('select', 31)),
        degrees=(
            int(float(params.get('degX', 10))),
            int(float(params.get('degY', 20))),
            int(float(params.get('degZ', 30))),
        ),
        degrees_2=(
            int(float(params.get('degX2', 0))),
            int(float(params.get('degY2', 0))),
            int(float(params.get('degZ2', 0))),
        )
    )

    print(kwargs)

    content = brain_render.slice(**kwargs)
    content_type = "image/png"

    return HttpResponse(content, content_type)
