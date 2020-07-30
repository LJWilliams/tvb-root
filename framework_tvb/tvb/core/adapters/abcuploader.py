# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2020, Baycrest Centre for Geriatric Care ("Baycrest") and others
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
.. moduleauthor:: Mihai Andrei <mihai.andrei@codemart.ro>
"""

import os
import numpy
from abc import ABCMeta
from scipy import io as scipy_io
from tvb.basic.logger.builder import get_logger
from tvb.core.adapters.abcadapter import ABCSynchronous, ABCAdapterForm
from tvb.core.neotraits.forms import StrField
from tvb.core.neotraits.uploader_view_model import UploaderViewModel


class ABCUploaderForm(ABCAdapterForm):

    def __init__(self, prefix='', project_id=None):
        super(ABCUploaderForm, self).__init__(prefix, project_id)
        self.subject_field = StrField(UploaderViewModel.data_subject, self, name='Data_Subject')
        self.encrypted_aes_key = TraitUploadField(UploaderViewModel.encrypted_aes_key, '.pem', self,
                                                  name='encrypted_aes_key')
        self.temporary_files = []

    @staticmethod
    def get_required_datatype():
        return None

    @staticmethod
    def get_filters():
        return None

    @staticmethod
    def get_input_name():
        return None


class ABCUploader(ABCSynchronous, metaclass=ABCMeta):
    """
    Base class of the uploading algorithms
    """
    LOGGER = get_logger(__name__)

    def _prelaunch(self, operation, view_model, uid=None, available_disk_space=0):
        """
        Before going with the usual prelaunch, get from input parameters the 'subject'.
        """
        self.generic_attributes.subject = view_model.data_subject

        # TODO: After it works for single file uploaders,
        #  find a way to make it work for 2 or more file uploaders as well
        trait_upload_field_name = list(self.get_form_class().get_upload_information().keys())[0]
        self.crypto_service.decrypt_content(view_model, trait_upload_field_name)

        return ABCSynchronous._prelaunch(self, operation, view_model, uid, available_disk_space)

    def get_required_memory_size(self, view_model):
        """
        Return the required memory to run this algorithm.
        As it is an upload algorithm and we do not have information about data, we can not approximate this.
        """
        return -1

    def get_required_disk_size(self, view_model):
        """
        As it is an upload algorithm and we do not have information about data, we can not approximate this.
        """
        return 0

    @staticmethod
    def read_list_data(full_path, dimensions=None, dtype=numpy.float64, skiprows=0, usecols=None):
        """
        Read numpy.array from a text file or a npy/npz file.
        """
        try:
            if full_path.endswith(".npy") or full_path.endswith(".npz"):
                array_result = numpy.load(full_path)
            else:
                array_result = numpy.loadtxt(full_path, dtype=dtype, skiprows=skiprows, usecols=usecols)
            if dimensions:
                return array_result.reshape(dimensions)
            return array_result
        except ValueError as exc:
            file_ending = os.path.split(full_path)[1]
            exc.args = (exc.args[0] + " In file: " + file_ending,)
            raise

    @staticmethod
    def read_matlab_data(path, matlab_data_name=None):
        """
        Read array from matlab file.
        """
        try:
            matlab_data = scipy_io.matlab.loadmat(path)
        except NotImplementedError:
            ABCUploader.LOGGER.error("Could not read Matlab content from: " + path)
            ABCUploader.LOGGER.error("Matlab files must be saved in a format <= -V7...")
            raise

        try:
            return matlab_data[matlab_data_name]
        except KeyError:
            def double__(n):
                n = str(n)
                return n.startswith('__') and n.endswith('__')

            available = [s for s in matlab_data if not double__(s)]
            raise KeyError("Could not find dataset named %s. Available datasets: %s" % (matlab_data_name, available))

    @staticmethod
    def get_upload_information():
        return NotImplementedError
