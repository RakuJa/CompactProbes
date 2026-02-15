<br />
<div align="center">
  <a href="https://github.com/GiovanniBaccichet/COMPACT">
    <img src="images/compact_logo.png" alt="Logo" width="400">
  </a>

<h3 align="center">COMPACT</h3>

  <p align="center">
    Compressed features and representations for network traffic analysis in centralized and edge internet architectures.
    <br />
    <a href="https://compact-prin.github.io/"><strong>Website »</strong></a>
    <br />
    <br />
    <a href="https://antlab.deib.polimi.it/">ANT Lab - PoliMI</a>
    ·
    <a href="https://github.com/GiovanniBaccichet/COMPACT/issues">Report Bug</a>
    ·
    <a href="https://github.com/GiovanniBaccichet/COMPACT/issues">Request Feature</a>
  </p>
</div>

</details>



<!-- ABOUT THE PROJECT -->
## About The Project

Reducing complexity and costs of network traffic analysis Network traffic analysis is a critical tool used by network operators for monitoring, managing, and ensuring the security of networks at different scales. Traditional network traffic analysis involves capturing network data and can demand extensive storage and computational resources, resulting in high management and operational costs. The COMPACT project aims to revolutionize traffic analysis by reducing resource complexity and costs associated with it.

- **Shift to Feature-Based Analysis**: COMPACT promotes a shift from conventional packet-based traffic representation to a feature-based approach. Statistical features are extracted from captured data and employed in machine learning algorithms.

- **Native Feature-Based Systems**: COMPACT explores the creation of native feature-based traffic analysis systems that sidestep the traditional packet-based representation. This shift reduces storage costs while maintaining analysis accuracy.

- **Lossy Compression Techniques**: A key innovation pursued by COMPACT is the development of lossy compression techniques tailored to network traffic features. These techniques significantly cut storage costs without sacrificing analysis accuracy.

- **Rate-Accuracy Tradeoff Exploration**: The project includes the development of models to analyze the trade-off between compression rates and analysis accuracy. This helps identify critical traffic features for specific analysis tasks.

The methodologies developed in the COMPACT project will be tested in various network scenarios. These scenarios encompass central traffic analysis in backbone networks, examination of IoT traffic in home networks, and various traffic analysis tasks across different network elements and traffic rates.


# How to replicate the results
Steps marked as (opt) are optional: the result is either inconsequential or the output can already be found in the data folder. If we are looking to run everything from scratch then it's highly suggested to run those steps

0. Be in the project's root


1. Create a venv (i'm using [uv](https://docs.astral.sh/uv/) as project manager).
It MUST be python 3.11, libraries are not updated to new python versions.
```bash
uv venv --python 3.11
```
2. Source it
```bash
source .venv/bin/activate
```
3. Install requirements (jupyter lab included)
```bash
uv pip install -r requirements
```
4. (opt) Prepare data by running the various pre-processing notebooks in order (data_pre-processing, data_split)
```bash
jupyter lab notebooks/data_pre-processing/no_randomization_fix.ipynb
```
5. (opt) Run bamboo with various values (e.g. 16/32/64)
```bash
uv run bamboo_fast.py -M 64 -F 64
```
6. (opt) Extract values using the custom made (not official) script
```bash
uv run scripts/extract_from_log.py --log-file scripts/BAMBOO/BEST_CONFIG_FABIO\(8bit-filters\).log --extract-only
```
7. (opt) Update values found in the pf_training_x_bit.ipynb with the result of the previous script (Check for data_fabio or data arrays)
8. Run all the various testing notebook
```bash
jupyter lab notebooks/method_probabilistic_fingerprint/pf_testing_64bit.ipynb
```