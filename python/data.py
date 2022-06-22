'''
Read the data from everywhere
'''
# %%
import os
import numpy as np
import pandas as pd

import nibabel as nib
from imio import load
from vedo import Volume

from tqdm.auto import tqdm
from bs4 import BeautifulSoup as bs

from pathlib import Path

# %%
# Where the data is stored
base_folder = Path(__file__).parent
brain_raw_path = base_folder.joinpath(
    '../assets/fsl/standard/MNI152_T1_2mm_brain.nii.gz')
atlas_raw_path = base_folder.joinpath(
    '../assets/fsl/standard/HarvardOxford-cort-maxprob-thr25-2mm_YCG.nii')
xml_raw_path = base_folder.joinpath(
    '../assets/fsl/atlases/HarvardOxford-Cortical.xml')

# The stuff will be stored here
folder_raw_path = base_folder.joinpath('./cells_vertices')

# %%
# Read the mat of the nii file,
# it is the 3-D matrix, with the dtype of float64
mat_brain = nib.load(brain_raw_path).get_fdata()

mat_atlas = nib.load(atlas_raw_path).get_fdata()


# %%
if __name__ == '__main__':
    # Create the folder if it doesn't exist
    folder = Path(folder_raw_path)

    if not folder.is_dir():
        os.mkdir(folder)

    def mk_atlas_table(xml_raw_path=xml_raw_path):
        '''
        Make the table of atlas,
        the columns are

        | -- | name |  center   | idx |
        | -- | name | x | y | z | idx |

        '''

        path = Path(xml_raw_path)

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

    def mk_mesh(raw_path, select_value=None):
        '''
        Make the mesh for the raw_path input,

        Args:
            - raw_path, the full path of the .nii file;
            - select_value, default is None,
                if it is provided, the value will be used to mask the ROI,
                and ONLY the mesh of the ROI will be built.

        Returns:
            - The mesh.
        '''
        path = Path(raw_path)
        mni_mat = load.load_any(path)

        if select_value is not None:
            mni_mat[mni_mat != select_value] = 0
        print('Selected {} voxels'.format(np.count_nonzero(mni_mat)))

        vol = Volume(mni_mat)
        mesh = vol.isosurface()

        return mesh

    def mesh2cells_vertices(mesh, idx_value=0):
        '''
        Convert the mesh into the pairs of (cells, vertices)
            - cells: The cells of the mesh, the elements are the indices of the vertices;
            - vertices: The vertices of the mesh, the elements are the position of the vertices.

        Args:
            - mesh: The mesh to be converted;
            - idx_value: The index value to be added to the cells and vertices, default is 0.

        Returns:
            - The pair of (cells, vertices)
        '''

        cells = pd.DataFrame(mesh.cells(), columns=['v0', 'v1', 'v2'])
        vertices = pd.DataFrame(mesh.vertices(), columns=['x', 'y', 'z'])

        cells['idx'] = idx_value
        vertices['idx'] = idx_value

        return cells, vertices

    # Read the files and convert them into useable format,
    # and store them.

    # --------------------------------------------------------------------------------
    # Atlas table
    atlas_table = mk_atlas_table()
    atlas_table.to_csv(folder.joinpath('atlas_table.csv'))
    atlas_table

    # --------------------------------------------------------------------------------
    # Mesh and vertices of the brain
    mesh = mk_mesh(brain_raw_path)
    mesh.write(folder.joinpath('brain.obj').as_posix())

    cells, vertices = mesh2cells_vertices(mesh, 0)

    cells.to_csv(folder.joinpath('cells-0.csv'))
    vertices.to_csv(folder.joinpath('vertices-0.csv'))

    # --------------------------------------------------------------------------------
    # Mesh and vertices of the atlas
    cells_lst = []
    vertices_lst = []

    for i in tqdm(atlas_table['idx']):
        mesh = mk_mesh(atlas_raw_path, i)
        cells, vertices = mesh2cells_vertices(mesh, i)
        cells_lst.append(cells)
        vertices_lst.append(vertices)

    def _merge(lst):
        merged = pd.concat(lst, axis=0)
        merged.index = range(len(merged))
        return merged

    all_cells = _merge(cells_lst)
    all_vertices = _merge(vertices_lst)

    all_cells.to_csv(folder.joinpath('cells-all.csv'))
    all_vertices.to_csv(folder.joinpath('vertices-all.csv'))

    # %%
