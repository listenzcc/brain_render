# %%
import time
import numpy as np

import imutils
# from PIL import Image

from tqdm.auto import tqdm

import plotly.express as px

from data import mat_atlas, mat_brain

# %%

print(np.unique(mat_atlas))
print(mat_atlas.shape)
print(mat_brain.shape)

# %%


def rotate(mat, axis, deg, copy=False, verbose=False):
    if copy:
        mat = mat.copy()

    # kwargs = dict(
    #     resample=Image.BICUBIC,
    #     # resample=Image.BILINEAR,
    # )

    def _wrapper(a, b):
        print('Wrapping: {}, {}'.format(a, b))
        return a

    if verbose:
        wrapper = tqdm
    else:
        wrapper = _wrapper

    if axis == 0:
        for j in wrapper(range(mat.shape[0]), 'Rotate axis-{}'.format(axis)):
            mat[j] = imutils.rotate(mat[j], angle=deg)

            # img = Image.fromarray(mat[j].astype(np.uint8))
            # rotate_img = img.rotate(deg, **kwargs)
            # mat[j] = rotate_img

    if axis == 1:
        for j in wrapper(range(mat.shape[1]), 'Rotate axis-{}'.format(axis)):
            mat[:, j] = imutils.rotate(mat[:, j], angle=deg)

            # img = Image.fromarray(mat[:, j].astype(np.uint8))
            # rotate_img = img.rotate(deg, **kwargs)
            # mat[:, j] = rotate_img

    if axis == 2:
        for j in wrapper(range(mat.shape[2]), 'Rotate axis-{}'.format(axis)):
            mat[:, :, j] = imutils.rotate(mat[:, :, j], angle=deg)

            # img = Image.fromarray(mat[:, :, j].astype(np.uint8))
            # rotate_img = img.rotate(deg, **kwargs)
            # mat[:, :, j] = rotate_img

    return mat


# %%
select = 31
degrees = [10, 20, 50]

start = time.time()

brain = mat_brain.copy()
brain *= 255 / np.max(brain)

atlas = mat_atlas * 0
atlas[mat_atlas == select] = 255
print('Cost {} seconds'.format(time.time() - start))

for j, deg in enumerate(degrees):
    rotate(brain, j, deg)
    rotate(atlas, j, deg)
print('Cost {} seconds'.format(time.time() - start))

# Volume view
for j in range(3):
    img1 = np.mean(brain, axis=j).transpose()[::-1]
    img2 = np.mean(atlas, axis=j).transpose()[::-1]

    img1 *= 255 / np.max(img1) * 0.5
    img2 *= 255 / np.max(img2) * 0.7

    img3 = np.array([img1 + img2, img1, img1]).transpose((1, 2, 0))

    img3[img3 > 255] = 255
    img3 = img3.astype(np.uint8)

    fig = px.imshow(img3, title='Volume view, Axis-{}'.format(j))
    fig.show()


# Slice in 3 direction view
for j in range(3):
    if j == 0:
        img1 = brain[50].transpose()[::-1].copy()
        img2 = atlas[50].transpose()[::-1].copy()

    if j == 1:
        img1 = brain[:, 50].transpose()[::-1].copy()
        img2 = atlas[:, 50].transpose()[::-1].copy()

    if j == 2:
        img1 = brain[:, :, 50].transpose()[::-1].copy()
        img2 = atlas[:, :, 50].transpose()[::-1].copy()

    img1 *= 255 / np.max(img1) * 0.5
    if np.max(img2) > 0:
        img2 *= 255 / np.max(img2) * 0.5

    img3 = np.array([img1 + img2, img1, img1],
                    dtype=np.uint8).transpose((1, 2, 0))

    fig = px.imshow(img3, title='Slice view, Axis-{}'.format(j))
    fig.show()

print('Cost {} seconds'.format(time.time() - start))

# %%

# %%
