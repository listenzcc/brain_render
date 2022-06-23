# %%
import cv2
import time
import imutils

import numpy as np
import pandas as pd
import nibabel as nib

from pathlib import Path
from tqdm.auto import tqdm
from bs4 import BeautifulSoup as bs

import plotly.express as px

# %%
# Where the data is stored
base_folder = Path(__file__).parent
brain_raw_path = base_folder.joinpath(
    '../../assets/fsl/standard/MNI152_T1_2mm_brain.nii.gz')
atlas_raw_path = base_folder.joinpath(
    '../../assets/fsl/standard/HarvardOxford-cort-maxprob-thr25-2mm_YCG.nii')
xml_raw_path = base_folder.joinpath(
    '../../assets/fsl/atlases/HarvardOxford-Cortical.xml')

# The stuff will be stored here
# folder_raw_path = base_folder.joinpath('./cells_vertices')

# %%


def mk_atlas_table(xml_raw_path):
    '''
    Make the table of atlas,
    the columns are

    | -- | name |  center   | idx |
    | -- | name | x | y | z | idx |

    '''

    path = Path(xml_raw_path)

    assert path.is_file, 'File not found: {}'.format(path)

    def _sep_lr_atlas_table(table):
        lines = []
        table['idx'] = table.index
        for j in table.index:
            se = table.loc[j].copy()
            se['name'] += ' L'
            if se['x'] > 45:
                se['x'] = 90 - se['x']
            se['idx'] = (se['idx'] + 1) * 10 + 0
            lines.append(se)

            se = table.loc[j].copy()
            se['name'] += ' R'
            if se['x'] < 45:
                se['x'] = 90 - se['x']
            se['idx'] = (se['idx'] + 1) * 10 + 1
            lines.append(se)

        return pd.DataFrame(lines)

    soup = bs(open(path).read(), features='xml')
    soup

    lst = [(e.text, float(e.get('x')), float(e.get('y')), float(e.get('z')))
           for e in soup.find_all('label')]
    atlas_table = pd.DataFrame(lst, columns=['name', 'x', 'y', 'z'])
    atlas_table = _sep_lr_atlas_table(atlas_table)

    atlas_table.index = range(len(atlas_table))

    return atlas_table
# %%


def rotate(mat, axis, deg, copy=False, verbose=False):
    if copy:
        mat = mat.copy()

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

    if axis == 1:
        for j in wrapper(range(mat.shape[1]), 'Rotate axis-{}'.format(axis)):
            mat[:, j] = imutils.rotate(mat[:, j], angle=deg)

    if axis == 2:
        for j in wrapper(range(mat.shape[2]), 'Rotate axis-{}'.format(axis)):
            mat[:, :, j] = imutils.rotate(mat[:, :, j], angle=deg)

    return mat
# %%


class BrainRender(object):
    def __init__(self):
        self.load_mat()
        self.load_atlas_table()
        self.render(10000, (0, 0, 0))

    def load_mat(self):
        '''
        Load the 3d matrix for the brain,

        - self.brain: The brain gray pixels, in 3D shape;
        - self.atlas: The atlas pixels, the unique values are index of the atlas;
        - self.shape_3d: The shape of the brain and atlas, they are the same;
        - self.atlas_unique: The unique values of the atlas.
        '''
        mat_brain = nib.load(brain_raw_path).get_fdata()
        mat_atlas = nib.load(atlas_raw_path).get_fdata()

        self.brain = mat_brain[:91, 9:9+91, :91]
        self.atlas = mat_atlas[:91, 9:9+91, :91]
        self.shape_3d = mat_brain.shape
        self.atlas_unique = np.unique(mat_atlas)

    def load_atlas_table(self):
        '''
        Load the atlas table,

        - self.atlas_table: The table of atlas, their names, positions and indexes.
        '''
        self.atlas_table = mk_atlas_table(xml_raw_path=xml_raw_path)

    def rotate(self, select, degrees, degrees_2):
        brain = self.brain.copy()
        brain *= 255 / np.max(brain)

        atlas_mask = self.atlas.copy()
        atlas = atlas_mask * 0
        atlas[atlas_mask == select] = 255

        for j, deg in enumerate(degrees):
            rotate(brain, j, deg)
            rotate(atlas, j, deg)

        if degrees_2 is not None:
            for j, deg in enumerate(degrees_2):
                rotate(brain, j, deg)
                rotate(atlas, j, deg)

        return brain, atlas

    def slice(self, select, degrees, degrees_2=None, slice=50):
        start = time.time()

        brain, atlas = self.rotate(select, degrees, degrees_2)

        print('Stage 1, Cost {} seconds'.format(time.time() - start))

        # Volume view
        s = 0.5

        brain *= s
        atlas *= s

        img1 = brain[:, slice].transpose()[::-1]
        img2 = atlas[:, slice].transpose()[::-1]

        # img1 *= 255 / np.max(img1) * 0.8
        # if np.max(img2) > 0:
        #     img2 *= 255 / np.max(img2) * 0.7

        img3 = np.array([img1 + img2, img1, img1]).transpose((1, 2, 0))

        img3[img3 > 255] = 255
        img3 = img3.astype(np.uint8)

        success, arr = cv2.imencode(
            ext='.png', img=cv2.cvtColor(img3, cv2.COLOR_RGB2BGR))

        if not success:
            print('Something went wrong, the img fails on imencode')

        return arr.tostring()

    def render(self, select, degrees, degrees_2=None, slice=50):
        '''
        Render the brain using the volume rendering method.

        Args:
            - select: The atlas of interest, it will be marked as red color;
            - degrees: The degrees of flipping, (a, b, c) refers flipping degrees in the direction of the 3 axes;
            - degrees_2: The rotation AFTER the degrees.

        Returns:
            Something very interesting.
            It is under development, so I am not sure.
        '''
        start = time.time()

        brain, atlas = self.rotate(select, degrees, degrees_2)

        print('Stage 1, Cost {} seconds'.format(time.time() - start))

        # Volume view
        axis = 0

        for j, s in enumerate(np.linspace(0, 1, brain.shape[axis])):
            brain[j] *= s
            atlas[j] *= s

        print('Stage 2, Cost {} seconds'.format(time.time() - start))

        img1 = np.mean(brain, axis=axis).transpose()[::-1]
        img2 = np.mean(atlas, axis=axis).transpose()[::-1]

        img1 *= 255 / np.max(img1) * 0.8
        if np.max(img2) > 0:
            img2 *= 255 / np.max(img2) * 0.7

        img3 = np.array([img1 + img2, img1, img1]).transpose((1, 2, 0))

        img3[img3 > 255] = 255
        img3 = img3.astype(np.uint8)

        img3[:10, slice] = [0, 255, 255]

        success, arr = cv2.imencode(
            ext='.png', img=cv2.cvtColor(img3, cv2.COLOR_RGB2BGR))

        if not success:
            print('Something went wrong, the img fails on imencode')

        return arr.tostring()


brain_render = BrainRender()

# %%
