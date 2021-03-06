#
# The NFS source module.
#
# Copyright (C) 2020 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
from pyanaconda.core.i18n import _
from pyanaconda.core.payload import create_nfs_url, parse_nfs_url
from pyanaconda.core.signal import Signal
from pyanaconda.modules.common.structures.payload import RepoConfigurationData
from pyanaconda.modules.payloads.constants import SourceType, SourceState
from pyanaconda.modules.payloads.source.nfs.nfs_interface import NFSSourceInterface
from pyanaconda.modules.payloads.source.nfs.initialization import SetUpNFSSourceTask
from pyanaconda.modules.payloads.source.mount_tasks import TearDownMountTask
from pyanaconda.modules.payloads.source.source_base import PayloadSourceBase, \
    MountingSourceMixin, RPMSourceMixin

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)

__all__ = ["NFSSourceModule"]


class NFSSourceModule(PayloadSourceBase, MountingSourceMixin, RPMSourceMixin):
    """The NFS source module."""

    def __init__(self):
        super().__init__()
        self._url = ""
        self.url_changed = Signal()

    def __repr__(self):
        return "Source(type='NFS', url='{}')".format(self.url)

    def for_publication(self):
        """Return a DBus representation."""
        return NFSSourceInterface(self)

    @property
    def type(self):
        """Get type of this source."""
        return SourceType.NFS

    @property
    def description(self):
        """Get description of this source."""
        return _("NFS server {}").format(self.url)

    @property
    def network_required(self):
        """Does the source require a network?

        :return: True or False
        """
        return True

    def get_state(self):
        """Get state of this source."""
        return SourceState.from_bool(self.get_mount_state())

    def process_kickstart(self, data):
        """Process the kickstart data."""
        nfs_url = create_nfs_url(data.nfs.server, data.nfs.dir, data.nfs.opts)
        self.set_url(nfs_url)

    def setup_kickstart(self, data):
        """Setup the kickstart data."""
        (opts, host, path) = parse_nfs_url(self.url)

        data.nfs.server = host
        data.nfs.dir = path
        data.nfs.opts = opts
        data.nfs.seen = True

    def generate_repo_configuration(self):
        """Generate RepoConfigurationData structure."""
        return RepoConfigurationData.from_directory(self.mount_point)

    @property
    def url(self):
        """URL for mounting.

        Combines server address, path, and options.

        :rtype: str
        """
        return self._url

    def set_url(self, url):
        """Set all NFS values with a valid URL.

        Fires all signals.

        :param url: URL
        :type url: str
        """
        self._url = url
        self.url_changed.emit()
        log.debug("NFS URL is set to %s", self._url)

    def set_up_with_tasks(self):
        """Set up the installation source for installation.

        :return: list of tasks required for the source setup
        :rtype: [Task]
        """
        return [SetUpNFSSourceTask(self.mount_point, self._url)]

    def tear_down_with_tasks(self):
        """Tear down the installation source.

        :return: list of tasks required for the source clean-up
        :rtype: [TearDownMountTask]
        """
        task = TearDownMountTask(self._mount_point)
        return [task]
