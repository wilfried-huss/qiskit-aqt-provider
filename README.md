# Qiskit AQT Provider

[![License](https://img.shields.io/github/license/Qiskit-Partners/qiskit-aqt-provider.svg?style=popout-square)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://img.shields.io/github/workflow/status/Qiskit-Partners/qiskit-aqt-provider/Tests/master?style=popout-square)](https://github.com/Qiskit-Partners/qiskit-aqt-provider/actions/workflows/main.yml)
[![](https://img.shields.io/github/release/Qiskit-Partners/qiskit-aqt-provider.svg?style=popout-square)](https://github.com/Qiskit-Partners/qiskit-aqt-provider/releases)

**Qiskit** is an open-source SDK for working with quantum computers at the level of circuits, algorithms, and application modules.


This project contains a provider that allows access to the **[AQT ion-trap quantum](https://www.aqt.eu)**
systems and simulators.

## Installation

You can install the provider using pip tool:

```bash
pip install qiskit-aqt-provider
```

`pip` will handle installing all the python dependencies automatically and you
will always install the  latest (and well-tested) version.

## Setting up the AQT Provider

Once the package is installed, you can use it to access the provider from qiskit.

### Configure your AQT credentials

1. Create an AQT accout or log into your existing account by visiting the
   [AQT Portal login page](https://gateway-portal.aqt.eu/).
2. Copy the your access token from your [AQT Portal account page](https://gateway-portal.aqt.eu/).
3. Paste your token from step 2, here called `MY_ACCESS_TOKEN`, into a python session and run:

    ```python
    from qiskit_aqt_provider import AQTProvider
    aqt = AQTProvider('MY_ACCESS_TOKEN')
    ```

Then you can access the the list of available AQT backends:

```python
print(aqt.backends())
```

### Submitting a circuit

Select one of the available backends. For example the AQT simulator:

```python
backend = aqt.backends.aqt_qasm_simulator
```


The selected backend can then be used like any other qiskit backend. For
example, to construct a bell state:

```python
from qiskit import QuantumCircuit, transpile

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0,1], [0,1])

trans_qc = transpile(qc, backend)
job = backend.run(trans_qc)
print(job.get_counts())
```

## Access to the ion trap quantum computer

For running the quantum circuit on the [ion-trap quantum devices](https://www.aqt.eu/qc-systems/)
you need to use `aqt_innsbruck` as backend, which is currently only available for partners of AQT.
To inquire about access to the quantum devices, please [contact AQT](https://www.aqt.eu/contact/)
directly.

## License

[Apache License 2.0].

[AQT]: https://www.aqt.eu/
[Apache License 2.0]: https://github.com/qiskit-community/qiskit-aqt-provider/blob/master/LICENSE.txt
