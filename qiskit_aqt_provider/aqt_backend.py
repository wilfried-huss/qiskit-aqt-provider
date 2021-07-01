# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import List
import warnings

import requests

from qiskit import qobj as qobj_mod
from qiskit.providers import BackendV1 as Backend
from qiskit.providers import Options
from qiskit.providers.models import BackendConfiguration, BackendProperties
from qiskit.exceptions import QiskitError
from qiskit.util import deprecate_arguments

from . import aqt_job
from . import qobj_to_aqt
from . import circuit_to_aqt

MICROSECONDS = "µs"

class AQTSimulator(Backend):

    def __init__(self, provider):
        self.url = "https://gateway.aqt.eu/marmot/sim/"
        configuration = {
            'backend_name': 'aqt_qasm_simulator',
            'backend_version': '0.0.1',
            'url': self.url,
            'simulator': True,
            'local': False,
            'coupling_map': None,
            'description': 'AQT trapped-ion device simulator',
            'basis_gates': ['rx', 'ry', 'rxx'],
            'memory': False,
            'n_qubits': 11,
            'conditional': False,
            'max_shots': 200,
            'max_experiments': 1,
            'open_pulse': False,
            'gates': [
                {
                    'name': 'TODO',
                    'parameters': [],
                    'qasm_def': 'TODO'
                }
            ]
        }
        super().__init__(
            configuration=BackendConfiguration.from_dict(configuration),
            provider=provider)

    @classmethod
    def _default_options(cls):
        return Options(shots=100)

    @deprecate_arguments({'qobj': 'circuit'})
    def run(self, circuit, **kwargs):
        if isinstance(circuit, qobj_mod.QasmQobj):
            warnings.warn("Passing in a QASMQobj object to run() is "
                          "deprecated and will be removed in a future "
                          "release", DeprecationWarning)
            if circuit.config.shots > self.configuration().max_shots:
                raise ValueError('Number of shots is larger than maximum '
                                 'number of shots')
            aqt_json = qobj_to_aqt.qobj_to_aqt(
                circuit, self._provider.access_token)[0]
        elif isinstance(circuit, qobj_mod.PulseQobj):
            raise QiskitError("Pulse jobs are not accepted")
        else:
            for kwarg in kwargs:
                if kwarg != 'shots':
                    warnings.warn(
                        "Option %s is not used by this backend" % kwarg,
                        UserWarning, stacklevel=2)
            out_shots = kwargs.get('shots', self.options.shots)
            if out_shots > self.configuration().max_shots:
                raise ValueError('Number of shots is larger than maximum '
                                 'number of shots')
            aqt_json = circuit_to_aqt.circuit_to_aqt(
                circuit, self._provider.access_token, shots=out_shots)[0]
        header = {
            "Ocp-Apim-Subscription-Key": self._provider.access_token,
            "SDK": "qiskit"
        }
        res = requests.put(self.url, data=aqt_json, headers=header)
        res.raise_for_status()
        response = res.json()
        if 'id' not in response:
            raise Exception
        job = aqt_job.AQTJob(self, response['id'], qobj=circuit)
        return job


def fully_connected_coupling_map(n_ions: int) -> List[List[int]]:
    coupling_map = []
    for i in range(n_ions):
        for j in range(i+1, n_ions):
            coupling_map.append([i, j])
    return coupling_map


class AQTSimulatorNoise1(Backend):
    _N_QUBITS: int = 11
    _DATE: str = "2000-01-01 00:00:00Z"
    url: str = "https://gateway.aqt.eu/marmot/sim/noise-model-1"

    def __init__(self, provider):
        configuration = {
            'backend_name': 'aqt_qasm_simulator_noise_1',
            'backend_version': '0.0.1',
            'url': self.url,
            'simulator': True,
            'local': False,
            'coupling_map': fully_connected_coupling_map(self._N_QUBITS),
            'description': 'AQT trapped-ion device simulator '
                           'with noise model 1',
            'basis_gates': ['rx', 'ry', 'rxx'],
            'memory': False,
            'n_qubits': self._N_QUBITS,
            'conditional': False,
            'max_shots': 200,
            'max_experiments': 1,
            'open_pulse': False,
            'gates': [
                {
                    'name': 'TODO',
                    'parameters': [],
                    'qasm_def': 'TODO'
                }
            ]
        }
        super().__init__(
            configuration=BackendConfiguration.from_dict(configuration),
            provider=provider)

    def properties(self):
        """Return backend properties"""
        coupling_map: List[List[int]] = self.configuration().coupling_map
        unique_qubits: List[int] = list(set().union(*coupling_map))

        # TODO: provide correct values
        properties = {
            "backend_name": self.name(),
            "backend_version": self.configuration().backend_version,
            "last_update_date": self._DATE,
            "qubits": [
                [
                    {"date": self._DATE, "name": "T1", "unit": MICROSECONDS, "value": 0.0},
                    {"date": self._DATE, "name": "T2", "unit": MICROSECONDS, "value": 0.0},
                    {
                        "date": self._DATE,
                        "name": "frequency",
                        "unit": "GHz",
                        "value": 0.0,
                    },
                    {
                        "date": self._DATE,
                        "name": "readout_error",
                        "unit": "",
                        "value": 0.0,
                    },
                    {"date": self._DATE, "name": "operational", "unit": "", "value": 1},
                ]
                for _ in range(len(unique_qubits))
            ],
            "gates": [
                {
                    "gate": "cx",
                    "name": "CX" + str(pair[0]) + "_" + str(pair[1]),
                    "parameters": [
                        {
                            "date": self._DATE,
                            "name": "gate_error",
                            "unit": "",
                            "value": 0.0,
                        }
                    ],
                    "qubits": [pair[0], pair[1]],
                }
                for pair in coupling_map
            ],
            "general": [],
        }

        return BackendProperties.from_dict(properties)

    @classmethod
    def _default_options(cls):
        return Options(shots=100)

    @deprecate_arguments({'qobj': 'circuit'})
    def run(self, circuit, **kwargs):
        if isinstance(circuit, qobj_mod.QasmQobj):
            warnings.warn("Passing in a QASMQobj object to run() is "
                          "deprecated and will be removed in a future "
                          "release", DeprecationWarning)
            if circuit.config.shots > self.configuration().max_shots:
                raise ValueError('Number of shots is larger than maximum '
                                 'number of shots')
            aqt_json = qobj_to_aqt.qobj_to_aqt(
                circuit, self._provider.access_token)[0]
        elif isinstance(circuit, qobj_mod.PulseQobj):
            raise QiskitError("Pulse jobs are not accepted")
        else:
            for kwarg in kwargs:
                if kwarg != 'shots':
                    warnings.warn(
                        "Option %s is not used by this backend" % kwarg,
                        UserWarning, stacklevel=2)
            out_shots = kwargs.get('shots', self.options.shots)
            if out_shots > self.configuration().max_shots:
                raise ValueError('Number of shots is larger than maximum '
                                 'number of shots')
            aqt_json = circuit_to_aqt.circuit_to_aqt(
                circuit, self._provider.access_token, shots=out_shots)[0]
        header = {
            "Ocp-Apim-Subscription-Key": self._provider.access_token,
            "SDK": "qiskit"
        }
        res = requests.put(self.url, data=aqt_json, headers=header)
        res.raise_for_status()
        response = res.json()
        if 'id' not in response:
            raise Exception
        job = aqt_job.AQTJob(self, response['id'], qobj=circuit)
        return job


class AQTDevice(Backend):

    def __init__(self, provider):
        self.url = 'https://gateway.aqt.eu/marmot/lint'
        configuration = {
            'backend_name': 'aqt_innsbruck',
            'backend_version': '0.0.1',
            'url': self.url,
            'simulator': False,
            'local': False,
            'coupling_map': None,
            'description': 'AQT trapped-ion device',
            'basis_gates': ['rx', 'ry', 'rxx', 'ms'],
            'memory': False,
            'n_qubits': 4,
            'conditional': False,
            'max_shots': 200,
            'max_experiments': 1,
            'open_pulse': False,
            'gates': [
                {
                    'name': 'TODO',
                    'parameters': [],
                    'qasm_def': 'TODO'
                }
            ]
        }
        super().__init__(
            configuration=BackendConfiguration.from_dict(configuration),
            provider=provider)

    @classmethod
    def _default_options(cls):
        return Options(shots=100)

    @deprecate_arguments({'qobj': 'circuit'})
    def run(self, circuit, **kwargs):
        if isinstance(circuit, qobj_mod.QasmQobj):
            warnings.warn("Passing in a QASMQobj object to run() is "
                          "deprecated and will be removed in a future "
                          "release", DeprecationWarning)
            if circuit.config.shots > self.configuration().max_shots:
                raise ValueError('Number of shots is larger than maximum '
                                 'number of shots')
            aqt_json = qobj_to_aqt.qobj_to_aqt(
                circuit, self._provider.access_token)[0]
        elif isinstance(circuit, qobj_mod.PulseQobj):
            raise QiskitError("Pulse jobs are not accepted")
        else:
            for kwarg in kwargs:
                if kwarg != 'shots':
                    warnings.warn(
                        "Option %s is not used by this backend" % kwarg,
                        UserWarning, stacklevel=2)
            out_shots = kwargs.get('shots', self.options.shots)
            if out_shots > self.configuration().max_shots:
                raise ValueError('Number of shots is larger than maximum '
                                 'number of shots')
            aqt_json = circuit_to_aqt.circuit_to_aqt(
                circuit, self._provider.access_token, shots=out_shots)[0]
        header = {
            "Ocp-Apim-Subscription-Key": self._provider.access_token,
            "SDK": "qiskit"
        }
        res = requests.put(self.url, data=aqt_json, headers=header)
        res.raise_for_status()
        response = res.json()
        if 'id' not in response:
            raise Exception
        job = aqt_job.AQTJob(self, response['id'], qobj=circuit)
        return job


class AQTDeviceIbex(Backend):

    def __init__(self, provider):
        self.url = 'https://gateway.aqt.eu/marmot/Ibex'
        configuration = {
            'backend_name': 'aqt_ibex',
            'backend_version': '0.0.1',
            'url': self.url,
            'simulator': False,
            'local': False,
            'coupling_map': None,
            'description': 'AQT trapped-ion device',
            'basis_gates': ['rx', 'ry', 'rxx', 'ms'],
            'memory': False,
            'n_qubits': 10,
            'conditional': False,
            'max_shots': 200,
            'max_experiments': 1,
            'open_pulse': False,
            'gates': [
                {
                    'name': 'TODO',
                    'parameters': [],
                    'qasm_def': 'TODO'
                }
            ]
        }
        super().__init__(
            configuration=BackendConfiguration.from_dict(configuration),
            provider=provider)

    @classmethod
    def _default_options(cls):
        return Options(shots=100)

    def run(self, qobj, **kwargs):
        if isinstance(qobj, qobj_mod.QasmQobj):
            warnings.warn("Passing in a QASMQobj object to run() is "
                          "deprecated and will be removed in a future "
                          "release", DeprecationWarning)
            if qobj.config.shots > self.configuration().max_shots:
                raise ValueError('Number of shots is larger than maximum '
                                 'number of shots')
            aqt_json = qobj_to_aqt.qobj_to_aqt(
                qobj, self._provider.access_token)[0]
        elif isinstance(qobj, qobj_mod.PulseQobj):
            raise QiskitError("Pulse jobs are not accepted")
        else:
            for kwarg in kwargs:
                if kwarg != 'shots':
                    warnings.warn(
                        "Option %s is not used by this backend" % kwarg,
                        UserWarning, stacklevel=2)
            out_shots = kwargs.get('shots', self.options.shots)
            aqt_json = circuit_to_aqt.circuit_to_aqt(
                qobj, self._provider.access_token, shots=out_shots)[0]
        header = {
            "Ocp-Apim-Subscription-Key": self._provider.access_token,
            "SDK": "qiskit"
        }
        res = requests.put(self.url, data=aqt_json, headers=header)
        res.raise_for_status()
        response = res.json()
        if 'id' not in response:
            raise Exception
        job = aqt_job.AQTJob(self, response['id'], qobj=qobj)
        return job
