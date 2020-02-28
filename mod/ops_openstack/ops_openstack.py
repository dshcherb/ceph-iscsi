from ops.charm import CharmBase
from ops.framework import (
    StoredState,
)

from charmhelpers.fetch import (
    apt_install,
    apt_update,
)
from ops.model import (
    ActiveStatus,
    MaintenanceStatus,
    WaitingStatus,
)
import charmhelpers.contrib.openstack.utils as os_utils
import logging
logger = logging.getLogger()

class OSBaseCharm(CharmBase):
    state = StoredState()

    PACKAGES = []

    RESTART_MAP = {}

    def __init__(self, framework, key):
        super().__init__(framework, key)
        self.state.set_default(is_started=False)
        self.state.set_default(is_paused=False)
        self.framework.observe(self.on.install, self)
        self.framework.observe(self.on.update_status, self)
        self.framework.observe(self.on.pause_action, self)
        self.framework.observe(self.on.resume_action, self)

    def on_install(self, event):
        logging.info("Installing packages")
        apt_update(fatal=True)
        apt_install(self.PACKAGES, fatal=True)

    def update_status(self):
        logging.info("Updating status")
        if self.state.is_paused:
            self.model.unit.status = MaintenanceStatus(
                "Paused. Use 'resume' action to resume normal service.")
        if self.state.is_started:
            self.model.unit.status = ActiveStatus('Unit is ready')
        else:
            self.model.unit.status = WaitingStatus('Not ready for reasons')
        logging.info("Status updated")

    def on_update_status(self, event):
        self.update_status()

    def services(self):
        _svcs = []
        for svc in self.RESTART_MAP.values():
            _svcs.extend(svc)
        return list(set(_svcs))

    def on_pause_action(self, event):
        _, messages = os_utils.manage_payload_services(
            'pause',
            services=self.services(),
            charm_func=None)
        self.state.is_paused = True
        self.update_status()

    def on_resume_action(self, event):
        _, messages = os_utils.manage_payload_services(
            'resume',
            services=self.services(),
            charm_func=None)
        self.state.is_paused = False
        self.update_status()
