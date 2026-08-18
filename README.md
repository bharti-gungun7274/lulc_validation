\# Delhi LULC Validation



\## Overview



This project develops a Python-based validation framework for Delhi Land Use/Land Cover (LULC) classification for multiple years.



The current study years are:



\- 2018

\- 2020

\- 2022

\- 2024



The validated LULC datasets will be used for temporal urbanization analysis and subsequent Markov-chain-based land-use transition analysis.



\---



\## Objectives



The main objectives are:



1\. Validate LULC classification results for multiple years.

2\. Assign independent reference classes to validation points.

3\. Compare reference classes with classified raster classes.

4\. Generate confusion matrices.

5\. Calculate quantitative accuracy measures.

6\. Produce validated LULC datasets for further temporal and Markov analysis.



\---



\## Data



The project uses:



\- Dynamic World-derived LULC raster data.

\- Sentinel-2 reference RGB imagery.

\- Validation point CSV files.

\- Delhi study-area boundary and spatial information.



The large raster files are stored separately on Google Drive because some TIFF files exceed GitHub's 100 MB individual file-size limit.



\### Large Raster Data



\*\*Google Drive:\*\*



https://drive.google.com/drive/folders/1LhiA8BOgYGM9CcFkec9aMeHIImnUSqY5?usp=drive\_link



The Google Drive folder contains the large raster datasets for:



\- 2018

\- 2020

\- 2022

\- 2024



The validation CSV files are maintained in this GitHub repository.



\---



\## Study Years



| Year | LULC | Validation Points | Sentinel-2 Reference |

|------|------|-------------------|----------------------|

| 2018 | Available | Available | Available |

| 2020 | Available | Available | Available |

| 2022 | Available | Available | Available |

| 2024 | Available | Available | Available |



\---



\## Validation Workflow



The planned validation workflow is:



```text

LULC Raster

&#x20;    |

&#x20;    v

Validation Points

&#x20;    |

&#x20;    v

Reference Image

&#x20;    |

&#x20;    v

Assign Reference Class

&#x20;    |

&#x20;    v

Compare Reference vs Classified Class

&#x20;    |

&#x20;    v

Confusion Matrix

&#x20;    |

&#x20;    +-------------------+

&#x20;    |                   |

&#x20;    v                   v

Overall Accuracy     Kappa

&#x20;    |

&#x20;    +-------------------+

&#x20;    |

&#x20;    v

Producer Accuracy

&#x20;    |

&#x20;    v

User Accuracy

&#x20;    |

&#x20;    v

Validated LULC Dataset

